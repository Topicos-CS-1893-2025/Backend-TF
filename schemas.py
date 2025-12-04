from pydantic import BaseModel
from typing import List, Optional, Set

# Coordenada simple {r: 0, c: 1}
class Pos(BaseModel):
    r: int
    c: int

# La jaula como la envía Angular
class CageSchema(BaseModel):
    id: Optional[str] = None
    target: int
    op: str # "+", "-", "mod", etc.
    cells: List[Pos]

# El estado completo del tablero
class BoardState(BaseModel):
    size: int
    values: List[List[int]] # Matriz de números
    cages: List[CageSchema]
    conflicts: Optional[list] = [] # Angular manda un Set, aquí llega como lista o null