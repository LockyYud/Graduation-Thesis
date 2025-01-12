from neo4j import GraphDatabase


class Neo4jInteractor:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # def hybrid_search(self, index_name, question, k):

    def vector_search_chunks(self, index_name, question_vector, k):
        with self.driver.session() as session:
            query = (
                "CALL db.index.vector.queryNodes($index_name, $k, $question_vector) "
                "YIELD node as chunk, score "
                "RETURN chunk, score "
            )
            result = session.run(
                query,
                {"index_name": index_name, "question_vector": question_vector, "k": k},
            )
            nodes = [dict(record) for record in result]
            return nodes

    def vector_search(self, index_name, question_vector, k):
        with self.driver.session() as session:
            query = (
                "CALL db.index.vector.queryNodes($index_name, $k, $question_vector) "
                "YIELD node as chunk, score "
                "RETURN chunk, score "
            )
            result = session.run(
                query,
                {"index_name": index_name, "question_vector": question_vector, "k": k},
            )
            nodes = [dict(record["chunk"]) for record in result]
            return nodes

    def fulltext_search(self, index_name, question, k):
        with self.driver.session() as session:
            query = (
                "CALL db.index.fulltext.queryNodes($index_name, $query) "
                "YIELD node, score "
                "RETURN node, score "
                "ORDER BY score DESC "
                "LIMIT $k"
            )
            result = session.run(
                query, {"index_name": index_name, "query": question, "k": k}
            )
            nodes = [dict(record["node"]) for record in result]
            return nodes

    def fulltext_search_entities(self, index_name, ner_entities: list, k):
        entities = " OR ".join(ner_entities)
        with self.driver.session() as session:
            query = (
                "CALL db.index.fulltext.queryNodes($index_name, $entities) "
                "YIELD node, score "
                "RETURN node, score "
                "ORDER BY score DESC "
                "LIMIT $k"
            )
            result = session.run(
                query, {"index_name": index_name, "entities": entities, "k": k}
            )
            nodes = [dict(record["node"]) for record in result]
            return nodes

    def calculate_distances(self, docs_id: list, docs_id_ex: list = []):
        if len(docs_id_ex) != 0:
            query = f"""
            UNWIND [{",".join(docs_id)}] AS idA
            UNWIND [{",".join(docs_id_ex)}] AS idB
            MATCH (nodeA), (nodeB)
            WHERE nodeA.element_id = idA AND nodeB.element_id = idB
            AND idA <> idB
            MATCH p = shortestPath((nodeA)-[*]-(nodeB))
            RETURN idA AS nodeA_id, idB AS nodeB_id, length(p) AS distance
            """
        else:
            query = f"""
            UNWIND [{",".join(docs_id)}] AS idA
            UNWIND [{",".join(docs_id)}] AS idB
            MATCH (nodeA), (nodeB)
            WHERE nodeA.element_id = idA AND nodeB.element_id = idB
            AND idA < idB
            MATCH p = shortestPath((nodeA)-[*]-(nodeB))
            RETURN idA AS nodeA_id, idB AS nodeB_id, length(p) AS distance
            """
        with self.driver.session() as session:
            result = session.run(query)  # Use dictionary syntax here
            distances = []
            for record in result:
                distances.append(
                    {
                        "nodeA": record["nodeA_id"],
                        "nodeB": record["nodeB_id"],
                        "distance": record["distance"],
                    }
                )
            return distances

    def get_chunks(self, chunks_id: list):
        with self.driver.session() as session:
            query = """
            MATCH (chunk:paragraph) WHERE chunk.element_id IN $chunks_id return chunk"""
            result = session.run(query, {"chunks_id": chunks_id})
            chunks = [dict(record["chunk"]) for record in result]
            return chunks

    def get_related_nodes(self, node_id, type_relation):
        with self.driver.session() as session:
            query = """
            MATCH (node)-[r]-(related)
            WHERE node.element_id = $node_id
            AND type(r) = $type_relation
            WITH related, r, CASE
                WHEN startNode(r) = node THEN TRUE
                ELSE FALSE
            END AS direction
            RETURN {relation: {type: type(r), detail: r.detail, time: r.time, direction: direction}, node_related: {name: related.name, element_id: related.element_id, docs_id: related.docs_id}} as res LIMIT 10"""
            result = session.run(
                query, {"node_id": node_id, "type_relation": type_relation}
            )
            related_nodes = [dict(record["res"]) for record in result]
            return related_nodes

    def get_related_relations(self, node_id):
        with self.driver.session() as session:
            query = """
            MATCH (node)-[r]-(related)
            WHERE node.element_id = $node_id
            RETURN r LIMIT 10"""
            result = session.run(query, {"node_id": node_id})
            related_relations = [record["r"] for record in result]
            return related_relations
