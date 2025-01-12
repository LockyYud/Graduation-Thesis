from pydantic import BaseModel
from typing import List, Optional


# define classes for the input and output data
class Relation(BaseModel):
    id: Optional[int]
    name: str
    detail: Optional[str]


class Entity(BaseModel):
    id: int
    name: str
    relations: List[Relation]
    docs_id: List[int]


class ReasoningPath(BaseModel):
    list_nodes: List[Entity]
