tool_extract_topic_entities = [
    {
        "type": "function",
        "function": {
            "name": "topic_entities",
            "description": "Các thực thể đóng vai trò quan trọng trong việc trả lời câu hỏi được cung cấp.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_entities": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "Các thực thể xuất hiện trong phần câu hỏi được cung cấp.",
                        },
                    },
                },
                "required": ["topic_entities"],
            },
        },
    }
]

tool_relation_prune = [
    {
        "type": "function",
        "function": {
            "name": "relation_prune",
            "description": "Chọn ra những quan hệ liên quan nhất tới câu hỏi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relation_prune": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "description": "Các quan hệ liên quan tới câu hỏi.",
                            "properties": {
                                "id": {
                                    "type": "number",
                                    "description": "ID của relationship.",
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Tên của quan hệ đó.",
                                },
                                "score": {
                                    "type": "number",
                                    "description": "Độ tương đồng giữa thực thể, quan hệ với câu hỏi.",
                                },
                            },
                            "required": ["name", "score", "id"],
                        },
                    },
                },
                "required": ["relation_prune"],
            },
        },
    }
]

tool_path_prune = [
    {
        "type": "function",
        "function": {
            "name": "path_prune",
            "description": "Chọn ra những thực thể liên quan nhất tới câu hỏi, đóng góp quan trọng trong việc trả lời câu hỏi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path_prune": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "description": "Điểm số của bộ 3 trong việc trả lời câu hỏi.",
                            "properties": {
                                "score": {
                                    "type": "string",
                                    "description": "Điểm sô đánh giá độ liên quan, quan trọng trong việc trả lời câu hỏi. Nằm trong khoảng từ 0 đến 100",
                                },
                                "id": {
                                    "type": "number",
                                    "description": "Mã số của bộ 3.",
                                },
                                "rationale": {
                                    "type": "string",
                                    "description": "Lý do vì sao bộ 3 này quan trọng trong việc trả lời câu hỏi.",
                                },
                            },
                            "required": ["score", "id", "rationale"],
                        },
                    },
                },
                "required": ["path_prune"],
            },
        },
    }
]

tool_entity_prune = [
    {
        "type": "function",
        "function": {
            "name": "entity_prune",
            "description": "Chọn ra những thực thể, khái niệm quan trọng, đóng vai trò chính để trả lời câu hỏi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_prune": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "description": "Các thực thể liên quan tới câu hỏi.",
                            "properties": {
                                "score": {
                                    "type": "string",
                                    "description": "Điểm đánh giá mức độ quan trọng của thực thể trong việc trả lời câu hỏi từ 0 đến 10.",
                                },
                                "id": {
                                    "type": "number",
                                    "description": "Id của thực thể.",
                                },
                            },
                            "required": ["score", "id"],
                        },
                    },
                },
                "required": ["entity_prune"],
            },
        },
    }
]

tool_answer_mpc_question = [
    {
        "type": "function",
        "function": {
            "name": "answer_question",
            "description": "Trả lời câu hỏi được cung cấp",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "enum": ["A", "B", "C", "D"],
                        "description": "Câu trả lời đúng, đây là câu hỏi trắc nghiệm, chỉ chọn 1 trong 4 đáp án",
                    },
                },
                "required": ["list_answers"],
                "additionalProperties": False,
            },
        },
    }
]
