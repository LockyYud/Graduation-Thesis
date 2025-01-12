from openai import OpenAI
from pipeline.DatabaseInteractor import Neo4jInteractor
from pipeline.LLMsInteractor import LLMsInteractor
from pipeline.pipeline import Pipeline
from dotenv import load_dotenv
import os

load_dotenv()

uri_neo4j = "bolt://localhost:7687"
user_neo4j = "neo4j"
password_neo4j = "password"
db_interactor = Neo4jInteractor(uri=uri_neo4j, user=user_neo4j, password=password_neo4j)

client_llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model_llm = "gpt-4o-mini"
llms_interactor = LLMsInteractor(
    client_llm,
    model_llm,
)

pipeline = Pipeline(
    db_interactor=db_interactor,
    llms_interactor=llms_interactor,
    depth_loop=3,
    beam_depth=5,
    reasoning_depth=5,
    chunks_depth=5,
    vector_index="chunks_vector",
)


def main():
    pipeline.run()


if __name__ == "__main__":
    main()
