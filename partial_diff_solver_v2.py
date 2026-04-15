# partial_diff_solver_v2.py
"""
Enhanced partial-differentiation solver for MathMinds.

Provides modes:
 - first
 - higher
 - composite        (outer function + subs -> chain rule)
 - multi_chain      (general chain rule with any number of inner vars)
 - total_diff       (total derivative w.r.t. a parameter t)
 - variable_transform (coordinate transforms, compute partials w.r.t new coords)
 - euler            (auto-detect 2/3 var, detect degree n, verify)

Returns a dict:
{
  "type": "partial_diff",
  "result": "<LaTeX result>",
  "steps": ["Step 1 ...", "Step 2 ..."],
  "table": { "headers": [...], "rows": [...] }  # only if needed
}
"""

import re
import sympy as sp
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


def _identifiers_from(s: str):
    return set(re.findall(r"[A-Za-z_]\w*", s))


def safe_parse(expr_str: str):
    """Parse with implicit multiplication, ^ -> **, and create symbols for identifiers."""
    s = expr_str.replace('^', '**')
    idents = _identifiers_from(s)
    # treat allowed names as functions/constants, rest as symbols
    vars_only = sorted(list(idents - set(ALLOWED_FUNCS.keys())))
    local = {}
    for v in vars_only:
        # create sympy Symbol for each identifier (don't overwrite function names)
        local[v] = sp.symbols(v)
    local.update(ALLOWED_FUNCS)
    return parse_expr(s, local_dict=local, transformations=transformations)


def latexify(expr):
    try:
        return sp.latex(sp.simplify(expr))
    except Exception:
        return sp.latex(expr)


def numeric_round(val):
    if isinstance(val, (int, sp.Integer)):
        return int(val)
    if isinstance(val, (float, sp.Float)):
        return float(round(float(val), 3))
    try:
        f = float(val)
        return float(round(f, 3))
    except Exception:
        return val


def _maybe_eval(expr, eval_at):
    """Evaluate expr at mapping eval_at (dict of var: value)."""
    if not eval_at:
        return None
    try:
        subs_map = {}
        for k, v in eval_at.items():
            subs_map[sp.symbols(k)] = float(v)
        val = sp.N(expr.subs(subs_map))
        return numeric_round(val)
    except Exception:
        return None


def _detect_degree_homogeneous(f_expr, vars_symbols):
    """Try to detect n such that f(t*x1, t*x2, ...) = t^n f(x1,x2,...).
       Returns (n, ratio_expr) where n is sympy expression or None.
    """
    t = sp.symbols('t')
    subs_map = {v: t * v for v in vars_symbols}
    try:
        scaled = sp.simplify(f_expr.subs(subs_map))
        ratio = sp.simplify(scaled / f_expr)
        # If ratio is t**n
        if ratio.is_Pow and ratio.base == t:
            return ratio.exp, ratio
        # If ratio is a power, maybe ratio = t
        if ratio == t:
            return sp.Integer(1), ratio
        # Try log trick: n = log(ratio)/log(t)
        n_try = sp.simplify(sp.log(ratio) / sp.log(t))
        # Accept if n_try does not depend on original vars
        orig_syms = set(f_expr.free_symbols)
        if isinstance(n_try, sp.Expr):
            free = set(n_try.free_symbols)
            if free.issubset({t}) or len(free) == 0:
                # evaluate at t=1 to get numeric? keep symbolic
                return sp.simplify(n_try), ratio
        return None, ratio
    except Exception:
        return None, None


def solve_partial_diff(payload: dict):
    """
    Main solver entry. Expects payload dict with keys:
      - mode (required)
      - function (required)
    Mode-specific keys documented in earlier messages.
    """
    mode = payload.get('mode')
    if not mode:
        raise ValueError("Missing 'mode' in payload")
    func_str = payload.get('function')
    if not func_str:
        raise ValueError("Missing 'function' in payload")

    # parse main expression
    f_expr = safe_parse(func_str)
    steps = []
    table = None
    result_latex = ""
    eval_at = payload.get('evaluate_at', None)

    # Helper for latex of symbol or value (keeps things readable)
    def L(x):
        return latexify(x)

    # --------- FIRST ORDER ----------
    if mode == 'first':
        varname = payload.get('var', 'x')
        var = sp.symbols(varname)
        steps.append(f"1. $$f = {L(f_expr)}$$")
        deriv = sp.diff(f_expr, var)
        deriv_s = sp.simplify(deriv)
        steps.append(f"2. $$\\frac{{\\partial f}}{{\\partial {varname}}} = {L(deriv_s)}$$")
        result_latex = L(deriv_s)
        numeric = _maybe_eval(deriv_s, eval_at)
        if numeric is not None:
            steps.append(f"3. Numeric evaluation at {eval_at}: ${numeric}$")

    # --------- HIGHER ORDER ----------
    elif mode == 'higher':
        seq = payload.get('sequence', [])
        if not seq:
            raise ValueError("'sequence' list required for mode 'higher'")
        steps.append(f"1. $$f = {L(f_expr)}$$")
        cur = f_expr
        table = {"headers": ["Step", "Operation", "Expression"], "rows": []}
        for i, v in enumerate(seq):
            sym = sp.symbols(v)
            cur = sp.diff(cur, sym)
            cur_s = sp.simplify(cur)
            steps.append(f"{i+2}. $$\\frac{{\\partial}}{{\\partial {v}}} = {L(cur_s)}$$")
            table["rows"].append([str(i+1), f"d/d{v}", L(cur_s)])
        result_latex = L(cur)

    # --------- COMPOSITE (outer function with subs mapping) ----------
    elif mode == 'composite':
        subs = payload.get('subs', {})
        wrt = payload.get('wrt', 'x')
        if not subs:
            raise ValueError("'subs' mapping required for mode 'composite'")
        outer_vars = list(subs.keys())
        local_outer = {name: sp.symbols(name) for name in outer_vars}
        local_outer.update(ALLOWED_FUNCS)
        f_outer = parse_expr(func_str.replace('^', '**'), local_dict=local_outer,
                             transformations=transformations)
        steps.append(f"1. Outer function: $$f({', '.join(outer_vars)}) = {sp.latex(f_outer)}$$")
        partials = {name: sp.diff(f_outer, local_outer[name]) for name in outer_vars}
        for name, p in partials.items():
            steps.append(f"2. $$\\frac{{\\partial f}}{{\\partial {name}}} = {sp.latex(sp.simplify(p))}$$")
        subs_expr = {k: safe_parse(v) for k, v in subs.items()}
        for k, v in subs_expr.items():
            steps.append(f" - substitution: $${k} = {L(v)}$$")
        wrt_sym = sp.symbols(wrt)
        inner_derivs = {k: sp.diff(subs_expr[k], wrt_sym) for k in subs_expr}
        for k, d in inner_derivs.items():
            steps.append(f"3. $$\\frac{{\\partial {k}}}{{\\partial {wrt}}} = {L(sp.simplify(d))}$$")
        total = sp.Integer(0)
        for k in outer_vars:
            total += partials[k].subs({sp.symbols(k): subs_expr[k]}) * inner_derivs[k]
        total = sp.simplify(total)
        steps.append(f"4. Chain rule: $$\\frac{{\\partial f}}{{\\partial {wrt}}} = {sp.latex(total)}$$")
        result_latex = sp.latex(total)
        numeric = _maybe_eval(total, eval_at)
        if numeric is not None:
            steps.append(f"5. Numeric evaluation at {eval_at}: ${numeric}$")

    # --------- MULTI_CHAIN (general chain rule for many inner vars) ----------
    elif mode == 'multi_chain':
        # payload.subs: mapping outer_var -> expression (in original base vars)
        # payload.wrt: the variable to differentiate with respect to (e.g., 'x' or 't')
        subs = payload.get('subs', {})
        wrt = payload.get('wrt', None)
        if not subs or not wrt:
            raise ValueError("'subs' mapping and 'wrt' required for mode 'multi_chain'")
        outer_vars = list(subs.keys())
        local_outer = {name: sp.symbols(name) for name in outer_vars}
        local_outer.update(ALLOWED_FUNCS)
        f_outer = parse_expr(func_str.replace('^', '**'), local_dict=local_outer,
                             transformations=transformations)
        steps.append(f"1. Outer function: $$f({', '.join(outer_vars)}) = {sp.latex(f_outer)}$$")
        # partials wrt outer variables
        partials = {name: sp.diff(f_outer, local_outer[name]) for name in outer_vars}
        for name, p in partials.items():
            steps.append(f"2. $$\\frac{{\\partial f}}{{\\partial {name}}} = {sp.latex(sp.simplify(p))}$$")
        # parse inner expressions
        subs_expr = {k: safe_parse(v) for k, v in subs.items()}
        for k, v in subs_expr.items():
            steps.append(f" - substitution: $${k} = {L(v)}$$")
        # compute derivative of each inner var wrt 'wrt'
        wrt_sym = sp.symbols(wrt)
        inner_derivs = {k: sp.simplify(sp.diff(subs_expr[k], wrt_sym)) for k in subs_expr}
        for k, d in inner_derivs.items():
            steps.append(f"3. $$\\frac{{\\partial {k}}}{{\\partial {wrt}}} = {L(d)}$$")
        # sum
        total = sp.Integer(0)
        for k in outer_vars:
            total += partials[k].subs({sp.symbols(k): subs_expr[k]}) * inner_derivs[k]
        total = sp.simplify(total)
        steps.append(f"4. Chain rule final: $$\\frac{{\\partial f}}{{\\partial {wrt}}} = {sp.latex(total)}$$")
        result_latex = sp.latex(total)
        numeric = _maybe_eval(total, eval_at)
        if numeric is not None:
            steps.append(f"5. Numeric evaluation at {eval_at}: ${numeric}$")

    # --------- TOTAL DIFFERENTIAL (w.r.t parameter t) ----------
    elif mode == 'total_diff':
        # payload.function : u(x,y,...) string
        # payload.param_subs: mapping variable -> expression in t (e.g., {"x":"cos(t)","y":"t**2"})
        # payload.param : parameter name, default 't'
        param_subs = payload.get('param_subs', {})
        param = payload.get('param', 't')
        if not param_subs:
            raise ValueError("'param_subs' mapping required for mode 'total_diff'")
        # parse original function variables
        vars_in_func = sorted([str(s) for s in f_expr.free_symbols])
        # create symbol objects
        vars_symbols = [sp.symbols(v) for v in vars_in_func]
        steps.append(f"1. $$u({', '.join(vars_in_func)}) = {L(f_expr)}$$")
        # partial derivatives
        partials = {str(v): sp.diff(f_expr, v) for v in vars_symbols}
        for name, p in partials.items():
            steps.append(f"2. $$\\frac{{\\partial u}}{{\\partial {name}}} = {L(sp.simplify(p))}$$")
        # parse substitutions x(t), y(t), ...
        subs_expr = {}
        for var, expr_str in param_subs.items():
            subs_expr[var] = safe_parse(expr_str)
            steps.append(f" - substitution: $${var} = {L(subs_expr[var])}$$")
        # compute derivatives dx/dt etc
        t_sym = sp.symbols(param)
        dparam = {}
        for var, expr in subs_expr.items():
            dparam[var] = sp.simplify(sp.diff(expr, t_sym))
            steps.append(f"3. $$\\frac{{d {var}}}{{d {param}}} = {L(dparam[var])}$$")
        # total derivative
        total = sp.Integer(0)
        for var in partials:
            if var in subs_expr:
                total += partials[var].subs({sp.symbols(var): subs_expr[var]}) * dparam[var]
            else:
                # if some variable in u wasn't provided in subs, we still include symbolic derivative * d(var)/dt
                dv = sp.symbols(f"d{var}_dt")  # placeholder
                total += partials[var] * dv
        total = sp.simplify(total)
        steps.append(f"4. Total derivative: $$\\frac{{du}}{{d{param}}} = {sp.latex(total)}$$")
        result_latex = sp.latex(total)
        numeric = _maybe_eval(total, eval_at)
        if numeric is not None:
            steps.append(f"5. Numeric evaluation at {eval_at}: ${numeric}$")

    # --------- VARIABLE TRANSFORM (coordinate transforms) ----------
    elif mode == 'variable_transform':
        # payload.transform: mapping old_var -> expression in new coords.
        # payload.new_coords: list of new coordinate symbols (e.g., ["r","theta"])
        # Example: transform = {"x":"r*cos(theta)","y":"r*sin(theta)"}; function is in x,y.
        transform = payload.get('transform', {})
        new_coords = payload.get('new_coords', [])
        if not transform or not new_coords:
            raise ValueError("'transform' mapping and 'new_coords' list required for mode 'variable_transform'")
        # parse transforms
        trans_expr = {k: safe_parse(v) for k, v in transform.items()}
        steps.append(f"1. Original function: $$f({', '.join([str(s) for s in f_expr.free_symbols])}) = {L(f_expr)}$$")
        for k, v in trans_expr.items():
            steps.append(f" - transform: $${k} = {L(v)}$$")
        # compute partial derivatives of original f wrt old vars
        old_vars = sorted([str(s) for s in f_expr.free_symbols])
        old_syms = [sp.symbols(v) for v in old_vars]
        partials = {v: sp.diff(f_expr, sp.symbols(v)) for v in old_vars}
        for v, p in partials.items():
            steps.append(f"2. $$\\frac{{\\partial f}}{{\\partial {v}}} = {L(sp.simplify(p))}$$")
        # For each new coord, compute df/d(new) = sum old_partial * d(old)/d(new)
        results = {}
        for nc in new_coords:
            nc_sym = sp.symbols(nc)
            df_dnc = sp.Integer(0)
            for old in old_vars:
                old_sym = sp.symbols(old)
                # derivative of old variable expression wrt new coord
                if old in trans_expr:
                    d_old_d_new = sp.simplify(sp.diff(trans_expr[old], nc_sym))
                    df_dnc += partials[old].subs({old_sym: trans_expr[old]}) * d_old_d_new
            df_dnc = sp.simplify(df_dnc)
            steps.append(f"3. $$\\frac{{\\partial f}}{{\\partial {nc}}} = {sp.latex(df_dnc)}$$")
            results[nc] = df_dnc
        # If a single new coord requested, return that; else return a dict in result
        if len(new_coords) == 1:
            result_latex = sp.latex(results[new_coords[0]])
        else:
            # represent as a small table
            table = {"headers": ["New Coord", "∂f/∂(coord)"], "rows": []}
            for nc in new_coords:
                table["rows"].append([nc, sp.latex(results[nc])])
            result_latex = ""  # primary result left blank; frontend can read table
    # --------- EULER'S THEOREM (auto-detect 2/3 vars) ----------
    elif mode == 'euler':
        # Determine number of variables from f_expr.free_symbols
        free_syms = list(f_expr.free_symbols)
        if not free_syms:
            raise ValueError("Function has no symbols for Euler's theorem")
        # Sort by name to have consistent ordering (x,y,z)
        free_names = sorted([str(s) for s in free_syms])
        # Limit to 2 or 3 variables; if more, consider first 3
        if len(free_names) >= 3:
            var_names = free_names[:3]
        else:
            var_names = free_names[:2]
        vars_symbols = [sp.symbols(n) for n in var_names]
        steps.append(r"Euler's Theorem: If \(f\) is homogeneous of degree \(n\), then \(\sum_i x_i f_{x_i} = n f\).")
        # compute partials
        partials = {str(v): sp.diff(f_expr, v) for v in vars_symbols}
        parts = ", ".join([f"$f_{{{n}}} = {L(partials[n] if isinstance(n, str) else partials[str(n)])}$" for n in [str(v) for v in vars_symbols]])
        # More explicit:
        fx_list = [f"$f_{{{name}}} = {L(partials[name])}$" for name in [str(v) for v in vars_symbols]]
        steps.append("First partial derivatives: " + ",\\; ".join(fx_list))
        # LHS
        LHS = sp.Integer(0)
        for name in [str(v) for v in vars_symbols]:
            sym = sp.symbols(name)
            LHS += sym * partials[name]
        LHS = sp.simplify(LHS)
        steps.append(f"LHS: $$\\sum {', '.join([name + ' ' for name in [str(v) for v in vars_symbols]])} f_{{\\cdot}} = {L(LHS)}$$")
        # detect degree
        n_detected, ratio = _detect_degree_homogeneous(f_expr, vars_symbols)
        if n_detected is not None:
            steps.append(f"Detected degree of homogeneity: $$n = {L(n_detected)}$$")
            RHS = sp.simplify(n_detected * f_expr)
            steps.append(f"RHS: $$n f = {L(RHS)}$$")
            diff_check = sp.simplify(LHS - RHS)
            steps.append(f"Check: $$x f_x + y f_y \\dots - n f = {L(diff_check)}$$")
            if sp.simplify(diff_check) == 0:
                steps.append(r"\(\text{Since LHS = RHS, Euler's theorem is VERIFIED for this function.}\)")
            else:
                steps.append(r"\(\text{LHS ≠ RHS, Euler's theorem is NOT satisfied for this function.}\)")
        else:
            steps.append("Could not automatically detect a single degree of homogeneity 'n' for this function.")
            if ratio is not None:
                steps.append(f"Scaled ratio found: $${sp.latex(ratio)}$$")
        result_latex = L(LHS)

    else:
        raise ValueError(f"Unknown mode '{mode}'")

    # Build response
    res = {"type": "partial_diff", "result": result_latex, "steps": steps}
    if table:
        res["table"] = table
    return res
