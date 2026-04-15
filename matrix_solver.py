import sympy as sp
from sympy import Matrix, latex, pretty, eye, I, conjugate, simplify, symbols, Eq, solve
from sympy.parsing.sympy_parser import parse_expr


def parse_matrix(matrix_list):
    try:
        parsed = [[parse_expr(str(entry), evaluate=True) for entry in row] for row in matrix_list]
        return Matrix(parsed)
    except Exception as e:
        raise ValueError(f"Invalid matrix input: {e}")


def handle_operations(A, B=None, operation=None, scalar=None):
    steps = []
    if operation == 'add':
        if A.shape != B.shape:
            raise ValueError("Addition requires matrices of the same shape.")
        result = A + B
        steps.append("Given matrices A and B.")
        steps.append("Add corresponding elements of A and B.")
        
        steps.append(f"A B = {latex(result)}")
    elif operation == 'subtract':
        if A.shape != B.shape:
            raise ValueError("Subtraction requires matrices of the same shape.")
        result = A - B
        steps.append(f"A - B = {latex(result)}")
    elif operation == 'multiply':
        if A.shape[1] != B.shape[0]:
            raise ValueError("Matrix multiplication requires A.columns == B.rows.")
        result = A * B
        steps.append(f"A B = {latex(result)}")
    elif operation == 'scalar':
        if scalar is None:
            raise ValueError("Scalar value required for scalar multiplication.")
        result = scalar * A
        steps.append(f"{scalar} A = {latex(result)}")
    elif operation == 'inverse':
        if A.shape[0] != A.shape[1]:
            raise ValueError("Inverse requires a square matrix.")
        if A.det() == 0:
            raise ValueError("Matrix is singular and not invertible.")
        result = A.inv()
        steps.append(f"A^{{-1}} = {latex(result)}")
    elif operation == 'transpose':
        result = A.T
        steps.append(f"A^T = {latex(result)}")
    else:
        raise ValueError("Unknown operation.")
    return {"result_latex": latex(result), "result_str": pretty(result), "steps": steps}


def handle_determinant(A):
    if A.shape[0] != A.shape[1]:
        raise ValueError("Determinant requires a square matrix.")
    det = A.det()
    steps = [f"\\det(A) = {latex(det)}"]
    if det == 0:
        steps.append("Matrix is singular (not invertible).")
        return {"result_latex": latex(det), "result_str": str(det), "steps": steps}
    # Also return inverse if exists
    inv = A.inv()
    steps.append(f"A^{{-1}} = {latex(inv)}")
    return {"result_latex": latex(det), "result_str": str(det), "steps": steps, "inverse_latex": latex(inv), "inverse_str": pretty(inv)}


def handle_echelon(A):
    # If symbolic, do not attempt row reduction
    if len(A.free_symbols) > 0:
        return {"result_latex": latex(A), "result_str": pretty(A), "steps": ["Row reduction is not supported for symbolic matrices."]}
    # Track steps
    ops = []
    M = A.as_mutable()
    m, n = M.shape
    pivots = []
    for col in range(n):
        # Find pivot
        pivot_row = None
        for row in range(col, m):
            if M[row, col] != 0:
                pivot_row = row
                break
        if pivot_row is None:
            continue
        if pivot_row != col:
            M.row_swap(col, pivot_row)
            ops.append(f"R_{{{col+1}}} \\leftrightarrow R_{{{pivot_row+1}}}")
        pivots.append((col, col))
        # Make pivot 1
        if M[col, col] != 1:
            factor = M[col, col]
            M.row_op(col, lambda x, _: x / factor)
            ops.append(f"R_{{{col+1}}} \\to R_{{{col+1}}}/({latex(factor)})")
        # Eliminate below
        for row in range(col+1, m):
            if M[row, col] != 0:
                factor = M[row, col]
                M.row_op(row, lambda x, j: x - factor * M[col, j])
                ops.append(f"R_{{{row+1}}} \\to R_{{{row+1}}} - ({latex(factor)})R_{{{col+1}}}")
    steps = []
    
    for i, op in enumerate(ops):
        op_arrow = op.replace('.', ' \\to ')
        steps.append(f"Step {i+1}: {op_arrow}")
    steps.append(f"Row Echelon Form (REF): {latex(M)}")
    # After REF is obtained
    rank_A = A.rank()
    rank_aug = M.rank()
    n_vars = A.shape[1] - 1 if A.shape[1] > A.shape[0] else A.shape[1]

    if rank_A == rank_aug:
        if rank_A == n_vars:
            steps.append("System is consistent with a unique solution.")
        else:
            steps.append("System is consistent with infinitely many solutions.")
    else:
        steps.append("System is inconsistent (no solution).")

    return {"result_latex": latex(M), "result_str": pretty(M), "steps": steps}


def handle_paq(A):
    # If symbolic, do not attempt PAQ
    if len(A.free_symbols) > 0:
        return {"result_latex": latex(A), "result_str": pretty(A), "steps": ["PAQ factorization is not supported for symbolic matrices."]}
    if A.shape != (3, 3):
        raise ValueError("PAQ factorization is only implemented for 3x3 matrices.")
    from sympy import eye, Matrix
    M = A.as_mutable()
    P = eye(3)
    Q = eye(3)
    steps = [f"Initial: {latex(M)}"]
    # Row operations to REF
    for i in range(3):
        # Find pivot in column i
        pivot_row = None
        for r in range(i, 3):
            if M[r, i] != 0:
                pivot_row = r
                break
        if pivot_row is None:
            continue
        if pivot_row != i:
            M.row_swap(i, pivot_row)
            P.row_swap(i, pivot_row)
            steps.append(f"R_{{{i+1}}} \\leftrightarrow R_{{{pivot_row+1}}}: {latex(M)}")
        # Make pivot 1
        if M[i, i] != 1:
            factor = M[i, i]
            M.row_op(i, lambda x, _: x / factor)
            P.row_op(i, lambda x, _: x / factor)
            steps.append(f"R_{{{i+1}}} \\to R_{{{i+1}}}/({latex(factor)}): {latex(M)}")
        # Eliminate below
        for r in range(i+1, 3):
            if M[r, i] != 0:
                factor = M[r, i]
                M.row_op(r, lambda x, j: x - factor * M[i, j])
                P.row_op(r, lambda x, j: x - factor * P[i, j])
                steps.append(f"R_{{{r+1}}} \\to R_{{{r+1}}} - ({latex(factor)})R_{{{i+1}}}: {latex(M)}")
    # Column operations to identity
    for i in range(3):
        # Find pivot in row i
        pivot_col = None
        for c in range(i, 3):
            if M[i, c] != 0:
                pivot_col = c
                break
        if pivot_col is None:
            continue
        if pivot_col != i:
            M.col_swap(i, pivot_col)
            Q.col_swap(i, pivot_col)
            steps.append(f"C_{{{i+1}}} \\leftrightarrow C_{{{pivot_col+1}}}: {latex(M)}")
        # Make pivot 1 (already done by row ops)
        # Eliminate above
        for c in range(i+1, 3):
            if M[i, c] != 0:
                factor = M[i, c]
                M.col_op(c, lambda x, j: x - factor * M[j, i])
                Q.col_op(c, lambda x, j: x - factor * Q[j, i])
                steps.append(f"C_{{{c+1}}} \\to C_{{{c+1}}} - ({latex(factor)})C_{{{i+1}}}: {latex(M)}")
    steps.append(f"Final PAQ: {latex(M)}")
    steps.append(f"P = {latex(P)}")
    steps.append(f"Q = {latex(Q)}")
    rank = M.rank()
    steps.append(f"Rank(A) = {rank}")
    inv = None
    if rank == 3 and A.det() != 0:
        inv = Q * P
        steps.append(f"A^{{-1}} = QP = {latex(inv)}")
    return {"result_latex": latex(M), "result_str": pretty(M), "steps": steps, "P": latex(P), "Q": latex(Q), "rank": rank, "inverse_latex": latex(inv) if inv is not None else None}


def handle_rank(A):
    rank = A.rank()
    steps = [f"Rank(A) = {rank}"]
    return {"result_latex": str(rank), "result_str": str(rank), "steps": steps}


def solve_for_type(A, typeCheck, k=None):
    n, m = A.shape
    if n != m:
        raise ValueError("Type checks require a square matrix.")
    unknowns = list(A.free_symbols)
    if k is not None:
        unknowns.append(k)
    if typeCheck == "orthogonal":
        k = k or 1
        eq = simplify((k*A)*(k*A).T - eye(n))
    elif typeCheck == "unitary":
        k = k or 1
        eq = simplify((k*A)*(k*A).H - eye(n))
    elif typeCheck == "hermitian":
        eq = simplify(A - A.H)
    elif typeCheck == "skewhermitian":
        eq = simplify(A + A.H)
    elif typeCheck == "symmetric":
        eq = simplify(A - A.T)
    elif typeCheck == "skewsymmetric":
        eq = simplify(A + A.T)
    else:
        raise ValueError("Unknown typeCheck for symbolic solve.")
    equations = []
    for i in range(n):
        for j in range(n):
            equations.append(Eq(eq[i, j], 0))
    sol = solve(equations, unknowns, dict=True)
    return sol


def check_matrix_types(A, typeCheck, k_value=None):
    results = {}
    n, m = A.shape
    if n != m:
        raise ValueError("Type checks require a square matrix.")
    # Symbolic solve mode
    if len(A.free_symbols) > 0 or (k_value is not None and str(k_value) != '1'):
        k = None
        if k_value is not None and str(k_value) != '1':
            k = symbols('k')
        sol = solve_for_type(A, typeCheck, k)
        steps = [f"Solutions for {typeCheck}: {sol}"]
        return {"result_latex": latex(A), "result_str": pretty(A), "steps": steps, "solutions": sol}
    def is_hermitian(M):
        return M.equals(M.H)
    def is_skewhermitian(M):
        return M.equals(-M.H)
    def is_unitary(M):
        return simplify(M * M.H).equals(eye(n))
    def is_orthogonal(M):
        return simplify(M * M.T).equals(eye(n))
    def is_symmetric(M):
        return M.equals(M.T)
    def is_skewsymmetric(M):
        return M.equals(-M.T)
    checks = {
        "hermitian": is_hermitian,
        "skewhermitian": is_skewhermitian,
        "unitary": is_unitary,
        "orthogonal": is_orthogonal,
        "symmetric": is_symmetric,
        "skewsymmetric": is_skewsymmetric,
    }
    if typeCheck == "all":
        for k, func in checks.items():
            results[k] = func(A)
    elif typeCheck in checks:
        results[typeCheck] = checks[typeCheck](A)
    else:
        raise ValueError("Unknown typeCheck.")
    steps = [f"{k.replace('_',' ').title()}: {'Yes' if v else 'No'}" for k, v in results.items()]
    return {"result_latex": latex(A), "result_str": pretty(A), "steps": steps, "type_results": results}


def solve_matrix_problem(data):
    try:
        type_ = data.get("type")
        A = parse_matrix(data["A"])
        B = parse_matrix(data["B"]) if data.get("B") else None
        operation = data.get("operation")
        typeCheck = data.get("typeCheck", "all")
        scalar = None
        k_value = data.get("typeCheckConstant", "1")
        # New: handle 'solveconstants' type
        if type_ == "solveconstants":
            property_ = data.get("property", "orthogonal")
            try:
                sol = solve_for_type(A, property_)
                steps = [f"Solutions for {property_}: {repr(sol)}"]
                return {"result_latex": latex(A), "result_str": pretty(A), "steps": steps, "solutions": sol}
            except Exception as e:
                return {"result_latex": latex(A), "result_str": pretty(A), "steps": [f"Error: {str(e)}"], "solutions": None, "error": str(e)}
        if operation == "scalar":
            scalar = parse_expr(str(data.get("scalar", "1")), evaluate=True)
        if type_ == "operations":
            return handle_operations(A, B, operation, scalar)
        elif type_ == "determinant":
            return handle_determinant(A)
        elif type_ == "echelon":
            return handle_echelon(A)
        elif type_ == "paq":
            return handle_paq(A)
        elif type_ == "typecheck":
            return check_matrix_types(A, typeCheck, k_value)
        elif type_ == "rank":
            return handle_rank(A)
        else:
            raise ValueError("Unknown problem type.")
    except Exception as e:
        return {"error": str(e)} 