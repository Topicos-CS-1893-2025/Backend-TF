import random
from ortools.sat.python import cp_model
from uuid import uuid4

def generate_latin_square(size: int):
    """Genera un tablero NxN válido (filas y columnas únicas)."""
    model = cp_model.CpModel()
    grid = []
    for i in range(size):
        row = []
        for j in range(size):
            row.append(model.NewIntVar(1, size, f'cell_{i}_{j}'))
        grid.append(row)

    # Restricciones de unicidad
    for row in grid:
        model.AddAllDifferent(row)
    for j in range(size):
        col = [grid[i][j] for i in range(size)]
        model.AddAllDifferent(col)

    solver = cp_model.CpSolver()
    solver.parameters.random_seed = random.randint(0, 100000)
    
    status = solver.Solve(model)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return [[solver.Value(grid[i][j]) for j in range(size)] for i in range(size)]
    return None

def apply_operation(values, op):
    """Calcula el target basado en los valores y la operación."""
    if not values: return 0
    
    if op == '+': return sum(values)
    if op == '*': 
        res = 1
        for v in values: res *= v
        return res
    if op == 'range': return max(values) - min(values)
    if op == 'sum_sq': return sum(v*v for v in values)
    
    # Para resta, div, mod, pot asumimos 2 valores
    if len(values) == 2:
        a, b = sorted(values, reverse=True) 
        if op == '-': return a - b
        if op == '/': return a // b if b != 0 and a % b == 0 else 0 
        if op == 'mod': return a % b if b != 0 else 0
        if op == '^': return int(a ** b) if b < 10 else 0 
    
    return sum(values)

def generate_puzzle(size: int):
    # 1. Generar solución base
    solution = generate_latin_square(size)
    if not solution: return []

    # 2. Crear celdas no visitadas
    unvisited = set((r, c) for r in range(size) for c in range(size))
    cages = []

    # Pool de operaciones
    ops_pool = ['+', '*', '-', '/', 'mod', 'range']
    if size > 4: ops_pool.append('sum_sq')

    # --- FASE 1: GENERACIÓN BASE (Soporte Disjoint) ---
    while unvisited:
        start = random.choice(list(unvisited))
        current_cage_cells = [start]
        unvisited.remove(start)
        
        target_size = random.randint(1, 4)
        
        for _ in range(target_size - 1):
            # 30% probabilidad de salto (Disjoint)
            if random.random() < 0.3 and unvisited:
                 next_cell = random.choice(list(unvisited))
                 current_cage_cells.append(next_cell)
                 unvisited.remove(next_cell)
            else:
                neighbors = []
                for r, c in current_cage_cells:
                    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nr, nc = r + dr, c + dc
                        if (nr, nc) in unvisited:
                            neighbors.append((nr, nc))
                
                if not neighbors: 
                    if unvisited: # Salto forzado si se encierra
                         next_cell = random.choice(list(unvisited))
                         current_cage_cells.append(next_cell)
                         unvisited.remove(next_cell)
                    else:
                        break
                else:
                    next_cell = random.choice(neighbors)
                    current_cage_cells.append(next_cell)
                    unvisited.remove(next_cell)

        # Asignar operación
        cell_values = [solution[r][c] for r, c in current_cage_cells]
        op = '+'
        
        if len(cell_values) == 1:
            op = '='
        elif len(cell_values) == 2:
             # Intentar asignar una operación interesante que sea válida
             possible_ops = ['+', '*', 'range', '-']
             
             # Solo permitir división si es exacta
             a, b = sorted(cell_values, reverse=True)
             if b != 0 and a % b == 0: possible_ops.append('/')
             if b != 0: possible_ops.append('mod')
             
             op = random.choice(possible_ops)
        else:
            op = random.choice(['+', '*', 'range', 'sum_sq'])

        target = apply_operation(cell_values, op)
        
        cages.append({
            "id": str(uuid4()),
            "cells": [{"r": r, "c": c} for r, c in current_cage_cells],
            "op": op,
            "target": target
        })

    # --- FASE 2: REGLAS EXTRA (Corrección de Lógica) ---
    num_extra_rules = max(1, size // 2)
    
    for _ in range(num_extra_rules):
        r1, c1 = random.randint(0, size-1), random.randint(0, size-1)
        r2, c2 = random.randint(0, size-1), random.randint(0, size-1)
        
        cells = [(r1,c1)]
        if (r1,c1) != (r2,c2): cells.append((r2,c2))
        
        vals = [solution[r][c] for r, c in cells]
        
        # Selección inteligente de operación extra
        op_extra = '+'
        if len(vals) == 2:
            a, b = sorted(vals, reverse=True)
            choices = ['+', '*', 'range', '-']
            # SOLO permitir división/mod si tiene sentido matemático
            if b != 0 and a % b == 0: choices.append('/')
            if b != 0: choices.append('mod')
            op_extra = random.choice(choices)
        
        target_extra = apply_operation(vals, op_extra)
        
        cages.append({
            "id": str(uuid4()), 
            "cells": [{"r": r, "c": c} for r, c in cells],
            "op": op_extra,
            "target": target_extra
        })

    return cages