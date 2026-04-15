# laplace_solver.py — step-by-step Laplace Transform solver
from sympy import (
    symbols, sympify, simplify, expand, apart, latex,
    sin, cos, sinh, cosh, exp, Heaviside, Derivative, Integral, oo, I
)
from sympy.abc import t, s, a, b, c, k
from parse_math_input import parse_math_input
from pretty_laplace import pretty
from sympy.integrals.transforms import laplace_transform


# ----------------- Utilities -----------------
def _L(expr):
    """Convert sympy expression to LaTeX string."""
    return latex(expr)


def _num_step(n, body_latex):
    """Make a numbered step (LaTeX inline)."""
    return rf"\({n}.\ {body_latex}\)"


def _lin_parts(expr):
    """Split sum into parts for linearity."""
    return list(expr.as_ordered_terms()) if expr.is_Add else [expr]


def _const_and_core(p):
    """Split constant coefficient wrt t."""
    const, core = p.as_independent(t, as_Add=False)
    return const, core


# ----------------- Rule library -----------------
RULES = [
    {
        "name": "Power of t",
        "predicate": lambda core: core.is_Pow and core.base == t and core.exp.is_Integer and core.exp >= 0,
        "formula": r"\mathcal{L}\{t^{n}\}=\dfrac{n!}{s^{n+1}},\; \Re(s)>0",
        "note": lambda core: rf"Here, \(n={_L(core.exp)}\)."
    },
    {
        "name": "Exponential",
        "predicate": lambda core: core.func == exp and core.args[0].has(t),
        "formula": r"\mathcal{L}\{e^{a t}\}=\dfrac{1}{s-a},\; \Re(s)>\Re(a)",
        "note": lambda core: rf"a={_L(core.args[0].coeff(t))}."
    },
    {
        "name": "Sin",
        "predicate": lambda core: core.func == sin and core.args[0].has(t),
        "formula": r"\mathcal{L}\{\sin(\omega t)\}=\dfrac{\omega}{s^{2}+\omega^{2}}",
        "note": lambda core: rf"\(\omega={_L(core.args[0].coeff(t))}\)."
    },
    {
        "name": "Cos",
        "predicate": lambda core: core.func == cos and core.args[0].has(t),
        "formula": r"\mathcal{L}\{\cos(\omega t)\}=\dfrac{s}{s^{2}+\omega^{2}}",
        "note": lambda core: rf"\(\omega={_L(core.args[0].coeff(t))}\)."
    },
    {
        "name": "Sinh",
        "predicate": lambda core: core.func == sinh and core.args[0].has(t),
        "formula": r"\mathcal{L}\{\sinh(\omega t)\}=\dfrac{\omega}{s^{2}-\omega^{2}}",
        "note": lambda core: rf"\(\omega={_L(core.args[0].coeff(t))}\)."
    },
    {
        "name": "Cosh",
        "predicate": lambda core: core.func == cosh and core.args[0].has(t),
        "formula": r"\mathcal{L}\{\cosh(\omega t)\}=\dfrac{s}{s^{2}-\omega^{2}}",
        "note": lambda core: rf"\(\omega={_L(core.args[0].coeff(t))}\)."
    },
]


def _match_rule(core):
    """Return rule dict if one matches, else None."""
    for rule in RULES:
        try:
            if rule["predicate"](core):
                return rule
        except Exception:
            continue
    return None


# ----------------- Main solver -----------------
def solve_laplace(user_expr):
    steps = []
    step_no = 1

    try:
        # 1) Parse input
        parsed = parse_math_input(user_expr)
        context = {
            "t": t, "s": s, "a": a, "b": b, "c": c, "k": k,
            "sin": sin, "cos": cos, "sinh": sinh, "cosh": cosh,
            "exp": exp, "Heaviside": Heaviside, "Derivative": Derivative, "diff": Derivative, "Integral": Integral
        }
        f = sympify(parsed, locals=context)

        # Step: Given
        steps.append(_num_step(step_no, rf"Given: \(f(t)={_L(f)}\)"))
        step_no += 1

        # 2) Simplify
        f_simpl = simplify(f)
        if f_simpl != f:
            steps.append(_num_step(step_no, rf"Rewrite: \(f(t)={_L(f_simpl)}\)"))
            step_no += 1
            f = f_simpl

        # 3) Special cases
        # (a) Integral from 0 to t
        if isinstance(f, Integral) and len(f.limits) == 1:
            lim = f.limits[0]
            if lim[0] == t and lim[1] == 0 and lim[2] == t:
                steps.append(_num_step(step_no, r"Detected: \(\int_0^t g(\tau)d\tau\). Use: \(\dfrac{G(s)}{s}\)"))
                step_no += 1

        # (b) Derivatives
        if f.has(Derivative):
            steps.append(_num_step(step_no, r"Detected derivative. Use: \(\mathcal{L}\{f'(t)\}=sF(s)-f(0)\)"))
            step_no += 1
            f = f.doit()

        # (c) Division by t
        if f.is_Mul and any(arg == 1/t for arg in f.args):
            f_base = f / (1/t)
            steps.append(_num_step(step_no, r"Detected: \(f(t)/t\). Use: \(\int_s^\infty F(u)\,du\)"))
            step_no += 1

            F_base = laplace_transform(f_base, t, s, noconds=True)
            u = symbols('u')
            from sympy import integrate as sp_integrate
            result_exact = sp_integrate(F_base.subs(s, u), (u, s, oo))

            try:
                partial = apart(result_exact)
            except Exception:
                partial = result_exact

            # Build LaTeX safely
            latex_Fbase = _L(F_base).replace("s", "u")
            latex_result = _L(simplify(result_exact))
            latex_fbase = _L(f_base)

            step_expr = (
                r"\(\mathcal{L}\left\{\frac{" + latex_fbase +
                r"}{t}\right\}=\int_{s}^{\infty}" + latex_Fbase +
                r"~du=" + latex_result + r"\)"
            )
            steps.append(_num_step(step_no, step_expr))
            step_no += 1

            return {
                "input": user_expr,
                "expression": user_expr,
                "parsed": parsed,
                "steps": steps,
                "result": pretty(result_exact),
                "partial": pretty(partial),
                "input_latex": rf"\mathcal{{L}}\!\left[{_L(f)}\right]={latex_result}",
                "latex_partial": latex(partial)
            }

        # 4) Linearity split
        parts = _lin_parts(f)
        if len(parts) > 1:
            steps.append(_num_step(step_no, "By linearity, split into parts"))
            step_no += 1

        total = 0
        for idx, p in enumerate(parts, start=1):
            const, core = _const_and_core(simplify(p))
            steps.append(_num_step(step_no, rf"Part {idx}: \({_L(p)}\)"))
            step_no += 1

            # Rule check
            rule = _match_rule(core)
            if rule:
                steps.append(_num_step(step_no, f"Formula: {rule['formula']}"))
                step_no += 1
                if callable(rule.get("note")):
                    steps.append(_num_step(step_no, rule["note"](core)))
                    step_no += 1

            # Compute with SymPy
            Tf = laplace_transform(p, t, s, noconds=True)
            Tf_simpl = simplify(expand(Tf))
            if Tf_simpl.has(I):
                Tf_simpl = simplify(expand(Tf_simpl))

            steps.append(_num_step(step_no, rf"\(\mathcal{{L}}\{{{_L(p)}\}}={_L(Tf_simpl)}\)"))
            step_no += 1

            total += Tf_simpl

        total_simpl = simplify(expand(total))
        steps.append(_num_step(step_no, rf"Combine: \(F(s)={_L(total_simpl)}\)"))
        step_no += 1

        try:
            partial = apart(total_simpl)
        except Exception:
            partial = total_simpl

        return {
            "input": user_expr,
            "expression": user_expr,
            "parsed": parsed,
            "steps": steps,
            "result": pretty(total_simpl),
            "partial": pretty(partial),
            "input_latex": rf"\mathcal{{L}}\!\left[{_L(f)}\right]={_L(total_simpl)}",
            "latex_partial": latex(partial)
        }

    except Exception as e:
        return {"error": str(e)}
