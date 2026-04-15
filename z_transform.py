# z_transform.py
from flask import Blueprint, request, jsonify
import sympy as sp

bp = Blueprint("z_transform", __name__)

# Symbols
k, z = sp.symbols('k z')
# For convenience in many formulas
a, C, n, alpha, beta = sp.symbols('a C n alpha beta')

def safe_sympify(s):
    if s is None:
        return None
    s = str(s).replace("−", "-").replace("^", "**")
    return sp.sympify(s)

def latex(obj):
    try:
        return sp.latex(sp.simplify(obj))
    except Exception:
        try:
            return sp.latex(obj)
        except Exception:
            return str(obj)

# ----------------- standard transforms (closed-form known formulas) -----------------
def transform_a_pow_k(a_val):
    # Z{a^k} = z/(z-a), ROC: |z| > |a|
    X = z/(z - a)
    roc = f"|z| > |{sp.N(a_val)}|" if a_val is not None else "|z| > |a|"
    return X.subs(a, a_val), roc

def transform_k_a_k(a_val):
    # Z{k a^k} = a z / (z - a)^2, ROC: |z| > |a|
    X = a*z/(z - a)**2
    roc = f"|z| > |{sp.N(a_val)}|" if a_val is not None else "|z| > |a|"
    return X.subs(a, a_val), roc

def transform_a_abs_k(a_val):
    # x(k) = a^{|k|} -> X(z) = z(1-a^2)/((z-a)(1-az)) or equivalent with 1/a form.
    # One common form (for two-sided) : X(z) = (z*(1-a**2))/((z-a)*(1-a*z))
    X = z*(1 - a**2)/((z - a)*(1 - a*z))
    roc = f"{abs(a_val)} < |z| < {1/abs(a_val)}" if a_val not in (None, 0) else "|a|<|z|<|1/a|"
    return X.subs(a, a_val), roc

def transform_C_a_k_plus_n(C_val, a_val, n_val):
    # x(k) = C * a^{k+n} for k >= 0 (causal) => C a^n * z/(z - a)
    X = C * a**n * z/(z - a)
    roc = f"|z| > |{sp.N(a_val)}|" if a_val is not None else "|z| > |a|"
    return X.subs({C: C_val, a: a_val, n: n_val}), roc

def transform_c_sin_alpha_beta(a_prefactor, alpha_val, beta_val):
    # x(k) = C * sin(alpha*k + beta) can be handled via ztransform of sin sequence:
    # Z{sin(alpha k + beta)} = z * (sin beta + sin(alpha + beta) * (a) ) / (z^2 - 2 z cos alpha + 1)
    # But usually sin sequence corresponds to combination of e^{j alpha k}. We'll use sympy ztransform.
    expr = (a_prefactor or 1) * sp.sin(alpha * k + beta)
    try:
        X = sp.ztransform(expr, k, z)
        roc = "ROC depends on form (usually |z| > 1 for causal sin sequences)"
        return X, roc
    except Exception:
        return None, "Could not compute symbolic transform."

def transform_c_sinh(alpha_val):
    # sinh(alpha k) = (e^{a k} - e^{-a k})/2 with a = alpha
    # Use ztransform on symbolic expression
    expr = sp.sinh(alpha * k)
    try:
        X = sp.ztransform(expr, k, z)
        roc = "ROC: |z| > e^{Re(alpha)} (causal form)"
        return X, roc
    except Exception:
        return None, "Could not compute symbolic transform."

def transform_c_cosh(alpha_val):
    expr = sp.cosh(alpha * k)
    try:
        X = sp.ztransform(expr, k, z)
        roc = "ROC: |z| > e^{Re(alpha)} (causal form)"
        return X, roc
    except Exception:
        return None, "Could not compute symbolic transform."

# ----------------- property helpers -----------------
def compute_ztransform_of_expr(expr_str):
    """Compute Z{expr(k)} symbolically using sympy.ztransform(expr, k, z)."""
    try:
        expr = safe_sympify(expr_str)
        X = sp.ztransform(expr, k, z)
        return X
    except Exception as e:
        raise

# ----------------- endpoint -----------------
@bp.route("/api/z_transform", methods=["POST"])
def api_z_transform():
    """
    Accepts JSON with structure:
    {
      "action": "definition" | "standard" | "property",
      "payload": { ... }
    }

    For action == "definition":
      payload: { "expr": "a**k" }  -- expression in variable k (use ** for power)
      returns: X(z), latex, ROC (best-effort)

    For action == "standard":
      payload: {
        "standard_type": "a_pow_k" | "k_a_pow_k" | "a_abs_k" | "C_a_k_plus_n" | "sin_alpha_beta" | "sinh" | "cosh",
        params...
      }

    For action == "property":
      payload: {
        "property": "scaling" | "shifting",
        "expr": "a**k" or supply "Xz" (optional),
        additional params: a (for scaling), n (for shifting)
      }
    """
    try:
        data = request.get_json(force=True)
        action = data.get("action")
        payload = data.get("payload", {}) or {}

        if action == "definition":
            expr_str = payload.get("expr")
            if not expr_str:
                return jsonify(success=False, message="Provide 'expr' in payload for definition.")
            try:
                X = compute_ztransform_of_expr(expr_str)
                latex_X = latex(X)
                steps = [f"Definition: Z{{x(k)}} = \\sum_{{k=-\\infty}}^\\infty x(k) z^{{-k}}",
                         f"Compute Z{{{expr_str}}} symbolically."]
                # ROC: sympy doesn't reliably give ROC; provide best-effort note
                roc = "ROC depends on the sequence; determine by convergence of the defining sum."
                return jsonify(success=True, result=latex_X, steps=steps, roc=roc)
            except Exception as e:
                return jsonify(success=False, message=f"Could not compute transform: {e}")

        elif action == "standard":
            stype = payload.get("standard_type")
            # normalize inputs
            a_val = payload.get("a")  # may be None
            C_val = payload.get("C")
            n_val = payload.get("n")
            alpha_val = payload.get("alpha")
            beta_val = payload.get("beta")

            if stype == "a_pow_k":
                X, roc = transform_a_pow_k(a_val)
                return jsonify(success=True, result=latex(X), steps=[latex(X)], roc=roc)

            if stype == "k_a_pow_k":
                X, roc = transform_k_a_k(a_val)
                return jsonify(success=True, result=latex(X), steps=[latex(X)], roc=roc)

            if stype == "a_abs_k":
                X, roc = transform_a_abs_k(a_val)
                return jsonify(success=True, result=latex(X), steps=[latex(X)], roc=roc)

            if stype == "C_a_k_plus_n":
                X, roc = transform_C_a_k_plus_n(C_val, a_val, n_val)
                return jsonify(success=True, result=latex(X), steps=[latex(X)], roc=roc)

            if stype == "sin_alpha_beta":
                # payload: alpha, beta, (C optional)
                Cp = C_val if C_val is not None else 1
                if alpha_val is None or beta_val is None:
                    return jsonify(success=False, message="Provide 'alpha' and 'beta' for sin_alpha_beta.")
                X, roc = transform_c_sin_alpha_beta(Cp, alpha_val, beta_val)
                if X is None:
                    return jsonify(success=False, message="Sympy couldn't compute transform for sin sequence.")
                return jsonify(success=True, result=latex(X), steps=[latex(X)], roc=roc)

            if stype == "sinh":
                if alpha_val is None:
                    return jsonify(success=False, message="Provide 'alpha' for sinh.")
                X, roc = transform_c_sinh(alpha_val)
                if X is None:
                    return jsonify(success=False, message="Sympy couldn't compute transform for sinh.")
                return jsonify(success=True, result=latex(X), steps=[latex(X)], roc=roc)

            if stype == "cosh":
                if alpha_val is None:
                    return jsonify(success=False, message="Provide 'alpha' for cosh.")
                X, roc = transform_c_cosh(alpha_val)
                if X is None:
                    return jsonify(success=False, message="Sympy couldn't compute transform for cosh.")
                return jsonify(success=True, result=latex(X), steps=[latex(X)], roc=roc)

            return jsonify(success=False, message="Unknown standard_type.")

        elif action == "property":
            prop = payload.get("property")
            expr_str = payload.get("expr")
            # either user gives expr in k or gives Xz (string) for transform
            if not expr_str:
                return jsonify(success=False, message="Provide 'expr' (sequence in k) for property checks.")

            # compute X(z)
            try:
                X = compute_ztransform_of_expr(expr_str)
            except Exception as e:
                return jsonify(success=False, message=f"Could not compute Z{{expr}}: {e}")

            if prop == "scaling":
                # scaling by 'a' means sequence a^k * x(k) => X(z/a)
                a_param = payload.get("a")
                if a_param is None:
                    return jsonify(success=False, message="Provide 'a' for scaling property.")
                # replace z by z/a in X
                X_scaled = sp.simplify(X.subs(z, z / sp.sympify(a_param)))
                steps = [
                    f"Let X(z) = {latex(X)}",
                    f"Z{{a^k x(k)}} = X(z/a) = {latex(X_scaled)}"
                ]
                return jsonify(success=True, result=latex(X_scaled), steps=steps, roc=f"ROC scaled by factor a (replace z with z/a)")

            elif prop == "shifting":
                # shifting: x(k-n) -> z^{-n} X(z) (causal shift). Need integer n
                n_param = payload.get("n")
                if n_param is None:
                    return jsonify(success=False, message="Provide integer 'n' for shifting property.")
                try:
                    n_int = int(n_param)
                except Exception:
                    return jsonify(success=False, message="'n' should be an integer.")
                X_shift = sp.simplify(z**(-n_int) * X)
                steps = [
                    f"Let X(z) = {latex(X)}",
                    f"Z{{x(k - {n_int})}} = z^{{-{n_int}}} X(z) = {latex(X_shift)}"
                ]
                return jsonify(success=True, result=latex(X_shift), steps=steps, roc="Same ROC as X(z) except possible adjustments from the shift")

            else:
                return jsonify(success=False, message="Unknown property type. Supported: scaling, shifting.")

        else:
            return jsonify(success=False, message="Unknown action. Use 'definition', 'standard', or 'property'.")

    except Exception as exc:
        return jsonify(success=False, message=f"Server error: {exc}")
