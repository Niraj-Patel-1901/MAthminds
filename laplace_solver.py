# laplace_solver.py — detailed step-by-step Laplace Transform solver
from sympy import (
    symbols, sympify, simplify, expand, apart, latex,
    sin, cos, sinh, cosh, exp, Heaviside, Derivative, Integral, oo, I, diff, integrate
)
from sympy.abc import t, s, a, b, c, k
from parse_math_input import parse_math_input
from pretty_laplace import pretty

# ----------------- Utilities -----------------
def _L(expr):
    """Convert sympy expression to LaTeX string."""
    return latex(expr)

def _num_step(n, title, body_latex=""):
    """Make a formatted step using HTML bold."""
    if body_latex:
        return f"{n}. <strong>{title}</strong>: \\({body_latex}\\)"
    return f"{n}. <strong>{title}</strong>"

# ----------------- Property Handlers -----------------

def _handle_trig_identities(expr, steps, step_no):
    """Detect and apply trig identities to linearize products/powers."""
    # Handle sin^2(at), cos^2(at)
    if expr.is_Pow and expr.exp == 2:
        base = expr.base
        if base.func == sin:
            arg = base.args[0]
            new_expr = (1 - cos(2*arg))/2
            steps.append(_num_step(step_no, "Trig Identity", rf"\sin^2({_L(arg)}) = \frac{{1 - \cos(2 \cdot {_L(arg)})}}{{2}}"))
            return new_expr, step_no + 1
        if base.func == cos:
            arg = base.args[0]
            new_expr = (1 + cos(2*arg))/2
            steps.append(_num_step(step_no, "Trig Identity", rf"\cos^2({_L(arg)}) = \frac{{1 + \cos(2 \cdot {_L(arg)})}}{{2}}"))
            return new_expr, step_no + 1
            
    # Handle sin(at)cos(bt) etc. (via expand_trig)
    # Sympy's expand(trig=True) or manual check
    return expr, step_no

def _handle_first_shifting(expr, steps, step_no):
    """Detect e^{at} * f(t) -> F(s-a)."""
    if expr.is_Mul:
        exp_terms = [arg for arg in expr.args if arg.func == exp and arg.args[0].has(t)]
        if exp_terms:
            e_at = exp_terms[0]
            at = e_at.args[0]
            a_val = at.coeff(t)
            remaining = simplify(expr / e_at)
            
            steps.append(_num_step(step_no, "First Shifting Theorem", 
                rf"\mathcal{{L}}\{{e^{{at}} f(t)\}} = F(s-a) \text{{ where }} a = {_L(a_val)}"))
            step_no += 1
            
            # Recursive call for remaining
            res_s, step_no = _solve_recursive(remaining, steps, step_no)
            
            final_res = res_s.subs(s, s - a_val)
            steps.append(_num_step(step_no, "Apply Shift", rf"F(s - {_L(a_val)}) = {_L(final_res)}"))
            return final_res, step_no + 1
            
    return None, step_no

def _handle_mult_by_t(expr, steps, step_no):
    """Detect t^n * f(t) -> (-1)^n * d^n/ds^n F(s)."""
    if expr.is_Mul:
        t_terms = [arg for arg in expr.args if (arg == t) or (arg.is_Pow and arg.base == t and arg.exp.is_Integer and arg.exp > 0)]
        if t_terms:
            t_pow = t_terms[0]
            n = t_pow.exp if t_pow.is_Pow else 1
            remaining = simplify(expr / t_pow)
            
            steps.append(_num_step(step_no, "Differentiation in s-domain", 
                rf"\mathcal{{L}}\{{t^{{{_L(n)}}} f(t)\}} = (-1)^{{{_L(n)}}} \frac{{d^{{{_L(n)}}}}}{{ds^{{{_L(n)}}}}} F(s)"))
            step_no += 1
            
            # Recursive call for remaining
            res_s, step_no = _solve_recursive(remaining, steps, step_no)
            
            final_res = ((-1)**n * diff(res_s, s, n)).expand()
            steps.append(_num_step(step_no, "Differentiate", rf"(-1)^{{{_L(n)}}} \frac{{d^{{{_L(n)}}}}}{{ds^{{{_L(n)}}}}} ({_L(res_s)}) = {_L(final_res)}"))
            return final_res, step_no + 1
            
    return None, step_no

def _handle_div_by_t(expr, steps, step_no):
    """Detect f(t)/t -> integral from s to inf."""
    if expr.is_Mul:
        div_t = [arg for arg in expr.args if arg == 1/t]
        if div_t:
            remaining = simplify(expr * t)
            steps.append(_num_step(step_no, "Division by t Property", 
                rf"\mathcal{{L}}\{{\frac{{f(t)}}{{t}}\}} = \int_{{s}}^{{\infty}} F(u) du"))
            step_no += 1
            
            # Recursive call
            res_s, step_no = _solve_recursive(remaining, steps, step_no)
            
            u = symbols('u')
            integrand = res_s.subs(s, u)
            final_res = integrate(integrand, (u, s, oo))
            
            steps.append(_num_step(step_no, "Integrate", rf"\int_{{s}}^{{\infty}} {_L(integrand)} du = {_L(final_res)}"))
            return final_res, step_no + 1
            
    return None, step_no

# ----------------- Basic Rules -----------------
RULES = [
    {"name": "Constant", "pred": lambda e: e.is_Number or (not e.has(t)), "formula": r"\mathcal{L}\{k\} = \frac{k}{s}", "apply": lambda e: e/s},
    {"name": "Power of t", "pred": lambda e: e.is_Pow and e.base == t and e.exp.is_Integer and e.exp >= 0, "formula": r"\mathcal{L}\{t^n\} = \frac{n!}{s^{n+1}}", "apply": lambda e: sympify(f"factorial({e.exp})") / (s**(e.exp+1))},
    {"name": "Simple t", "pred": lambda e: e == t, "formula": r"\mathcal{L}\{t\} = \frac{1}{s^2}", "apply": lambda e: 1/(s**2)},
    {"name": "Exponential", "pred": lambda e: e.func == exp, "formula": r"\mathcal{L}\{e^{at}\} = \frac{1}{s-a}", "apply": lambda e: 1/(s - e.args[0].coeff(t))},
    {"name": "Sin", "pred": lambda e: e.func == sin, "formula": r"\mathcal{L}\{\sin(\omega t)\} = \frac{\omega}{s^2 + \omega^2}", "apply": lambda e: e.args[0].coeff(t) / (s**2 + (e.args[0].coeff(t))**2)},
    {"name": "Cos", "pred": lambda e: e.func == cos, "formula": r"\mathcal{L}\{\cos(\omega t)\} = \frac{s}{s^2 + \omega^2}", "apply": lambda e: s / (s**2 + (e.args[0].coeff(t))**2)},
    {"name": "Sinh", "pred": lambda e: e.func == sinh, "formula": r"\mathcal{L}\{\sinh(at)\} = \frac{a}{s^2 - a^2}", "apply": lambda e: e.args[0].coeff(t) / (s**2 - (e.args[0].coeff(t))**2)},
    {"name": "Cosh", "pred": lambda e: e.func == cosh, "formula": r"\mathcal{L}\{\cosh(at)\} = \frac{s}{s^2 - a^2}", "apply": lambda e: s / (s**2 - (e.args[0].coeff(t))**2)},
]

def _solve_recursive(expr, steps, step_no):
    """Core recursive solver."""
    # expr = simplify(expr)  <-- Removed to prevent infinite loops with trig identities
    
    # 1. Linearity check (Sum)
    if expr.is_Add:
        steps.append(_num_step(step_no, "Linearity", rf"\text{{Split sum: }} {_L(expr)}"))
        step_no += 1
        terms = expr.as_ordered_terms()
        total_s = 0
        for term in terms:
            res_s, step_no = _solve_recursive(term, steps, step_no)
            total_s += res_s
        return total_s, step_no

    # 2. Pull out constants
    const, core = expr.as_independent(t, as_Add=False)
    if const != 1:
        steps.append(_num_step(step_no, "Constant Multiple", rf"\text{{Pull out }} {_L(const)}: \mathcal{{L}}\{{{_L(expr)}\}} = {_L(const)} \cdot \mathcal{{L}}\{{{_L(core)}\}}"))
        step_no += 1
        res_s, step_no = _solve_recursive(core, steps, step_no)
        return const * res_s, step_no

    # 3. Property detectors
    # (a) First Shifting
    res, next_no = _handle_first_shifting(expr, steps, step_no)
    if res is not None: return res, next_no

    # (b) Multiplication by t
    res, next_no = _handle_mult_by_t(expr, steps, step_no)
    if res is not None: return res, next_no
    
    # (c) Division by t
    res, next_no = _handle_div_by_t(expr, steps, step_no)
    if res is not None: return res, next_no

    # (d) Trig Identities
    new_expr, next_no = _handle_trig_identities(expr, steps, step_no)
    if new_expr != expr:
        return _solve_recursive(new_expr, steps, next_no)

    # 4. Basic Rules
    for rule in RULES:
        if rule["pred"](expr):
            res_s = rule["apply"](expr)
            steps.append(_num_step(step_no, f"Standard Formula ({rule['name']})", 
                rf"{rule['formula']} \implies \mathcal{{L}}\{{{_L(expr)}\}} = {_L(res_s)}"))
            return res_s, step_no + 1

    # Fallback to general transform
    from sympy.integrals.transforms import laplace_transform
    res_s = laplace_transform(expr, t, s, noconds=True)
    steps.append(_num_step(step_no, "General Transform", rf"\mathcal{{L}}\{{{_L(expr)}\}} = {_L(res_s)}"))
    return res_s, step_no + 1

# ----------------- Main solver -----------------
def solve_laplace(user_expr):
    steps = []
    try:
        parsed = parse_math_input(user_expr)
        f = sympify(parsed, locals={"t": t, "s": s, "exp": exp, "sin": sin, "cos": cos, "sinh": sinh, "cosh": cosh})
        
        steps.append(_num_step(1, "Input Function", rf"f(t) = {_L(f)}"))
        
        # Start recursion
        final_s, _ = _solve_recursive(f, steps, 2)
        
        final_res = simplify(final_s)
        try:
            partial = apart(final_res, s)
        except:
            partial = final_res

        return {
            "input": user_expr,
            "steps": steps,
            "result": pretty(final_res),
            "partial": pretty(partial),
            "input_latex": rf"\mathcal{{L}}\{{{_L(f)}\}} = {_L(final_res)}",
            "latex_partial": _L(partial)
        }
    except Exception as e:
        return {"error": str(e)}

