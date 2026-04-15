# linear_algebra_solver.py — step-by-step Linear Algebra (Matrices) solver
from sympy import Matrix, symbols, latex, eye, simplify, factor, Poly, Symbol
from sympy.matrices.common import NonSquareMatrixError

t = Symbol('t')
lam = symbols('lambda')

# ----------------------------
# LaTeX helper
# ----------------------------
def _L(x):
    """Return a LaTeX string wrapped in math delimiters."""
    try:
        if isinstance(x, Matrix):
            # Pretty bmatrix for matrices/vectors
            return r"\(" + latex(x, mat_delim="bmatrix") + r"\)"
        return r"\(" + latex(x) + r"\)"
    except Exception:
        return str(x)

def _num_step(n, body_latex):
    return f"{n}. {body_latex}"

def _to_matrix(data):
    rows = []
    for row in data:
        rows.append([simplify(str(x)) for x in row])
    return Matrix(rows)

# ----------------------------
# Characteristic polynomial
# ----------------------------
def _char_poly_info(A):
    n = A.shape[0]
    cp = A.charpoly(lam)
    p = factor(cp.as_expr())
    coeffs = cp.all_coeffs()
    return n, p, coeffs, cp

# ----------------------------
# Cayley–Hamilton helpers
# ----------------------------
def _poly_of_A(A, coeffs):
    n = A.shape[0]
    acc = Matrix.zeros(n)
    for k, c in enumerate(coeffs):
        deg = len(coeffs) - 1 - k
        term = (A ** deg) if deg > 0 else eye(n)
        acc = acc + c * term
    return simplify(acc)

def _reduce_A_power(A, k, charpoly_expr):
    n = A.shape[0]
    x = lam
    p = Poly(charpoly_expr, x)
    q = Poly(x**k, x)
    r = q.rem(p)
    out = Matrix.zeros(n)
    for i, coeff in enumerate(r.all_coeffs()):
        deg = r.degree() - i
        term = (A ** deg) if deg > 0 else eye(n)
        out = out + coeff * term
    return simplify(out), r

# ----------------------------
# Jordan profile for similarity
# ----------------------------
def _jordan_profile(M):
    """Return a sorted list of (eigenvalue_latex, block_size)."""
    blocks = []
    try:
        for blk in M.jordan_cells():
            lam_val = blk[0, 0]
            blocks.append((_L(lam_val), blk.shape[0]))
    except Exception:
        # fallback if jordan fails
        from sympy.polys.polytools import factor as _factor
        try:
            mp = M.minimal_polynomial(x=lam)
            blocks.append(("mp:" + _L(_factor(mp)), 0))
        except Exception:
            blocks.append(("fallback", M.shape[0]))
    return sorted(blocks)

def _are_similar(A, B):
    if A.shape != B.shape:
        return False, "Shapes differ"

    _, pA, _, _ = _char_poly_info(A)
    _, pB, _, _ = _char_poly_info(B)
    same_char = simplify(pA - pB) == 0

    profA = _jordan_profile(A)
    profB = _jordan_profile(B)
    similar = (profA == profB)
    reason = "Same Jordan profile" if similar else "Jordan profiles differ"
    return bool(similar), same_char, pA, pB, profA, profB, reason

# ----------------------------
# Main solver
# ----------------------------
def solve_linear_algebra(payload):
    steps = []
    step_no = 1
    try:
        if "A" not in payload:
            return {"success": False, "error": "Matrix A is required."}

        A = _to_matrix(payload["A"])
        if A.rows != A.cols:
            return {"success": False, "error": "Matrix must be square."}

        task = payload.get("task", "eigen")
        n, p_expr, coeffs, cp = _char_poly_info(A)

        steps.append(_num_step(step_no, rf"Given \(A \in \mathbb{{R}}^{{{n}\times{n}}}\): A = {_L(A)}")); step_no += 1
        steps.append(_num_step(step_no, rf"Characteristic polynomial: \(p(\lambda)={_L(p_expr)}\)")); step_no += 1

        # ----------------------------------
        # Eigenvalues & Eigenvectors
        # ----------------------------------
        if task == "eigen":
            eigenvals = A.eigenvals()
            steps.append(_num_step(step_no, r"Solve \(p(\lambda)=0\) to get eigenvalues."))
            step_no += 1

            ev_mults = [(ev, eigenvals[ev]) for ev in eigenvals]
            step_text = (
                r"Eigenvalues: "
            + ", ".join([rf"\(\lambda={_L(ev)} \;(\text{{alg mult}}={mult})\)" for ev, mult in ev_mults])
            )
            steps.append(_num_step(step_no, step_text))
            step_no += 1

            eigvects = A.eigenvects()
            ev_detail = []
            for (ev, am, basis) in eigvects:
                geo = len(basis)
                basis_cols = r"\;,\;".join([_L(b) for b in basis]) if basis else "—"
                steps.append(_num_step(step_no, rf"For \(\lambda={_L(ev)}\), solve \((A-\lambda I)\mathbf{{x}}=\mathbf{{0}}\). Basis: {basis_cols}"))

                step_no += 1
                ev_detail.append({"lambda": _L(ev), "alg_mult": am, "geo_mult": geo, "basis": [_L(b) for b in basis]})

            diag = A.is_diagonalizable()
            steps.append(_num_step(step_no, rf"Diagonalizable? {'Yes' if diag else 'No'}")); step_no += 1

            return {"success": True, "task": "eigen", "steps": steps,
                    "result": {"char_poly": _L(p_expr),
                               "eigenvalues": [{"value": _L(ev), "alg_mult": m} for ev, m in eigenvals.items()],
                               "eigenvectors": ev_detail,
                               "diagonalizable": bool(diag)}}

        # ----------------------------------
        # Cayley–Hamilton
        # ----------------------------------
        elif task == "cayley":
            steps.append(_num_step(step_no, r"By Cayley–Hamilton, \(p(A)=\mathbf{0}\).")); step_no += 1

            pA = _poly_of_A(A, coeffs)
            is_zero = (pA == Matrix.zeros(n))

            if is_zero:
                steps.append(_num_step(step_no, r"Compute \(p(A)\): \mathbf{0}"))
            else:
                steps.append(_num_step(step_no, rf"Compute \(p(A)\): {_L(pA)}"))
            step_no += 1

            reduce_degrees = payload.get("reduce_degrees", [n, n+1])
            red_items = []
            for k in reduce_degrees:
                Ak_red, rpoly = _reduce_A_power(A, k, p_expr)
                steps.append(_num_step(step_no, rf"Reduce \(A^{k}\) via remainder \(r(\lambda)={_L(rpoly.as_expr())}\) ⇒ \(A^{k}={_L(Ak_red)}\)"))
                step_no += 1
                red_items.append({"k": k, "expr": _L(Ak_red), "r_poly": _L(rpoly.as_expr())})

            return {"success": True, "task": "cayley", "steps": steps,
                    "result": {"char_poly": _L(p_expr), "pA_is_zero": bool(is_zero), "reductions": red_items}}

        # ----------------------------------
        # Diagonalization
        # ----------------------------------
        elif task == "diagonalize":
            diag = A.is_diagonalizable()
            steps.append(_num_step(step_no, r"Check diagonalizability.")); step_no += 1
            eigvects = A.eigenvects()
            total_geo = sum(len(basis) for (_, _, basis) in eigvects)
            steps.append(_num_step(step_no, rf"Total eigenvectors: {total_geo}")); step_no += 1

            if diag:
                P_cols, D_diags = [], []
                for (ev, am, basis) in eigvects:
                    for b in basis:
                        P_cols.append(b); D_diags.append(ev)
                P = Matrix.hstack(*P_cols)
                D = Matrix.diag(*D_diags)
                steps.append(_num_step(step_no, r"Construct \(P, D\).")); step_no += 1
                return {"success": True, "task": "diagonalize", "steps": steps,
                        "result": {"diagonalizable": True, "P": _L(P), "D": _L(D)}}
            else:
                return {"success": True, "task": "diagonalize", "steps": steps,
                        "result": {"diagonalizable": False}}

        # ----------------------------------
        # Similarity
        # ----------------------------------
        elif task == "similarity":
            if "B" not in payload:
                return {"success": False, "error": "Matrix B required."}
            B = _to_matrix(payload["B"])
            if B.shape != A.shape:
                return {"success": False, "error": "A and B must have same shape."}

            similar, same_char, pA, pB, profA, profB, reason = _are_similar(A, B)
            steps.append(_num_step(step_no, rf"For \(B\): \(p_B(\lambda)={_L(pB)}\)")); step_no += 1
            steps.append(_num_step(step_no, f"Characteristic polynomials equal? {'Yes' if same_char else 'No'}")); step_no += 1
            steps.append(_num_step(step_no, rf"Jordan profiles: \(A\): {profA} ; \(B\): {profB}")); step_no += 1
            steps.append(_num_step(step_no, rf"Similarity test: {'Yes' if similar else 'No'} ({reason})")); step_no += 1

            return {"success": True, "task": "similarity", "steps": steps,
                    "result": {"similar": bool(similar),
                               "char_poly_A": _L(pA), "char_poly_B": _L(pB),
                               "jordan_profile_A": profA, "jordan_profile_B": profB}}

        else:
            return {"success": False, "error": f"Unknown task '{task}'."}

    except NonSquareMatrixError:
        return {"success": False, "error": "Matrix must be square."}
    except Exception as e:
        return {"success": False, "error": str(e)}
