import os
from openai import OpenAI
from pipeline.DatabaseInteractor import Neo4jInteractor
from pipeline.LLMsInteractor import LLMsInteractor
from pipeline.main import Pipeline
from dotenv import load_dotenv
from huggingface_hub import login
from FlagEmbedding import FlagReranker, BGEM3FlagModel

load_dotenv()

uri_neo4j = os.getenv("NEO4J_URI")
user_neo4j = os.getenv("NEO4J_USER")
password_neo4j = os.getenv("NEO4J_PASSWORD")
hunggingface_token = os.getenv("HUGGINGFACE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
model_llm = "gpt-4o-mini"

login(token=hunggingface_token, add_to_git_credential=True)

reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)
embedding_model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)

client_llm = OpenAI(api_key=openai_api_key)
db_interactor = Neo4jInteractor(uri=uri_neo4j, user=user_neo4j, password=password_neo4j)
llms_interactor = LLMsInteractor(
    client_llm,
    model_llm,
)

pipeline = Pipeline(
    db_interactor=db_interactor,
    llms_interactor=llms_interactor,
    embedding=embedding_model,
    reranker=reranker,
    depth_loop=3,
    beam_depth=5,
    reasoning_depth=5,
    chunks_depth=5,
)


def main():
    question = ""
    answer, context = pipeline.run(
        question=question,
        vector_index="chunks_vector",
    )
    print(f"Question: {question}")
    print(f"Answer: {answer}")
    print(f"Context: {context}")


if __name__ == "__main__":
    main()
