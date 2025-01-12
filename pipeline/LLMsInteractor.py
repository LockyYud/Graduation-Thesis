import heapq
import json
import random
from pipeline.const import ReasoningPath, Relation
from pipeline.function_call import *
from pipeline.instruction_list import *


class LLMsInteractor:
    def __init__(self, llm_client, model) -> None:
        self.client = llm_client
        self.model = model

    def ner_task(self, question: str):
        extraction_entities = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": ner_prompt_instruction,
                },
                {"role": "user", "content": f"""## Câu hỏi: {question}"""},
            ],
            model=self.model,
            tools=tool_extract_topic_entities,
            tool_choice="auto",
            max_tokens=1024,  # Maximum number of tokens to allow in our response
        )
        final_res = rewrite_function_call_response(
            client=self.client,
            response=extraction_entities,
            tool=tool_extract_topic_entities,
            model=self.model,
        )
        return final_res

    def relation_prune(
        self,
        question: str,
        reasoning_path: ReasoningPath,
        list_relations: list[str],
        beam_depth: int,
    ):
        context_relation = f"""## Thực thể chính: {reasoning_path.list_nodes[-1].name}
    ## Danh sách mối quan hệ:
    # """
        for index, relation in enumerate(list_relations):
            context_relation += f"{{id: {index + 1}: {relation}}}\n"
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": relation_prune_prompt_instruct,
                },
                {
                    "role": "user",
                    "content": f"""## Câu hỏi: {question}
            {context_relation}
            """,
                },
            ],
            model=self.model,
            tools=tool_relation_prune,
            tool_choice="auto",
            max_tokens=1024,  # Maximum number of tokens to allow in our response
            temperature=0.5,
        )
        scores = rewrite_function_call_response(
            client=self.client,
            response=chat_completion,
            tool=tool_relation_prune,
            model=self.model,
        )
        sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)
        reasoning_path.list_nodes[-1].relations.extend(
            [
                Relation(name=list_relations[relation["id"] - 1], id=None, detail=None)
                for relation in sorted_scores[:beam_depth]
            ]
        )
        return reasoning_path

    def generate_final_answer(self, query: str, chunks: list[str]):
        chunks_text = "".join(
            [f"{index + 1}. {chunk}\n" for index, chunk in enumerate(chunks)]
        )
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": answer_prompt_instruct,
                },
                {
                    "role": "user",
                    "content": f"""Trả lời câu hỏi dựa trên các thông tin được cung cấp trong các đoạn văn bản.
            ## Câu hỏi: {query}
            ## Các đoạn văn bản:
            {chunks_text}
            """,
                },
            ],
            temperature=1,
            model=self.model,
        )

        return chat_completion

    def generate_final_answer_without_explain(self, query: str, chunks: list[str]):
        chunks_text = "".join(
            [f"{index + 1}. {chunk}\n" for index, chunk in enumerate(chunks)]
        )
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": answer_prompt_instruct_mcp,
                },
                {
                    "role": "user",
                    "content": f""".
            ## Câu hỏi: {query}
            ## Các đoạn văn bản:
            {chunks_text}
            """,
                },
            ],
            temperature=1,
            model=self.model,
            tool_choice="auto",
            tools=tool_answer_mpc_question,
        )

        return chat_completion

    def reasoning_path_prune(self, query: str, k: int, related_nodes: list):
        # Tạo lịch sử trò chuyện mới
        separator = ",\\n "
        conversation = [
            {
                "role": "system",
                "content": reasoning_path_prune_instruction,
            },
            {
                "role": "user",
                "content": f"""
            # Câu hỏi: {query}
            # Các bộ 3 (triples) được trích xuất từ đồ thị tri thức: 
            {separator.join(str(path) for path in related_nodes)}
            """,
            },
        ]
        # Sử dụng
        response = self.client.chat.completions.create(
            messages=conversation,
            model=self.model,
            max_tokens=1024,
            tools=tool_path_prune,
            tool_choice="auto",
            temperature=0.5,
        )
        res = rewrite_function_call_response(
            client=self.client,
            response=response,
            tool=tool_path_prune,
            model=self.model,
        )
        top_k = heapq.nlargest(k, res, key=lambda x: x["score"])
        return top_k

    def validate_entities(self, query: str, entities: list[str]):
        # Tạo lịch sử trò chuyện mới
        random.shuffle(entities)
        conversation = [
            {
                "role": "system",
                "content": validate_entities_instruction,
            },
            {
                "role": "user",
                "content": f"""
            ## Câu hỏi: {query}
            ## Các thực thể chủ đề: [{", ".join([str(item) for item in entities])}]
            """,
            },
        ]
        # Sử dụng
        response = self.client.chat.completions.create(
            messages=conversation,
            model=self.model,
            max_tokens=1024,
            tools=tool_entity_prune,
            tool_choice="auto",
            temperature=0.5,
        )
        res = rewrite_function_call_response(
            client=self.client,
            response=response,
            tool=tool_entity_prune,
            model=self.model,
        )
        return res

    def requery_clue(self, query: str, clues: str, chunks: list[str]):
        chunks_text = "".join(
            [f"{index + 1}. {chunk}\n" for index, chunk in enumerate(chunks)]
        )
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": requery_clues_instruction,
                },
                {
                    "role": "user",
                    "content": f"""
                    # Câu hỏi: 
                    {query}
                    # Manh mối:
                    {clues}
                    # Các đoạn văn bản:
                    {chunks_text}
                    """,
                },
            ],
            model=self.model,
            max_tokens=1024,
            temperature=1.0,
        )

        return chat_completion.choices[0].message.content

    def evaluate_chunks_query_change(self, query: str, clues: str, chunks: list[str]):
        chunks_text = "".join(
            [f"{index + 1}. {chunk}\n" for index, chunk in enumerate(chunks)]
        )
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": evaluate_chunks_change_query_instruction_zero_shot,
                },
                {
                    "role": "user",
                    "content": f"""Với một câu hỏi, một số manh mối đã được thu thập và các ngữ cảnh là các đoạn văn bản liên quan, bạn được yêu cầu đánh giá liệu những tài nguyên này, kết hợp với kiến thức sẵn có của bạn, có đủ để đưa ra câu trả lời ("Có" hoặc "Không").
            # Câu hỏi: 
            {query}
            # Manh mối:
            {clues if clues else 'Không có manh mối'}
            # Các đoạn văn bản:
            {chunks_text}
            """,
                },
            ],
            model=self.model,
            max_tokens=1024,
            temperature=1.0,
        )

        return chat_completion.choices[0].message.content

    def evaluate_chunks(self, query: str, clues: str, chunks: list[str]):
        chunks_text = "".join(
            [f"{index + 1}. {chunk}\n" for index, chunk in enumerate(chunks)]
        )
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": evaluate_chunks_instruction,
                },
                {
                    "role": "user",
                    "content": f"""Với một câu hỏi, một số manh mối đã được thu thập và các ngữ cảnh là các đoạn văn bản liên quan, bạn được yêu cầu đánh giá liệu những tài nguyên này, kết hợp với kiến thức sẵn có của bạn, có đủ để đưa ra câu trả lời ("Có" hoặc "Không")
                    # Câu hỏi: 
                    {query}
                    # Manh mối:
                    {clues}
                    # Các đoạn văn bản:
                    {chunks_text}
                    """,
                },
            ],
            model=self.model,
            max_tokens=4,
            temperature=1.0,
        )
        return chat_completion.choices[0].message.content


def rewrite_function_call_response(client, response, tool, model):
    while response.choices[0].message.tool_calls == None:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Sửa lại response sau theo đúng function_call được cung cấp",
                },
                {
                    "role": "user",
                    "content": f"""{response.choices[0].message.content}""",
                },
            ],
            model=model,
            max_tokens=1024,
            tools=tool,
            tool_choice="auto",
        )
    if type(response.choices[0].message.tool_calls[0].function.arguments) == str:
        return json.loads(response.choices[0].message.tool_calls[0].function.arguments)[
            tool[0]["function"]["name"]
        ]
    else:
        return (
            response.choices[0]
            .message.tool_calls[0]
            .function.arguments[tool[0]["function"]["name"]]
        )
