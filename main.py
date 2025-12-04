from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import BoardState, CageSchema
from solver import KenKenSolver
from generator import generate_puzzle
import logging

# Configurar logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- CONFIGURACIÓN DE CORS (CRUCIAL PARA ANGULAR) ---
origins = [
    "http://localhost:4200", # Tu Angular
    "http://127.0.0.1:4200",
    "https://kenken-frontend-tf.netlify.app",
    "https://www.kenken-frontend-tf.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Permitir estos dominios
    allow_credentials=True,
    allow_methods=["*"],   # Permitir GET, POST, OPTIONS, etc.
    allow_headers=["*"],   # Permitir cualquier header
)

@app.get("/")
def home():
    return {"message": "API KenKen v1.0 - CORS habilitado 🚀"}

@app.post("/solve")
def solve_puzzle(board: BoardState):
    logger.info(f"Resolviendo puzzle tamaño {board.size}")
    
    # 1. Adaptar datos de Pydantic a lo que espera solver.py
    # Solver espera objetos con atributo .cells = [[r,c], [r,c]]
    # BoardState trae .cells = [{r:0, c:0}, ...]
    
    class RuleAdapter:
        def __init__(self, cage: CageSchema):
            self.operation = cage.op
            self.result = cage.target
            self.cells = [[cell.r, cell.c] for cell in cage.cells]

    adapted_rules = [RuleAdapter(cage) for cage in board.cages]

    # 2. Llamar al solver
    solver = KenKenSolver(board.size, adapted_rules)
    solution = solver.solve()

    if not solution:
        # No lanzar error 400, mejor devolver null para que el frontend sepa
        return {"solution": None}

    return {"solution": solution}

@app.get("/random/{size}")
def get_random_puzzle(size: int):
    """Genera un puzzle aleatorio del tamaño solicitado."""
    if size < 2 or size > 9:
        raise HTTPException(status_code=400, detail="Tamaño debe ser entre 2 y 9")
    
    cages = generate_puzzle(size)
    return cages

@app.post("/validate")
def validate_board(board: BoardState):
    """
    Valida conflictos lógicos en el servidor.
    Retorna lista de celdas conflictivas ["0,1", "2,3"].
    """
    conflicts = set()
    
    # 1. Validar unicidad (Filas y Columnas) - Solo si hay valores
    size = board.size
    grid = board.values
    
    # Filas
    for r in range(size):
        seen = {}
        for c in range(size):
            val = grid[r][c]
            if val != 0:
                if val in seen:
                    conflicts.add(f"{r},{c}")
                    conflicts.add(f"{r},{seen[val]}")
                seen[val] = c
                
    # Columnas
    for c in range(size):
        seen = {}
        for r in range(size):
            val = grid[r][c]
            if val != 0:
                if val in seen:
                    conflicts.add(f"{r},{c}")
                    conflicts.add(f"{seen[val]},{c}")
                seen[val] = r

    # 2. (Opcional) Validar aritmética de Jaulas
    # Por ahora confiaremos en la validación del frontend para la aritmética,
    # ya que es más rápido, pero aquí podrías agregar la lógica espejo.
    
    return {"valid": len(conflicts) == 0, "conflicts": list(conflicts)}