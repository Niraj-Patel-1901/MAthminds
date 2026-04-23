# inverse_laplace.py — step-by-step Inverse Laplace (uniform with Laplace module)

from sympy import (
    symbols, inverse_laplace_transform, apart, latex, simplify, Poly, factor,
    exp, sin, cos, Heaviside, sqrt
)
from sympy.abc import s, t
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor
)

t, s = symbols('t s', real=True)
transformations = (
    standard_transformations
    + (implicit_multiplication_application, convert_xor)
)

def _L(x):
    return latex(x)

def _add_step(steps, n, title, expr_latex):
    """Append a numbered step with a LaTeX expression (or '' if none)."""
    steps.append({"step": f"{n}. {title}", "expr": expr_latex})
    return n + 1

def _as_parts(expr):
    return list(expr.as_ordered_terms()) if expr.is_Add else [expr]

def _lin_deg(p):
    try:
        return Poly(p, s).degree()
    except Exception:
        return None
def custom_inverse_laplace(expr):
    """
    Handles standard inverse Laplace + exponential time-shift property.
    """
    # Look for factors like exp(-a*s)
    for factor in expr.as_ordered_factors():
        if factor.is_Pow and factor.base == exp(1) and factor.exp.has(s):
            # e^(something with s)
            power = factor.exp
            if power.is_Mul and power.args[0] == -s:
                a = power.args[1]   # shift value
                remaining = simplify(expr / factor)
                f_unshifted = inverse_laplace_transform(remaining, s, t)
                return f_unshifted.subs(t, t-a) * Heaviside(t-a)

        elif factor.func == exp and factor.args[0].has(s):
            # direct exp(-a*s)
            arg = factor.args[0]
            if arg.is_Mul and -s in arg.args:
                a = [x for x in arg.args if x != -s][0]
                remaining = simplify(expr / factor)
                f_unshifted = inverse_laplace_transform(remaining, s, t)
                return f_unshifted.subs(t, t-a) * Heaviside(t-a)

    # Default: no shift term
    return inverse_laplace_transform(expr, s, t)
def _linear_root(den):
    # For a linear denominator A*s + B, return a where (s - a) == (A*s + B)/A
    P = Poly(den, s)
    A, B = P.all_coeffs() if P.degree() == 1 else (None, None)
    if A is None:
        return None, None
    a = -B / A
    return a, A

def _quad_params(den):
    # For A s^2 + B s + C -> (s - a)^2 + w^2 after normalization by A
    P = Poly(den, s)
    if P.degree() != 2:
        return None
    A, B, C = P.all_coeffs()
    a = -B/(2*A)
    w2 = C/A - a**2
    return A, a, w2

def _has_time_shift_factor(term):
    # Detect e^{-a s} factor → time shift property
    exps = [e for e in term.atoms(exp)]
    for e in exps:
        arg = e.args[0]
        if arg.has(s):
            coeff = arg.coeff(s)
            # Look for arg = -a*s  (coeff = -a)
            if coeff.is_Number or coeff.is_Symbol or coeff.is_Atom:
                # any linear multiple
                a = -coeff
                if a != 0:
                    return True, a
    return False, None

def solve_inverse_laplace(user_input):
    steps = []
    step_no = 1

    try:
        # 1) Parse
        F = parse_expr(user_input, transformations=transformations, local_dict={"s": s, "t": t, "exp": exp})
        step_no = _add_step(steps, step_no, "Given \(F(s)\)", _L(F))

        # 2) Simplify / partial fractions in s
        F_simp = simplify(F)
        F_pf = apart(F_simp, s)
        if F_pf != F_simp:
            if F_pf.is_Add:
                import string
                terms = list(F_pf.as_ordered_terms())
                assumed_terms = []
                constants_dict = {}
                letters = list(string.ascii_uppercase)
                letter_idx = 0
                
                for term in terms:
                    num, den = term.as_numer_denom()
                    if num.has(s):
                        l1 = letters[letter_idx % 26]
                        l2 = letters[(letter_idx + 1) % 26]
                        letter_idx += 2
                        assumed_terms.append(f"\\frac{{{l1}s + {l2}}}{{{_L(den)}}}")
                        constants_dict[f"{l1}s + {l2}"] = _L(num)
                    else:
                        l1 = letters[letter_idx % 26]
                        letter_idx += 1
                        assumed_terms.append(f"\\frac{{{l1}}}{{{_L(den)}}}")
                        constants_dict[l1] = _L(num)

                assumed_form = " + ".join(assumed_terms)
                step_no = _add_step(steps, step_no, "Assume Partial Fraction Form", assumed_form)
                
                const_str = ", \\quad ".join([f"{k} = {v}" for k, v in constants_dict.items()])
                step_no = _add_step(steps, step_no, "Calculate Constants", const_str)
                
            step_no = _add_step(steps, step_no, "Partial fraction decomposition result (in \(s\))", _L(F_pf))
            F = F_pf

        # 3) Linearity split
        parts = _as_parts(F)
        if len(parts) > 1:
            # Show the split list
            step_no = _add_step(steps, step_no, "By linearity, split into parts", _L(sum(parts)))

        # 4) Per-part analysis + inverse
        f_terms = []
        for i, part in enumerate(parts, start=1):
            step_no = _add_step(steps, step_no, f"Part {i}: Laplace-domain term", _L(part))

            # 4a) Property: time shift if e^{-a s} is present
            has_shift, a_shift = _has_time_shift_factor(part)
            if has_shift:
                step_no = _add_step(
                    steps,
                    step_no,
                    "Time shift property",
                    r"\mathcal{L}^{-1}\{e^{-a s}F(s)\}=f(t-a)\,u(t-a)\ \text{ with } a>0"
                )

            # 4b) Try to recognize standard forms from denominator structure
            num, den = part.as_numer_denom()
            deg_den = _lin_deg(den)

            # Repeated linear pole: 1/(s-a)^n
            if den.is_Pow and den.base.is_Add and _lin_deg(den.base) == 1 and den.exp.is_Integer and den.exp >= 1:
                a0, A0 = _linear_root(den.base)
                n = int(den.exp)
                # Formula note
                step_no = _add_step(
                    steps,
                    step_no,
                    "Formula used (repeated pole)",
                    r"\mathcal{L}^{-1}\!\left\{\frac{1}{(s-a)^n}\right\}=\frac{t^{n-1}}{(n-1)!}\,e^{a t}"
                )
                # Optional parameter note
                step_no = _add_step(steps, step_no, "Parameters", rf"a = \({ _L(a0) }\),\ n = {n}")

            # Simple linear pole: 1/(s-a)
            elif deg_den == 1:
                a0, A0 = _linear_root(den)
                # Show normalization and formula
                step_no = _add_step(
                    steps, step_no, "Formula used (simple pole)",
                    r"\mathcal{L}^{-1}\!\left\{\frac{1}{s-a}\right\}=e^{a t}"
                )
                step_no = _add_step(steps, step_no, "Parameter", rf"a = { _L(a0) }")

            # Quadratic → (s-a)^2 + w^2
            elif deg_den == 2:
                q = _quad_params(den)
                if q is not None:
                    Acoef, a0, w2 = q
                    
                    # Extract B, C for breakdown
                    P = Poly(den, s)
                    _, B, C = P.all_coeffs()
                    half_b = B/(2*Acoef)
                    c_a = C/Acoef
                    
                    step_no = _add_step(
                        steps, step_no, "Completing the Square Breakdown",
                        rf"s^2 + {_L(B/Acoef)}s + {_L(c_a)} \rightarrow \left(s + {_L(half_b)}\right)^2 + {_L(c_a)} - \left({_L(half_b)}\right)^2"
                    )
                    
                    step_no = _add_step(
                        steps, step_no, "Quadratic parameters",
                        rf"a = {_L(a0)},\ \omega^2 = {_L(w2)} \rightarrow (s - a)^2 + \omega^2"
                    )
                    # Show both cosine & sine formulas (numerator will determine the mix)
                    step_no = _add_step(
                        steps, step_no, "Formulas used",
                        r"\mathcal{L}^{-1}\!\left\{\frac{s-a}{(s-a)^2+\omega^2}\right\}=e^{a t}\cos(\omega t)"
                    )
                    step_no = _add_step(
                        steps, step_no, "Also",
                        r"\mathcal{L}^{-1}\!\left\{\frac{\omega}{(s-a)^2+\omega^2}\right\}=e^{a t}\sin(\omega t)"
                    )

            # 4c) Compute inverse of this part
            f_i = simplify(inverse_laplace_transform(part, s, t))
            step_no = _add_step(steps, step_no, f"Inverse of Part {i}", _L(f_i))
            f_terms.append(f_i)

        # 5) Combine the time-domain parts
        f_total = simplify(sum(f_terms)) if f_terms else simplify(inverse_laplace_transform(F, s, t))
        step_no = _add_step(steps, step_no, "Combine parts: \(f(t)\)", _L(f_total))
        
        step_no = _add_step(steps, step_no, "Note on Step Function", r"\text{The term } \theta(t) \text{ or } u(t) \text{ represents the Heaviside step function, meaning } f(t) = 0 \text{ for } t < 0.")

        return {
            "success": True,
            "steps": steps,
            "final_result": _L(f_total)
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
