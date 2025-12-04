from ortools.sat.python import cp_model

class KenKenSolver:
    def __init__(self, size: int, rules: list):
        self.size = size
        self.rules = rules
        self.model = cp_model.CpModel()
        self.grid = [] 

    def _get_vars_from_cells(self, cells):
        vars_list = []
        for r, c in cells:
            vars_list.append(self.grid[r][c])
        return vars_list

    def _create_board_variables(self):
        # 1. Crear variables
        for i in range(self.size):
            row = []
            for j in range(self.size):
                row.append(self.model.NewIntVar(1, self.size, f"Tile[{i},{j}]"))
            self.grid.append(row)

        # 2. Filas únicas
        for row in self.grid:
            self.model.AddAllDifferent(row)

        # 3. Columnas únicas
        for j in range(self.size):
            col = [self.grid[i][j] for i in range(self.size)]
            self.model.AddAllDifferent(col)

    # ==========================================
    #      IMPLEMENTACIÓN DE REGLAS
    # ==========================================

    def _apply_sum(self, cells, result):
        nivs = self._get_vars_from_cells(cells)
        self.model.Add(sum(nivs) == result)

    def _apply_mult(self, cells, result):
        nivs = self._get_vars_from_cells(cells)
        product = self.model.NewConstant(1)
        for niv in nivs:
            current_max = self.size ** len(nivs)
            new_product = self.model.NewIntVar(1, max(result, current_max), "")
            self.model.AddMultiplicationEquality(new_product, [product, niv])
            product = new_product
        self.model.Add(product == result)

    def _apply_sub(self, cells, result):
        nivs = self._get_vars_from_cells(cells)
        if len(nivs) != 2: return 
        a, b = nivs[0], nivs[1]
        
        way1 = self.model.NewBoolVar("sub_way1")
        way2 = self.model.NewBoolVar("sub_way2")
        
        self.model.Add(a - b == result).OnlyEnforceIf(way1)
        self.model.Add(b - a == result).OnlyEnforceIf(way2)
        self.model.AddBoolOr([way1, way2])

    def _apply_div(self, cells, result):
        nivs = self._get_vars_from_cells(cells)
        if len(nivs) != 2: return
        a, b = nivs[0], nivs[1]

        way1 = self.model.NewBoolVar("div_way1")
        way2 = self.model.NewBoolVar("div_way2")

        self.model.Add(a == b * result).OnlyEnforceIf(way1)
        self.model.Add(b == a * result).OnlyEnforceIf(way2)
        self.model.AddBoolOr([way1, way2])

    def _apply_exp(self, cells, result):
        nivs = self._get_vars_from_cells(cells)
        if len(nivs) != 2: return
        a, b = nivs[0], nivs[1]

        way1 = self.model.NewBoolVar("exp_way1")
        way2 = self.model.NewBoolVar("exp_way2")

        self.model.AddPower(a, b, result).OnlyEnforceIf(way1)
        self.model.AddPower(b, a, result).OnlyEnforceIf(way2)
        self.model.AddBoolOr([way1, way2])

    def _apply_mod(self, cells, result):
        nivs = self._get_vars_from_cells(cells)
        if len(nivs) != 2: return
        a, b = nivs[0], nivs[1]
        
        way1 = self.model.NewBoolVar("mod_way1")
        way2 = self.model.NewBoolVar("mod_way2")

        # a % b = res  =>  a = b * q1 + res
        q1 = self.model.NewIntVar(0, self.size, "q1")
        prod1 = self.model.NewIntVar(0, self.size * self.size, "p1")
        self.model.AddMultiplicationEquality(prod1, [b, q1])
        self.model.Add(a == prod1 + result).OnlyEnforceIf(way1)
        
        # b % a = res
        q2 = self.model.NewIntVar(0, self.size, "q2")
        prod2 = self.model.NewIntVar(0, self.size * self.size, "p2")
        self.model.AddMultiplicationEquality(prod2, [a, q2])
        self.model.Add(b == prod2 + result).OnlyEnforceIf(way2)
        
        self.model.AddBoolOr([way1, way2])

    def _apply_range(self, cells, result):
        nivs = self._get_vars_from_cells(cells)
        max_v = self.model.NewIntVar(1, self.size, "")
        min_v = self.model.NewIntVar(1, self.size, "")
        
        self.model.AddMaxEquality(max_v, nivs)
        self.model.AddMinEquality(min_v, nivs)
        self.model.Add(max_v - min_v == result)

    def _apply_pair_prod_max(self, cells, result):
        nivs = self._get_vars_from_cells(cells)
        pair_products = []
        for i in range(len(nivs)):
            for j in range(i + 1, len(nivs)):
                p = self.model.NewIntVar(1, self.size * self.size, "")
                self.model.AddMultiplicationEquality(p, [nivs[i], nivs[j]])
                pair_products.append(p)
        
        if not pair_products: return
        max_p = self.model.NewIntVar(1, self.size * self.size, "")
        self.model.AddMaxEquality(max_p, pair_products)
        self.model.Add(max_p == result)

    def _apply_sum_squares(self, cells, result):
        nivs = self._get_vars_from_cells(cells)
        squares = []
        for niv in nivs:
            sq = self.model.NewIntVar(1, self.size * self.size, "")
            self.model.AddMultiplicationEquality(sq, [niv, niv])
            squares.append(sq)
        self.model.Add(sum(squares) == result)

    def solve(self):
        self._create_board_variables()

        for rule in self.rules:
            # --- CORRECCIÓN AQUÍ: Evitar .get() si no es diccionario ---
            if hasattr(rule, 'operation'):
                op = rule.operation
                cells = rule.cells
                res = rule.result
            else:
                # Fallback para diccionarios
                op = rule.get('operation')
                cells = rule.get('cells')
                res = rule.get('result')

            if op == "+": self._apply_sum(cells, res)
            elif op == "*": self._apply_mult(cells, res)
            elif op == "-": self._apply_sub(cells, res)
            elif op == "/": self._apply_div(cells, res)
            elif op == "mod": self._apply_mod(cells, res)
            elif op == "^": self._apply_exp(cells, res)
            elif op == "range": self._apply_range(cells, res)
            elif op == "pair_prod_max": self._apply_pair_prod_max(cells, res)
            elif op == "sum_sq": self._apply_sum_squares(cells, res)
            elif op == "=": self._apply_sum(cells, res)

        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            solution_grid = []
            for i in range(self.size):
                row_vals = []
                for j in range(self.size):
                    val = solver.Value(self.grid[i][j])
                    row_vals.append(int(val))
                solution_grid.append(row_vals)
            return solution_grid
        else:
            return None