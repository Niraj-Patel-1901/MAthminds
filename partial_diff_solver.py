# partial_diff_solver.py
import sympy as sp
import re
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application
)

transformations = standard_transformations + (implicit_multiplication_application,)

ALLOWED_FUNCS = {
    'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan, 'exp': sp.exp, 'log': sp.log,
    'sqrt': sp.sqrt, 'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
    'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh, 'Abs': sp.Abs,
    'pi': sp.pi, 'E': sp.E, 'e': sp.E
}

def _identifiers_from(s):
    return set(re.findall(r"[A-Za-z_]\w*", s))

def safe_parse(expr_str):
    s = expr_str.replace('^', '**')
    idents = _identifiers_from(s)
    vars_only = sorted(list(idents - set(ALLOWED_FUNCS.keys())))
    local = {v: sp.symbols(v) for v in vars_only}
    local.update(ALLOWED_FUNCS)
    return parse_expr(s, local_dict=local, transformations=transformations)

def latexify(expr):
    return sp.latex(sp.simplify(expr))

def numeric_round(val):
    if isinstance(val, (int, sp.Integer)):
        return int(val)
    if isinstance(val, sp.Float) or isinstance(val, float):
        return float(round(float(val), 3))
    try:
        return float(round(float(val), 3))
    except Exception:
        return val

def solve_partial_diff(payload):
    mode = payload.get('mode')
    if not mode:
        raise ValueError("Missing 'mode'")
    func_str = payload.get('function')
    if not func_str:
        raise ValueError("Missing 'function'")

    f_expr = safe_parse(func_str)
    steps = []
    table = None
    result_latex = ""

    eval_at = payload.get('evaluate_at', None)
    def maybe_eval(expr):
        if not eval_at:
            return None
        try:
            subs_map = {sp.symbols(k): float(v) for k, v in eval_at.items()}
            return numeric_round(sp.N(expr.subs(subs_map)))
        except Exception:
            return None

    if mode == 'first':
        varname = payload.get('var', 'x')
        var = sp.symbols(varname)
        steps.append(f"1. $$f = {latexify(f_expr)}$$")
        deriv = sp.diff(f_expr, var)
        steps.append(f"2. $$\\frac{{\\partial f}}{{\\partial {varname}}} = {latexify(deriv)}$$")
        steps.append(f"3. Final: $${latexify(deriv)}$$")
        result_latex = latexify(deriv)
        numeric = maybe_eval(deriv)
        if numeric is not None:
            steps.append(f"4. Numeric evaluation at {eval_at}: ${numeric}$")

    elif mode == 'higher':
        seq = payload.get('sequence', [])
        steps.append(f"1. $$f = {latexify(f_expr)}$$")
        cur = f_expr
        table = {"headers": ["Step", "Operation", "Expression"], "rows": []}
        for i, v in enumerate(seq):
            sym = sp.symbols(v)
            cur = sp.diff(cur, sym)
            cur_s = sp.simplify(cur)
            steps.append(f"{i+2}. $$\\frac{{\\partial}}{{\\partial {v}}} = {latexify(cur_s)}$$")
            table["rows"].append([str(i+1), f"d/d{v}", latexify(cur_s)])
        result_latex = latexify(cur)

    elif mode == 'composite':
        subs = payload.get('subs', {})
        wrt = payload.get('wrt', 'x')
        outer_vars = list(subs.keys())
        local_outer = {name: sp.symbols(name) for name in outer_vars}
        local_outer.update(ALLOWED_FUNCS)
        f_outer = parse_expr(func_str.replace('^','**'), local_dict=local_outer,
                             transformations=transformations)
        steps.append(f"1. Outer function: $$f( {', '.join(outer_vars)} ) = {sp.latex(f_outer)}$$")
        partials = {name: sp.diff(f_outer, local_outer[name]) for name in outer_vars}
        for name, p in partials.items():
            steps.append(f"2. $$\\frac{{\\partial f}}{{\\partial {name}}} = {sp.latex(sp.simplify(p))}$$")
        subs_expr = {k: safe_parse(v) for k,v in subs.items()}
        wrt_sym = sp.symbols(wrt)
        inner_derivs = {k: sp.diff(subs_expr[k], wrt_sym) for k in subs_expr}
        for k, d in inner_derivs.items():
            steps.append(f"3. $$\\frac{{\\partial {k}}}{{\\partial {wrt}}} = {sp.latex(sp.simplify(d))}$$")
        total = sum(partials[k].subs({sp.symbols(k): subs_expr[k]}) * inner_derivs[k] for k in outer_vars)
        total = sp.simplify(total)
        steps.append(f"4. Chain rule final: $$\\frac{{\\partial f}}{{\\partial {wrt}}} = {sp.latex(total)}$$")
        result_latex = sp.latex(total)

    elif mode == 'euler':
        # Assume 2 variables: x, y (you can extend for z if needed)
        x, y = sp.symbols('x y')
        steps.append(r"Euler's Theorem: \(x f_x + y f_y = n f\) for homogeneous \(f\)")

        # Step 1: First partial derivatives
        fx = sp.diff(f_expr, x)
        fy = sp.diff(f_expr, y)
        steps.append(f"First partial derivatives: $$f_x = {latexify(fx)},\\ f_y = {latexify(fy)}$$")

        # Step 2: LHS calculation
        LHS = sp.simplify(x * fx + y * fy)
        steps.append(f"LHS: $$x f_x + y f_y = {latexify(LHS)}$$")

        # Step 3: Detect degree of homogeneity n
        t = sp.symbols('t')
        scaled_expr = f_expr.subs({x: t*x, y: t*y})
        try:
            ratio = sp.simplify(scaled_expr / f_expr)
            if ratio.is_Pow and ratio.base == t:
                n_detected = ratio.exp
            elif ratio == t:
                n_detected = 1
            else:
                n_detected = None
        except Exception:
            n_detected = None

        if n_detected is not None:
            steps.append(f"Detected degree of homogeneity: $$n = {latexify(n_detected)}$$")
            RHS = sp.simplify(n_detected * f_expr)
            steps.append(f"RHS: $$n f = {latexify(RHS)}$$")

            # Step 4: Verification
            if sp.simplify(LHS - RHS) == 0:
                steps.append(r"\(\text{Since LHS = RHS, Euler's theorem is VERIFIED.}\)")
            else:
                steps.append(r"\(\text{LHS ≠ RHS, Euler's theorem is NOT satisfied.}\)")
        else:
            steps.append("Could not automatically detect degree \(n\). Please check function.")

        result_latex = latexify(LHS)

    else:
        raise ValueError("Unknown mode")

    res = {"type": "partial_diff", "result": result_latex, "steps": steps}
    if table:
        res["table"] = table
    return res
