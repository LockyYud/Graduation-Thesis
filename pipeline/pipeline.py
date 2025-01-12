import copy
import heapq
import re
from typing import List
from pipeline.DatabaseInteractor import Neo4jInteractor
from pipeline.LLMsInteractor import LLMsInteractor
from pipeline.const import Entity, ReasoningPath, Relation
from pipeline.utils import cosine_similarity


class Pipeline:
    def __init__(
        self,
        db_interactor: Neo4jInteractor,
        llms_interactor: LLMsInteractor,
        depth_loop: int,
        beam_depth: int,
        reasoning_depth: int,
        chunks_depth: int,
        reranker,
        embedding,
    ):
        self.db_interactor = db_interactor
        self.llms_interactor = llms_interactor
        self.depth_loop = depth_loop
        self.beam_depth = beam_depth
        self.reasoning_depth = reasoning_depth
        self.chunks_depth = chunks_depth
        self.reranker = reranker
        self.embedding = embedding

    def ranking_chunks(
        self,
        chunks: list,
        question_vector: List[float] | list[List[float]],
        top_k: int,
        alpha: int = 40,
    ):
        score_embed_chunks = {}
        for chunk in chunks:
            score = cosine_similarity(question_vector, chunk["embedding"])
            score_embed_chunks[chunk["element_id"]] = score
        distances = self.interactor_database.calculate_distances(
            docs_id=[str(_["element_id"]) for _ in chunks], docs_id_ex=[]
        )

        chunks_score = {}
        for distance in distances:
            if distance["nodeA"] not in chunks_score:
                chunks_score[distance["nodeA"]] = score_embed_chunks[distance["nodeA"]]
            if distance["nodeB"] not in chunks_score:
                chunks_score[distance["nodeB"]] = score_embed_chunks[distance["nodeB"]]
            chunks_score[distance["nodeA"]] += (
                1
                / (distance["distance"] * distance["distance"] + alpha)
                * score_embed_chunks[distance["nodeB"]]
            )
            chunks_score[distance["nodeB"]] += (
                1
                / (distance["distance"] * distance["distance"] + alpha)
                * score_embed_chunks[distance["nodeA"]]
            )
        chunks_score = dict(
            sorted(chunks_score.items(), key=lambda item: item[1], reverse=True)
        )
        top_k_chunks = heapq.nlargest(top_k, chunks_score, key=chunks_score.get)
        print("Top k", top_k_chunks)
        return [chunk for chunk in chunks if chunk["element_id"] in top_k_chunks]

    def handle_relations(
        self,
        question: str,
        reasonings_path: list[ReasoningPath],
        beam_depth: int,
    ):
        for i in range(len(reasonings_path)):
            # relation exploration
            related_relation = self.db_interactor.get_related_relations(
                reasonings_path[i].list_nodes[-1].id
            )
            list_type_relations = list(
                set([relation.type for relation in related_relation])
            )
            # relation pruning
            reasonings_path[i] = self.llms_interactor.relation_prune(
                question, reasonings_path[i], list_type_relations, beam_depth
            )
        return reasonings_path

    def handle_entities(
        self,
        question: str,
        reasonings_path: list[ReasoningPath],
        k: int,
    ):
        # entity exploration
        related_entities = []
        str_related_entities = {}
        template_path_string = "{str_prev_path}{cur_node} -- {relation} -> {next_node}"
        for path in reasonings_path:
            # string of current path
            str_prev_path = ""
            for prev_node, current_node in zip(path.list_nodes, path.list_nodes[1:]):
                if current_node:
                    str_prev_path += f"{prev_node.name} -- {prev_node.relations[0]} -- {current_node.name}, "

            # get related entities
            related_entities.append(
                [
                    self.db_interactor.get_related_nodes(
                        node_id=path.list_nodes[-1].id, type_relation=relation.name
                    )
                    for relation in path.list_nodes[-1].relations
                ]
            )

            # string path with next triples
            for entities in related_entities[-1]:
                for entity in entities:
                    if entity["relation"]["direction"]:
                        str_related_entities[entity["node_related"]["element_id"]] = (
                            template_path_string.format(
                                str_prev_path=str_prev_path,
                                cur_node=path.list_nodes[-1].name,
                                relation=entity["relation"]["type"].replace("_", " "),
                                next_node=entity["node_related"]["name"],
                            )
                        )
                    else:
                        str_related_entities[entity["node_related"]["element_id"]] = (
                            template_path_string.format(
                                str_prev_path=str_prev_path,
                                cur_node=entity["node_related"]["name"],
                                relation=entity["relation"]["type"].replace("_", " "),
                                next_node=path.list_nodes[-1].name,
                            )
                        )
        # entity pruning
        res_entities_prune = self.llms_interactor.reasoning_path_prune(
            query=question, k=k, related_nodes=str_related_entities.items()
        )
        top_path = [int(_["id"]) for _ in res_entities_prune]
        new_reasonings_path = []
        for path, path_related_nodes in zip(reasonings_path, related_entities):
            for related_node in path_related_nodes:
                if int(related_node[0]["node_related"]["element_id"]) in top_path:
                    new_path = copy.deepcopy(path)
                    new_path.list_nodes[-1].relations = [
                        Relation(
                            name=related_node[0]["relation"]["type"],
                            id=None,
                            detail=related_node[0]["relation"]["detail"],
                        )
                    ]
                    new_path.list_nodes.append(
                        Entity(
                            id=related_node[0]["node_related"]["element_id"],
                            name=related_node[0]["node_related"]["name"],
                            relations=[],
                            docs_id=related_node[0]["node_related"]["docs_id"],
                        )
                    )
                    new_reasonings_path.append(new_path)
        return new_reasonings_path

    def handle_chunks(
        self,
        chunks_id: list,
        question: str,
        top_k: int,
        last_clues: list,
    ):
        top_k_chunks = self.ranking_chunks(
            chunks=chunks_id,
            top_k=top_k,
            last_clues=last_clues,
        )
        validation_res = self.llms_interactor.evaluate_chunks(
            question, [chunk["content"] for chunk in top_k_chunks]
        )
        if "Có" in validation_res:
            return (top_k_chunks, True)
        return (top_k_chunks, False)

    # extraction entities
    def extraction_topic_entities(self, question: str, k: int):
        ner_result = self.llms_interactor.ner_task(question)
        topic_entities = []
        for entity in ner_result:
            topic_entities.extend(
                self.db_interactor.fulltext_search("entities_fulltext", entity, 3)
            )
        # verification entities
        verified_entities = {}
        for entity in topic_entities:
            verified_entities[entity["element_id"]] = entity["name"]
        verified_res = self.llms_interactor.validate_entities(
            query=question,
            entities=[
                {"id": entity["element_id"], "name": entity["name"]}
                for entity in topic_entities
            ],
        )
        entities_id = [
            entity["id"]
            for entity in heapq.nlargest(k, verified_res, key=lambda x: int(x["score"]))
        ]
        topic_nodes = [
            Entity(
                id=node["element_id"],
                name=node["name"],
                relations=[],
                docs_id=node["docs_id"],
            )
            for node in topic_entities
            if node["element_id"] in entities_id
        ]
        return topic_nodes

    def run(
        self,
        question: str,
        vector_index: str,
    ):
        clues = "Không có manh mối nào"
        can_answer = False
        question_embedding = self.embedding(text=question)
        vector_search_results = self.interactor_database.vector_search(
            index_name=vector_index, question_vector=question_embedding, k=10
        )

        # extraction topic entities
        topic_entities = self.extraction_topic_entities(
            question=question,
            k=self.reasoning_depth,
        )

        reasoning_paths = [
            ReasoningPath(list_nodes=[entity]) for entity in topic_entities
        ]
        # extraction chunks from topic entities

        entities_guided_chunks = self.db_interactor.get_chunks(
            [doc_id for entity in topic_entities for doc_id in entity.docs_id]
        )

        entities_guided_chunks = self.db_interactor.get_chunks(
            [doc_id for entity in topic_entities for doc_id in entity.docs_id]
        )
        top_related_chunks = (
            self.ranking_chunks(
                chunks=entities_guided_chunks,
                question_vector=question_embedding,
                top_k=10,
            )
            + vector_search_results
        )

        scores_chunk = self.reranker.compute_score(
            sentence_pairs=[
                [question, chunk["content"]] for chunk in top_related_chunks
            ]
        )
        top_k_related_chunks = [
            top_related_chunks[_]
            for _ in [
                i
                for _, i in heapq.nlargest(
                    5, [(val, idx) for idx, val in enumerate(scores_chunk)]
                )
            ]
        ]

        evaluation_res = self.llms_interactor.evaluate_chunks(
            query=question,
            clues=clues,
            chunks=[chunk["content"] for chunk in top_k_related_chunks],
        )

        if "Có" in evaluation_res:
            can_answer = True
        else:
            requery_clue_res = self.llms_interactor.requery_clue(
                query=question,
                clues=clues,
                chunks=[chunk["content"] for chunk in top_k_related_chunks],
            )
            clues = re.findall(r"\{(.*?)\}", requery_clue_res)[0]
        for _ in range(self.depth_loop):
            if can_answer == True:
                break
            print("handle_relations")
            reasoning_paths = self.handle_relations(
                question=question,
                reasonings_path=reasoning_paths,
                beam_depth=self.beam_depth,
            )

            print("handle_entities")
            reasoning_paths = self.handle_entities(
                question=question,
                reasonings_path=reasoning_paths,
                k=self.reasoning_depth,
            )

            print("handle_chunks")
            entities_guided_chunks = self.db_interactor.get_chunks(
                list(
                    set(
                        [
                            doc_id
                            for path in reasoning_paths
                            for entity in path.list_nodes
                            for doc_id in entity.docs_id
                        ]
                    )
                )
            )

            top_related_chunks = (
                self.ranking_chunks(
                    chunks=entities_guided_chunks,
                    question_vector=question_embedding,
                    top_k=self.chunks_depth,
                )
                + top_k_related_chunks
            )
            scores_chunk = self.reranker.compute_score(
                sentence_pairs=[
                    [question, chunk["content"]] for chunk in top_related_chunks
                ]
            )
            top_k_related_chunks = [
                top_related_chunks[_]
                for _ in [
                    i
                    for _, i in heapq.nlargest(
                        self.chunks_depth,
                        [(val, idx) for idx, val in enumerate(scores_chunk)],
                    )
                ]
            ]

            evaluation_res = self.llms_interactor.evaluate_chunks(
                query=question,
                clues=clues,
                chunks=[chunk["content"] for chunk in top_k_related_chunks],
            )
            if "Có" in evaluation_res:
                can_answer = True
                break
            else:
                requery_clue_res = self.llms_interactor.requery_clue(
                    query=question,
                    clues=clues,
                    chunks=[chunk["content"] for chunk in top_k_related_chunks],
                )
                clues = re.findall(r"\{(.*?)\}", requery_clue_res)[0]
        context = [chunk["content"] for chunk in top_k_related_chunks]
        answer = self.llms_interactor.generate_final_answer(question, context)
        return (answer, context)
