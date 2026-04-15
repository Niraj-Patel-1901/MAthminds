"""
numerical_methods.py

Flask blueprint exposing /api/numerical that runs:
- newton
- regula_falsi
- gauss_jacobi
- gauss_seidel

Input (JSON):
{
  "method": "newton" | "regula_falsi" | "gauss_jacobi" | "gauss_seidel",
  "payload": { ... method-specific ... }
}

Outputs JSON:
{
  "success": True/False,
  "method": "...",
  "converged": True/False,
  "iterations": N,
  "result": <value or list>,
  "latex_steps": [ "...latex..." , ... ],
  "errors": [ ... per-iteration absolute errors ... ],
  "message": "helpful message"
}
"""

from flask import Blueprint, request, jsonify
import numpy as np
import math

# We'll use sympy for parsing functions and differentiating
try:
    import sympy as sp
except Exception as e:
    sp = None

bp = Blueprint("numerical_methods_bp", __name__)

# ------------------------
# Utilities
# ------------------------
def safe_float(x):
    try:
        return float(x)
    except:
        return None

def format_vec_latex(vec):
    # returns LaTeX vector form
    items = ",".join([f"{v:.6g}" for v in vec])
    return r"\begin{bmatrix}" + items + r"\end{bmatrix}"

def norm_inf(vec):
    return float(np.max(np.abs(np.array(vec, dtype=float))))

# ------------------------
# Newton-Raphson
# ------------------------
def newton_method(expr_str, x0, tol=1e-6, max_iter=50):
    if sp is None:
        return {"success": False, "message": "sympy is required for Newton-Raphson. Install sympy."}

    x = sp.symbols('x')
    try:
        f_sym = sp.sympify(expr_str)
    except Exception as e:
        return {"success": False, "message": f"Could not parse function: {e}"}

    fprime_sym = sp.diff(f_sym, x)
    f = sp.lambdify(x, f_sym, modules=["numpy", "math"])
    fprime = sp.lambdify(x, fprime_sym, modules=["numpy", "math"])

    steps = []
    errors = []
    xi = float(x0)
    steps.append(rf"\textbf{{Newton-Raphson}}: \quad x_0 = {xi}")
    converged = False

    for k in range(1, max_iter+1):
        try:
            fx = float(f(xi))
            fpx = float(fprime(xi))
        except Exception as e:
            return {"success": False, "message": f"Function evaluation failed at iteration {k}: {e}"}
        if abs(fpx) < 1e-14:
            return {"success": False, "message": f"Derivative nearly zero at x = {xi}; method may fail."}

        x_next = xi - fx / fpx
        err = abs(x_next - xi)
        errors.append(err)

        # LaTeX step
        step_latex = (rf"Iteration\ {k}:\quad x_{{{k}}} = x_{{{k-1}}} - \frac{{f(x_{{{k-1}}})}}{{f'(x_{{{k-1}}})}} = "
                      rf"{xi:.6g} - \frac{{{fx:.6g}}}{{{fpx:.6g}}} = {x_next:.12g} \quad \text{{error}} = {err:.6g}")
        steps.append(step_latex)

        if err < tol:
            converged = True
            return {
                "success": True,
                "method": "newton",
                "converged": True,
                "iterations": k,
                "result": float(x_next),
                "latex_steps": steps,
                "errors": errors,
                "message": f"Converged in {k} iterations to {x_next:.12g} with tolerance {tol}."
            }

        xi = x_next

    # if reached here, not converged
    return {
        "success": True,
        "method": "newton",
        "converged": False,
        "iterations": max_iter,
        "result": float(xi),
        "latex_steps": steps,
        "errors": errors,
        "message": f"Stopped after {max_iter} iterations; tolerance {tol} not reached. Last x = {xi:.12g}."
    }

# ------------------------
# Regula-Falsi (False Position)
# ------------------------
def regula_falsi_method(expr_str, a, b, tol=1e-6, max_iter=50):
    if sp is None:
        return {"success": False, "message": "sympy is required for Regula-Falsi. Install sympy."}

    x = sp.symbols('x')
    try:
        f_sym = sp.sympify(expr_str)
    except Exception as e:
        return {"success": False, "message": f"Could not parse function: {e}"}
    f = sp.lambdify(x, f_sym, modules=["numpy", "math"])

    fa = float(f(a))
    fb = float(f(b))
    if fa * fb > 0:
        return {"success": False, "message": "Function values at endpoints must have opposite signs (f(a)*f(b) < 0)."}

    steps = []
    errors = []
    steps.append(rf"\textbf{{Regula-Falsi}}: \quad a = {a},\ b = {b},\ f(a)={fa:.6g},\ f(b)={fb:.6g}")

    x_old = None
    converged = False

    for k in range(1, max_iter+1):
        # compute c by false position
        c = (a * fb - b * fa) / (fb - fa)
        fc = float(f(c))

        if x_old is None:
            err = None
        else:
            err = abs(c - x_old)
            errors.append(err)

        steps.append(rf"Iteration\ {k}:\quad c = \frac{{a f(b) - b f(a)}}{{f(b)-f(a)}} = {c:.12g},\ f(c)={fc:.6g}"
                     + (rf",\ error = {err:.6g}" if err is not None else ""))

        # check sign
        if fa * fc < 0:
            b = c
            fb = fc
        else:
            a = c
            fa = fc

        if err is not None and err < tol:
            converged = True
            return {
                "success": True,
                "method": "regula_falsi",
                "converged": True,
                "iterations": k,
                "result": float(c),
                "latex_steps": steps,
                "errors": errors,
                "message": f"Converged in {k} iterations to {c:.12g}."
            }

        x_old = c

    return {
        "success": True,
        "method": "regula_falsi",
        "converged": False,
        "iterations": max_iter,
        "result": float(c),
        "latex_steps": steps,
        "errors": errors,
        "message": f"Stopped after {max_iter} iterations; tolerance {tol} not reached. Last c = {c:.12g}."
    }

# ------------------------
# Jacobi & Gauss-Seidel helpers
# ------------------------
def check_diagonal_dominance(A):
    A = np.array(A, dtype=float)
    n = A.shape[0]
    strictly = True
    for i in range(n):
        diag = abs(A[i, i])
        off = np.sum(np.abs(A[i, :])) - diag
        if diag < off:
            strictly = False
            break
    return strictly

def jacobi_iteration(A, b, x0=None, tol=1e-6, max_iter=100):
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    n = A.shape[0]

    if x0 is None:
        x = np.zeros(n, dtype=float)
    else:
        x = np.array(x0, dtype=float)

    D = np.diag(np.diag(A))
    R = A - D  # R = L + U

    # Iteration matrix for Jacobi: T = D^{-1} * (-R)
    try:
        D_inv = np.linalg.inv(D)
    except np.linalg.LinAlgError:
        return {"success": False, "message": "Matrix D (diagonal) singular - cannot compute Jacobi."}

    T = -D_inv.dot(R)
    # spectral radius
    eigs = np.linalg.eigvals(T)
    rho = max(abs(eigs))

    steps = []
    errors = []
    steps.append(rf"\textbf{{Gauss-Jacobi}}: \quad A = {format_vec_latex(A.flatten())} \text{{ (flattened) }},\ b = {format_vec_latex(b)}")
    steps.append(rf"Iteration\ matrix\ T = D^{{-1}}( - (L+U) ).\ \rho(T) = {rho:.6g}")

    converged = False
    for k in range(1, max_iter+1):
        x_new = np.zeros_like(x)
        for i in range(n):
            s = np.dot(A[i, :], x) - A[i, i] * x[i]
            x_new[i] = (b[i] - s) / A[i, i]
        err = norm_inf(x_new - x)
        errors.append(err)
        steps.append(rf"Iter\ {k}:\quad x^{{({k})}} = {format_vec_latex(x_new)}\quad ||x^{{({k})}}-x^{{({k-1})}}||_{{\infty}} = {err:.6g}")
        if err < tol:
            converged = True
            return {
                "success": True,
                "method": "gauss_jacobi",
                "converged": True,
                "iterations": k,
                "result": x_new.tolist(),
                "latex_steps": steps,
                "errors": errors,
                "spectral_radius": float(rho),
                "message": f"Converged in {k} iterations with infinity-norm error {err:.6g}."
            }
        x = x_new

    return {
        "success": True,
        "method": "gauss_jacobi",
        "converged": False,
        "iterations": max_iter,
        "result": x.tolist(),
        "latex_steps": steps,
        "errors": errors,
        "spectral_radius": float(rho),
        "message": f"Stopped after {max_iter} iterations; tolerance {tol} not reached. Last error = {err:.6g}."
    }

def gauss_seidel_iteration(A, b, x0=None, tol=1e-6, max_iter=100):
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    n = A.shape[0]

    if x0 is None:
        x = np.zeros(n, dtype=float)
    else:
        x = np.array(x0, dtype=float)

    # Build iteration matrix for spectral radius check:
    D = np.diag(np.diag(A))
    L = -np.tril(A, -1)
    U = -np.triu(A, 1)
    # For Gauss-Seidel, T_gs = (D - L)^{-1} U
    try:
        inv_DL = np.linalg.inv(D - (-np.tril(A, -1)))  # D - L; note L was extracted differently; simplify:
        # Recompute properly:
        D = np.diag(np.diag(A))
        L_mat = np.tril(A, -1)
        U_mat = np.triu(A, 1)
        inv_DL = np.linalg.inv(D + L_mat)  # D + L because L_mat contains negative sign earlier? simpler: use formula below
    except Exception:
        # fallback: compute T numerically from Gauss-Seidel iteration for spectral radius approx
        inv_DL = None

    # Alternative correct assembly:
    D = np.diag(np.diag(A))
    L = np.tril(A, -1)
    U = np.triu(A, 1)
    try:
        T_gs = -np.linalg.inv(D + L).dot(U)
        eigs = np.linalg.eigvals(T_gs)
        rho = max(abs(eigs))
    except Exception:
        T_gs = None
        rho = float('nan')

    steps = []
    errors = []
    steps.append(rf"\textbf{{Gauss-Seidel}}: \quad A = {format_vec_latex(A.flatten())} \text{{ (flattened) }},\ b = {format_vec_latex(b)}")
    steps.append(rf"Iteration\ matrix\ T_{{GS}} = (D+L)^{{-1}}(-U). \ \rho(T_{{GS}}) \approx {rho if not math.isnan(rho) else 'N/A'}")

    converged = False
    for k in range(1, max_iter+1):
        x_new = x.copy()
        for i in range(n):
            s1 = np.dot(A[i, :i], x_new[:i])  # using updated values
            s2 = np.dot(A[i, i+1:], x[i+1:])  # old values
            x_new[i] = (b[i] - s1 - s2) / A[i, i]

        err = norm_inf(x_new - x)
        errors.append(err)
        steps.append(rf"Iter\ {k}:\quad x^{{({k})}} = {format_vec_latex(x_new)}\quad ||x^{{({k})}}-x^{{({k-1})}}||_{{\infty}} = {err:.6g}")
        if err < tol:
            converged = True
            return {
                "success": True,
                "method": "gauss_seidel",
                "converged": True,
                "iterations": k,
                "result": x_new.tolist(),
                "latex_steps": steps,
                "errors": errors,
                "spectral_radius": (float(rho) if not math.isnan(rho) else None),
                "message": f"Converged in {k} iterations with infinity-norm error {err:.6g}."
            }
        x = x_new

    return {
        "success": True,
        "method": "gauss_seidel",
        "converged": False,
        "iterations": max_iter,
        "result": x.tolist(),
        "latex_steps": steps,
        "errors": errors,
        "spectral_radius": (float(rho) if not math.isnan(rho) else None),
        "message": f"Stopped after {max_iter} iterations; tolerance {tol} not reached. Last error = {err:.6g}."
    }

# ------------------------
# Flask endpoint
# ------------------------
@bp.route("/api/numerical", methods=["POST"])
def api_numerical():
    """
    Expected JSON body:
    {
      "method": "newton" | "regula_falsi" | "gauss_jacobi" | "gauss_seidel",
      "payload": { ... }
    }

    Payload examples:
    Newtown:
      { "expr": "x**3 - 2*x - 5", "x0": 2.0, "tol": 1e-6, "max_iter": 50 }

    Regula-Falsi:
      { "expr": "x**3 - x - 2", "a": 1.0, "b": 2.0, "tol": 1e-6, "max_iter": 50 }

    Jacobi/Seidel:
      { "A": [[4,-1,0],[-1,4,-1],[0,-1,4]], "b": [15,10,10], "x0": [0,0,0], "tol":1e-6, "max_iter":100 }
    """
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({"success": False, "message": f"Invalid JSON: {e}"}), 400

    method = data.get("method")
    payload = data.get("payload", {})

    if method is None:
        return jsonify({"success": False, "message": "Missing 'method' in request body."}), 400

    # Newton
    if method == "newton":
        expr = payload.get("expr")
        x0 = payload.get("x0")
        tol = payload.get("tol", 1e-6)
        max_iter = int(payload.get("max_iter", 50))
        if expr is None or x0 is None:
            return jsonify({"success": False, "message": "Newton requires 'expr' and 'x0'."}), 400
        res = newton_method(expr, x0, tol=tol, max_iter=max_iter)
        return jsonify(res)

    # Regula-Falsi
    if method == "regula_falsi":
        expr = payload.get("expr")
        a = payload.get("a")
        b = payload.get("b")
        tol = payload.get("tol", 1e-6)
        max_iter = int(payload.get("max_iter", 50))
        if expr is None or a is None or b is None:
            return jsonify({"success": False, "message": "Regula-Falsi requires 'expr', 'a', and 'b'."}), 400
        res = regula_falsi_method(expr, float(a), float(b), tol=tol, max_iter=max_iter)
        return jsonify(res)

    # Gauss-Jacobi
    if method == "gauss_jacobi":
        A = payload.get("A")
        b = payload.get("b")
        x0 = payload.get("x0", None)
        tol = payload.get("tol", 1e-6)
        max_iter = int(payload.get("max_iter", 100))
        if A is None or b is None:
            return jsonify({"success": False, "message": "Gauss-Jacobi requires 'A' and 'b'."}), 400
        # check dims
        try:
            A_arr = np.array(A, dtype=float)
            b_arr = np.array(b, dtype=float)
            if A_arr.shape[0] != A_arr.shape[1] or A_arr.shape[0] != b_arr.shape[0]:
                return jsonify({"success": False, "message": "Dimensions of A and b not compatible."}), 400
        except Exception as e:
            return jsonify({"success": False, "message": f"Could not parse A or b: {e}"}), 400

        # warn about diagonal dominance
        dd = check_diagonal_dominance(A)
        if not dd:
            warn_msg = "Warning: A is not strictly diagonally dominant. Jacobi may not converge."
        else:
            warn_msg = None

        res = jacobi_iteration(A, b, x0=x0, tol=tol, max_iter=max_iter)
        if warn_msg:
            res["warning"] = warn_msg
        return jsonify(res)

    # Gauss-Seidel
    if method == "gauss_seidel":
        A = payload.get("A")
        b = payload.get("b")
        x0 = payload.get("x0", None)
        tol = payload.get("tol", 1e-6)
        max_iter = int(payload.get("max_iter", 100))
        if A is None or b is None:
            return jsonify({"success": False, "message": "Gauss-Seidel requires 'A' and 'b'."}), 400
        try:
            A_arr = np.array(A, dtype=float)
            b_arr = np.array(b, dtype=float)
            if A_arr.shape[0] != A_arr.shape[1] or A_arr.shape[0] != b_arr.shape[0]:
                return jsonify({"success": False, "message": "Dimensions of A and b not compatible."}), 400
        except Exception as e:
            return jsonify({"success": False, "message": f"Could not parse A or b: {e}"}), 400

        dd = check_diagonal_dominance(A)
        if not dd:
            warn_msg = "Warning: A is not strictly diagonally dominant. Gauss-Seidel may not converge."
        else:
            warn_msg = None

        res = gauss_seidel_iteration(A, b, x0=x0, tol=tol, max_iter=max_iter)
        if warn_msg:
            res["warning"] = warn_msg
        return jsonify(res)

    # Method not recognized
    return jsonify({"success": False, "message": f"Unknown method: {method}"}), 400
