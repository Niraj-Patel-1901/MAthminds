# complex_numbers.py
from flask import Blueprint, request, jsonify
import math
import cmath
from math import pi
from functools import lru_cache

# Try to import sympy for symbolic expansions. If not available, mark flag.
try:
    import sympy as sp
    SYMPY_AVAILABLE = True
    theta = sp.symbols('theta', real=True)
    x = sp.symbols('x')
except Exception:
    sp = None
    SYMPY_AVAILABLE = False

bp = Blueprint('complex_numbers', __name__, url_prefix='/api/complex')

# ---------- Utilities ----------
# Allow common math functions in evaluated numeric expressions
SAFE_NAMES = {k: getattr(math, k) for k in dir(math) if not k.startswith("__")}
SAFE_NAMES.update({
    'pi': math.pi,
    'e': math.e,
    'I': 1j, 'j': 1j, 'i': 1j,
    'complex': complex,
    # few convenience functions
    'abs': abs,
    'sqrt': math.sqrt,
    'pow': pow,
    'cmath': cmath
})

def safe_eval_num(expr: str):
    """
    Evaluate a numeric expression safely (light sandbox).
    Convert '^' -> '**', 'i' -> 'j' for complex literal support.
    NOTE: For production, replace eval with a stricter parser (sympy.sympify or asteval).
    """
    if expr is None:
        raise ValueError("Empty expression")
    e = expr.replace('^', '**')
    # replace unicode pi
    e = e.replace('π', 'pi')
    # Replace 'i' as imaginary unit but avoid replacing variable names like 'sin' -> this is naive:
    # We try replacing standalone 'i' patterns, but for simplicity we replace 'i' with 'j' globally
    e = e.replace('i', 'j')
    # Use a restricted eval environment
    return complex(eval(e, {"__builtins__": {}}, SAFE_NAMES))

def parse_complex_input(s: str):
    """
    Parse complex input like:
      3+4i, 5exp(i*pi/3), 5exp(iπ/3), 5 e^(iπ/3), etc.
    Returns (complex_value, description, r, theta)
    """
    if not s or not s.strip():
        raise ValueError("Empty input")
    s = s.strip()

    # normalize symbols
    s = s.replace('π', 'pi').replace('Π', 'pi')
    s = s.replace('^', '**')
    s = s.replace(' ', '')
    
    s = s.replace('e^(', 'exp(')  # allow "e^(i*pi/3)"
    s = s.replace('E^(', 'exp(')
    s = s.replace('exp(', '*exp(')

    try:
        # Replace exp( with cmath.exp( for complex exponentials
        s_eval = s.replace('exp(', 'cmath.exp(')
        # Replace 'i' with 'j' (Python notation)
        s_eval = s_eval.replace('i', 'j')
        val = complex(eval(s_eval, {"__builtins__": {}}, SAFE_NAMES))
        r, arg = cmath.polar(val)
        desc = f"{val.real:+.3f}{val.imag:+.3f}i"
        return val, desc, r, arg
    except Exception:
        raise ValueError(f"Could not parse complex input: '{s}'")


def complex_to_latex_cartesian(z: complex):
    a, b = z.real, z.imag
    # present small values as zero
    eps = 1e-12
    a = 0.0 if abs(a) < eps else a
    b = 0.0 if abs(b) < eps else b
    a_str = "{:g}".format(a)
    b_abs_str = "{:g}".format(abs(b))
    if abs(b) < eps:
        return a_str
    sign = "+" if b >= 0 else "-"
    return "{} {} {} i".format(a_str, sign, b_abs_str)

def polar_latex(r, theta_val):
    # return two representations: polar (r(cos+ i sin)) and exponential r e^{i theta}
    return "{}\\left(\\cos {} + i\\sin {}\\right),\\; {} e^{{i {}}}".format(r, theta_val, theta_val, r, theta_val)

# ---------- Core math helpers ----------
def cartesian_to_polar(z: complex):
    r, arg = cmath.polar(z)
    # normalize arg to (-pi, pi]
    if arg <= -math.pi:
        arg += 2 * math.pi
    if arg > math.pi:
        arg -= 2 * math.pi
    return r, arg

def de_moivre_power_steps(z: complex, n: int):
    r, arg = cartesian_to_polar(z)
    steps = []

    # Step 1: Given
    steps.append("Given complex number:")
    steps.append("z = {}.".format(complex_to_latex_cartesian(z)))

    # Step 2: Convert to polar / exponential form
    steps.append(r"Write\ z = r e^{i\theta},\quad r = |z|,\ \theta = \arg(z).")
    steps.append("Here, r = {:g} and \\theta = {:g}.".format(r, arg))

    # Step 3: Statement of De Moivre’s Theorem (VERY IMPORTANT FOR EXAM)
    steps.append(
        r"Statement\ of\ De\ Moivre's\ Theorem:\ "
        r"(re^{i\theta})^n = r^n e^{i n \theta},\ "
        r"where\ n\ is\ an\ integer."
    )

    # Step 4: Apply the theorem
    rn = r ** n
    ntheta = n * arg
    steps.append(
        "Applying De Moivre’s Theorem:"
    )
    steps.append(
        "(r e^(i\\theta))^{} = r^{} e^(i*{}\\theta).".format(n, n, n)
    )

    # Step 5: Final exponential form
    steps.append(
        "Therefore,"
    )
    steps.append(
        "z^{} = {:g} e^(i*{:g}).".format(n, rn, ntheta)
    )

    # Step 6: Convert back to Cartesian form
    val = rn * cmath.exp(1j * ntheta)
    steps.append(
        "Converting to Cartesian form:"
    )
    steps.append(
        "z^{} = {}.".format(n, complex_to_latex_cartesian(val))
    )

    return steps, val


def roots_of_complex_steps(z: complex, n: int):
    r, arg = cartesian_to_polar(z)
    steps = []
    steps.append("Find all {}th roots: z^{1/%d} = r^{1/%d} e^(i*(\\theta + 2\\pi k)/%d), k = 0,...,%d." % (n, n, n, n-1))
    steps.append("Here r = {:g}, \\theta = {:g}.".format(r, arg))
    root_r = r ** (1.0 / n)
    roots = []
    for k in range(n):
        thk = (arg + 2 * math.pi * k) / n
        val = root_r * cmath.exp(1j * thk)
        roots.append((k, root_r, thk, val))
        steps.append("k={}: z_{} = {:g} e^(i*{:g}) = {}.".format(k, k, root_r, thk, complex_to_latex_cartesian(val)))
    return steps, roots

# ---------- Trig expansions using sympy (optional) ----------
def cos_n_theta_power_polynomial(n: int):
    if not SYMPY_AVAILABLE:
        return None, "Sympy not installed."
    Tn = sp.chebyshevt(n, x)
    expr = sp.simplify(Tn.subs(x, sp.cos(theta)))
    return expr, sp.latex(expr)

def sin_n_theta_via_chebyshev(n: int):
    if not SYMPY_AVAILABLE:
        return None, "Sympy not installed."
    if n == 0:
        return sp.Integer(0), "0"
    Un = sp.chebyshevu(n - 1, x)
    expr = sp.simplify(sp.sin(theta) * Un.subs(x, sp.cos(theta)))
    return expr, sp.latex(expr)

def cos_power_to_multiple_angle(n: int):
    if not SYMPY_AVAILABLE:
        return None, "Sympy not installed."
    terms = []
    for kk in range(0, n + 1):
        coeff = sp.binomial(n, kk) / 2 ** n
        m = n - 2 * kk
        if m == 0:
            terms.append(sp.simplify(coeff))
        else:
            terms.append(sp.simplify(coeff * sp.cos(m * theta)))
    expr = sp.Add(*terms)
    return expr, sp.latex(expr)

def sin_power_to_multiple_angle(n: int):
    if not SYMPY_AVAILABLE:
        return None, "Sympy not installed."
    expr = sp.simplify(((sp.exp(sp.I * theta) - sp.exp(-sp.I * theta)) / (2 * sp.I)) ** n)
    expr_trig = sp.simplify(sp.expand(expr.rewrite(sp.cos)))
    return expr_trig, sp.latex(expr_trig)

# ---------- Helper for safe latex formatting (if sympy not available) ----------
def latex_number_safe(x):
    # If sympy available, use sp.Rational/latex where appropriate; else plain numeric string
    try:
        if SYMPY_AVAILABLE:
            return sp.latex(sp.nsimplify(x))
    except Exception:
        pass
    # fallback numeric string
    return "{:g}".format(x)

# ---------- API Route ----------
@bp.route('/solve', methods=['POST'])
def solve():
    data = request.get_json(force=True)
    problemType = data.get('problemType', 'arithmetic')
    c1s = (data.get('complex1') or '').strip()
    c2s = (data.get('complex2') or '').strip()
    power = data.get('power', None)
    roots_param = data.get('roots', None)

    # parse inputs
    try:
        if c1s:
            z1, desc1, r1, th1 = parse_complex_input(c1s)
        else:
            z1 = None; desc1 = ""; r1 = th1 = None
    except Exception as e:
        return jsonify(ok=False, error="Error parsing first complex number: {}".format(e)), 400

    try:
        if c2s:
            z2, desc2, r2, th2 = parse_complex_input(c2s)
        else:
            z2 = None; desc2 = ""; r2 = th2 = None
    except Exception as e:
        return jsonify(ok=False, error="Error parsing second complex number: {}".format(e)), 400

    steps = []
    result = {}

    try:
        if problemType == 'arithmetic':
            if (z1 is None) or (z2 is None):
                raise ValueError("Two complex numbers required for arithmetic.")
            # Addition
            add = z1 + z2
            steps.append("Addition: {} + {} = {}.".format(complex_to_latex_cartesian(z1), complex_to_latex_cartesian(z2), complex_to_latex_cartesian(add)))
            # Subtraction
            sub = z1 - z2
            steps.append("Subtraction: {} - {} = {}.".format(complex_to_latex_cartesian(z1), complex_to_latex_cartesian(z2), complex_to_latex_cartesian(sub)))
            # Multiplication
            mul = z1 * z2
            steps.append("Multiplication: (a+bi)(c+di) = (ac - bd) + i(ad + bc).")
            steps.append("Compute: {} × {} = {}.".format(complex_to_latex_cartesian(z1), complex_to_latex_cartesian(z2), complex_to_latex_cartesian(mul)))
            # Division
            if abs(z2) < 1e-14:
                div = None
                steps.append("Division: Denominator is zero; division undefined.")
            else:
                div = z1 / z2
                steps.append("Division: z1 / z2 = {}.".format(complex_to_latex_cartesian(div)))
            # conversions
            r1c, th1c = cartesian_to_polar(z1)
            r2c, th2c = cartesian_to_polar(z2)
            steps.append("z_1 = {} e^(i*{}); z_2 = {} e^(i*{}).".format(latex_number_safe(r1c), th1c, latex_number_safe(r2c), th2c))
            result = {
                "addition": {"latex": complex_to_latex_cartesian(add)},
                "subtraction": {"latex": complex_to_latex_cartesian(sub)},
                "multiplication": {"latex": complex_to_latex_cartesian(mul)},
                "division": {"latex": complex_to_latex_cartesian(div) if div is not None else None},
            }

        elif problemType in ('polar', 'convert'):
            if z1 is None:
                raise ValueError("Provide a complex number.")
            r, arg = cartesian_to_polar(z1)
            steps.append("Given: z = {}.".format(complex_to_latex_cartesian(z1)))
            steps.append("Modulus: r = sqrt(a^2 + b^2) = {:g}.".format(r))
            steps.append("Argument: \\theta = arg(z) = {:g}.".format(arg))
            # use parentheses/exponential form (avoid braces in formatted string)
            steps.append("Polar form: z = {:g}(cos {:g} + i sin {:g}).".format(r, arg, arg))
            steps.append("Exponential form: z = {:g} e^(i*{:g}).".format(r, arg))
            result = {
                "cartesian": complex_to_latex_cartesian(z1),
                "polar": "{}(cos {} + i sin {})".format(r, arg, arg),
                "exponential": "{} e^(i*{})".format(r, arg),
                "r": r,
                "theta": arg
            }

        elif problemType == 'demoivre':
            if z1 is None:
                raise ValueError("Provide a complex number.")
            if power is None or str(power).strip() == "":
                raise ValueError("Provide a power n.")
            n = int(power)
            steps_dm, val = de_moivre_power_steps(z1, n)
            steps.extend(steps_dm)
            result = {"power": n, "result_cartesian": complex_to_latex_cartesian(val), "numeric": {"real": val.real, "imag": val.imag}}

        elif problemType == 'roots':
            if z1 is None:
                raise ValueError("Provide a complex number (base).")
            if roots_param is None or str(roots_param).strip() == "":
                raise ValueError("Provide number of roots n.")
            n = int(roots_param)
            steps_r, roots_list = roots_of_complex_steps(z1, n)
            steps.extend(steps_r)
            result_roots = []
            for k, rad, thk, val in roots_list:
                result_roots.append({"k": k, "r_root": rad, "theta": thk, "latex": complex_to_latex_cartesian(val)})
            result = {"n": n, "roots": result_roots}

        elif problemType == 'trig_expand':
            if power is None or str(power).strip() == "":
                raise ValueError("Provide integer n for trigonometric expansion.")

            n = int(power)

            if not SYMPY_AVAILABLE:
                steps.append("SymPy is not installed on the server. Symbolic trigonometric expansions are unavailable.")
                result = {"sympy": False}

            else:
                # ---- Step 1: Problem statement ----
                steps.append("Given n = {}. We perform trigonometric expansions as per syllabus.".format(n))

        # ---- Step 2: cos(nθ) in terms of cosθ ----
                expr_cos, latex_cos = cos_n_theta_power_polynomial(n)
                steps.append(
                    r"Express\ \cos({}\theta)\ \text{in terms of powers of}\ \cos\theta:".format(n)
                )
                steps.append(latex_cos)

                # ---- Step 3: sin(nθ) using Chebyshev polynomial ----
                expr_sin, latex_sin = sin_n_theta_via_chebyshev(n)
                steps.append(
                    r"Express\ \sin({}\theta)\ \text{as}\ \sin\theta \cdot U_{{{}}}(\cos\theta):".format(n, n-1)
                )
                steps.append(latex_sin)

            # ---- Step 4: cosⁿθ in multiple-angle form ----
                cospow_expr, cospow_latex = cos_power_to_multiple_angle(n)
                steps.append(
                    r"Express\ \cos^{{{}}}\theta\ \text{in multiple-angle form:}".format(n)
                )
                steps.append(cospow_latex)

            # ---- Step 5: sinⁿθ in multiple-angle form ----
            sinpow_expr, sinpow_latex = sin_power_to_multiple_angle(n)
            steps.append(
                r"Express\ \sin^{{{}}}\theta\ \text{in multiple-angle form:}".format(n)
            )
            steps.append(sinpow_latex)

        # ---- Final Result ----
            steps.append("Hence, the required trigonometric expansions are obtained.")

            result = {
                "cos_n_theta_poly": latex_cos,
                "sin_n_theta_poly": latex_sin,
                "cos_pow_multiple": cospow_latex,
                "sin_pow_multiple": sinpow_latex
            }


    except Exception as e:
        return jsonify(ok=False, error="Computation error: {}".format(e)), 400

    return jsonify(ok=True, steps=steps, result=result, sympy_available=SYMPY_AVAILABLE)