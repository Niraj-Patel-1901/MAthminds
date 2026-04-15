# beta_gamma.py
import re
from collections import Counter
from flask import Blueprint, request, jsonify
from sympy import (
    symbols, Symbol, sympify, simplify, S, Rational,
    exp, log, sqrt, sin, cos, tan, integrate, gamma as sympy_gamma,
    beta as sympy_beta, latex, Derivative, Integral
)
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

beta_gamma_bp = Blueprint("beta_gamma", __name__)

# locals mapping for sympify/parse_expr
COMMON_LOCALS = {
    'exp': exp, 'log': log, 'sqrt': sqrt,
    'sin': sin, 'cos': cos, 'tan': tan,
    'integrate': integrate, 'gamma': sympy_gamma, 'beta': sympy_beta,
    'S': S
}

TRANSFORMS = (standard_transformations + (implicit_multiplication_application,))


def _parse_limit(s):
    if s is None:
        return None
    st = str(s).strip()
    if st.lower() in ('oo', 'infty', 'inf', 'infinity'):
        return S.Infinity
    if st.lower() in ('-oo', '-infty', '-inf', '-infinity'):
        return -S.Infinity
    if '/' in st:
        try:
            a, b = st.split('/')
            return Rational(int(a), int(b))
        except Exception:
            pass
    try:
        return sympify(st, locals=COMMON_LOCALS)
    except Exception:
        return st


def _try_match_gamma_form(integrand, var):
    """
    Match integrand of the form x**a * exp(-b * x**c) (times a constant).
    Returns tuple (a, b, c, const) if matched else None.
    """
    from sympy import Wild
    A = Wild('A'); B = Wild('B'); C = Wild('C'); CONST = Wild('CONST')
    # pattern: CONST * var**A * exp(-B*var**C)
    pattern = CONST * (var**A) * exp(-B * (var**C))
    m = integrand.match(pattern)
    if m:
        return (m.get(A), m.get(B), m.get(C), m.get(CONST))
    # try without explicit CONST (CONST = 1)
    pattern2 = (var**A) * exp(-B * (var**C))
    m2 = integrand.match(pattern2)
    if m2:
        return (m2.get(A), m2.get(B), m2.get(C), S.One)
    return None


def _try_match_beta_form(integrand, var):
    """
    Match integrand x**(p-1)*(1-x)**(q-1)
    """
    from sympy import Wild
    P = Wild('P'); Q = Wild('Q')
    pattern = (var**(P - 1)) * ((1 - var)**(Q - 1))
    m = integrand.match(pattern)
    if m:
        return (m.get(P), m.get(Q))
    return None


@beta_gamma_bp.route("/api/special-integrals", methods=["POST"])
def api_special_integrals():
    """
    Unified handler:
    - legacy 'gamma', 'beta', 'diff_integral'
    - new 'symbolic' for integrate(...) and diff(integrate(...), ...)
    """
    try:
        data = request.get_json(force=True)
        if not data or "type" not in data:
            return jsonify({"success": False, "error": "Missing 'type'."}), 400

        typ = data["type"]
        params = data.get("params", {})
        steps = []
        result_latex = ""
        input_desc = ""

        # ---------- legacy handlers (keep for compatibility) ----------
        if typ in ("gamma", "beta", "diff_integral"):
            if typ == "gamma":
                n_raw = params.get("n")
                if n_raw is None:
                    return jsonify({"success": False, "error": "Missing n"}), 400
                n = sympify(str(n_raw), locals=COMMON_LOCALS)
                input_desc = rf"\(\Gamma({latex(n)})\)"
                steps.append(rf"\(\Gamma({latex(n)})=\int_0^\infty x^{{{latex(n)}-1}} e^{{-x}}\,dx\)")
                try:
                    val = sympy_gamma(n)
                    result_latex = latex(simplify(val))
                except Exception:
                    result_latex = latex(sympy_gamma(n))
            elif typ == "beta":
                p = sympify(str(params.get("p")), locals=COMMON_LOCALS)
                q = sympify(str(params.get("q")), locals=COMMON_LOCALS)
                input_desc = rf"\(B({latex(p)},{latex(q)})\)"
                steps.append(rf"\(B({latex(p)},{latex(q)})=\int_0^1 x^{{{latex(p)}-1}}(1-x)^{{{latex(q)}-1}}dx\)")
                steps.append(r"Using \(B(p,q)=\dfrac{\Gamma(p)\Gamma(q)}{\Gamma(p+q)}\).")
                try:
                    val = sympy_beta(p, q)
                    result_latex = latex(simplify(val))
                    steps.append(rf"Computed: \(B({latex(p)},{latex(q)}) = {latex(val)}\).")
                except Exception:
                    result_latex = rf"B({latex(p)},{latex(q)})"
            else:
                # diff_integral minimal fallback (keep old behavior)
                integrand_raw = params.get("integrand")
                var_raw = params.get("var", "x")
                param_raw = params.get("param", None)
                lower_raw = params.get("lower", "0"); upper_raw = params.get("upper", "1")
                if not integrand_raw or not param_raw:
                    return jsonify({"success": False, "error": "Missing integrand or param"}), 400
                var_sym = Symbol(str(var_raw)); param_sym = Symbol(str(param_raw))
                integrand = sympify(integrand_raw, locals=COMMON_LOCALS)
                a = _parse_limit(lower_raw); b = _parse_limit(upper_raw)
                input_desc = rf"\(I({latex(param_sym)})=\int_{{{latex(a)}}}^{{{latex(b)}}} {latex(integrand)}\,d{latex(var_sym)}\)"
                steps.append(rf"Let \(I({latex(param_sym)})=\int_{{{latex(a)}}}^{{{latex(b)}}} {latex(integrand)}\,d{latex(var_sym)}\).")
                steps.append(rf"Differentiating under integral sign: \(\dfrac{{d}}{{d{latex(param_sym)}}}I({latex(param_sym)})=\int_{{{latex(a)}}}^{{{latex(b)}}}\dfrac{{\partial}}{{\partial {latex(param_sym)}}}{latex(integrand)}\,d{latex(var_sym)}\).")
                try:
                    integrand_diff = simplify(sympify(str(integrand)).diff(param_sym))
                    integrated = integrate(integrand_diff, (var_sym, a, b))
                    result_latex = latex(simplify(integrated))
                    steps.append(rf"Result: \(\dfrac{{d}}{{d{latex(param_sym)}}}I({latex(param_sym)}) = {result_latex}\).")
                except Exception as e:
                    return jsonify({"success": False, "error": f"Could not compute derivative integral: {e}"}), 500

            return jsonify({"success": True, "input": input_desc, "result": result_latex, "steps": steps})

        # ---------- new symbolic integrals handling ----------
        if typ == "symbolic":
            integral_str = params.get("integral", "").strip()
            if not integral_str:
                return jsonify({"success": False, "error": "Please provide the integral (e.g. integrate(...))."}), 400

            # 1) Display the raw user input
            input_desc = f"\\({integral_str}\\)"
            steps.append("Step 1: Input parsed: " + input_desc)

            # Attempt to sympify first (this may produce Integral or Derivative objects)
            parsed = None
            try:
                parsed = sympify(integral_str, locals=COMMON_LOCALS)
            except Exception:
                parsed = None

            # If parsed is a Derivative (diff(...)) we handle differentiation-under-integral
            if parsed is not None and getattr(parsed, 'func', None) is not None and parsed.func.__name__ == 'Derivative':
                # Handle Derivative objects robustly (also covers diff(...) with multiple symbols and orders)
                steps.append("Step 2: Detected top-level derivative (Differentiation under integral sign candidate).")
                deriv_obj = parsed
                # Counter of derivative variables (SymPy's Derivative has .variables attribute)
                try:
                    vars_tuple = tuple(deriv_obj.variables)
                except Exception:
                    # fallback: use args[1:]
                    vars_tuple = deriv_obj.args[1:]
                var_counts = Counter(vars_tuple)  # counts multiplicities -> orders
                # Extract inner function being differentiated
                inner = deriv_obj.args[0]
                # Ensure inner is an Integral
                if getattr(inner, 'func', None) is not None and inner.func.__name__ == 'Integral':
                    integral_obj = inner
                    # get integrand and limits
                    try:
                        integrand = integral_obj.args[0]
                        # integral_obj.limits gives tuples like (x, lower, upper)
                        if hasattr(integral_obj, 'limits') and len(integral_obj.limits) > 0:
                            lim = integral_obj.limits[0]
                            var_sym = lim[0]
                            lower = lim[1]
                            upper = lim[2]
                        else:
                            # fallback if args structure different
                            var_sym = integral_obj.args[1][0]
                            lower = integral_obj.args[1][1]
                            upper = integral_obj.args[1][2]
                    except Exception as e:
                        return jsonify({"success": False, "error": f"Could not extract integral limits: {e}"}), 400

                    steps.append(rf"Step 3: Inner integral detected: \(\int_{{{latex(lower)}}}^{{{latex(upper)}}} {latex(integrand)}\,d{latex(var_sym)}\).")

                    # Now apply differentiation under integral: compute partial derivatives of integrand
                    new_integrand = integrand
                    deriv_steps = []
                    # For deterministic ordering, iterate through var_counts items
                    for param_sym, order in var_counts.items():
                        # param_sym might be a Symbol or string; ensure Symbol
                        if not isinstance(param_sym, Symbol):
                            param_sym = Symbol(str(param_sym))
                        steps.append(rf"Step 4: Differentiating integrand w.r.t. parameter {latex(param_sym)} of order {order}.")
                        try:
                            new_integrand = simplify(new_integrand.diff(param_sym, order))
                            deriv_steps.append(rf"\(\dfrac{{\partial^{order}}}{{\partial {latex(param_sym)}^{order}}}({latex(integrand)}) = {latex(new_integrand)}\)")
                        except Exception as e:
                            return jsonify({"success": False, "error": f"Could not differentiate integrand: {e}"}), 500

                    # Add derivative expressions to steps
                    for idx, s in enumerate(deriv_steps, start=1):
                        steps.append(rf"Step 4.{idx}: {s}")

                    # Integrate the new integrand over the same limits
                    steps.append(rf"Step 5: Integrate the new integrand over the same limits: \(\int_{{{latex(lower)}}}^{{{latex(upper)}}} {latex(new_integrand)}\,d{latex(var_sym)}\).")
                    try:
                        computed = integrate(new_integrand, (var_sym, lower, upper))
                        computed_s = simplify(computed)
                        result_latex = latex(computed_s)
                        steps.append(rf"Step 6: Computed integral after differentiation: {latex(computed_s)}.")
                        # Attempt to detect Gamma/Beta forms for nicer explanation (reuse existing detectors)
                        if lower == S.Zero and upper == S.Infinity:
                            gmatch = _try_match_gamma_form(new_integrand, var_sym)
                            if gmatch:
                                A, B, C, CONST = gmatch
                                try:
                                    formula = (CONST / C) * (B ** (-(A + 1) / C)) * sympy_gamma((A + 1) / C)
                                    steps.append("Detected Gamma-type structure in the differentiated integrand.")
                                    steps.append(rf"Using standard formula, the integral equals: \(\frac{{{latex(CONST)}}}{{{latex(C)}}} {latex(B)}^{{-\frac{{{latex(A+1)}}}{{{latex(C)}}}}} \Gamma\!\left(\frac{{{latex(A+1)}}}{{{latex(C)}}}\right)\).")
                                    result_latex = latex(simplify(formula))
                                except Exception:
                                    # keep computed form
                                    pass
                        elif lower == 0 and upper == 1:
                            bmatch = _try_match_beta_form(new_integrand, var_sym)
                            if bmatch:
                                P, Q = bmatch
                                try:
                                    formula = sympy_gamma(P) * sympy_gamma(Q) / sympy_gamma(P + Q)
                                    steps.append("Detected Beta-type structure in the differentiated integrand.")
                                    steps.append(rf"Using \(B(p,q)=\dfrac{{\Gamma(p)\Gamma(q)}}{{\Gamma(p+q)}}\).")
                                    result_latex = latex(simplify(formula))
                                except Exception:
                                    pass

                        # final step - return
                        steps.append(rf"Final: \(\dfrac{{d}}{{d\cdots}} \int = {result_latex}\)")
                        return jsonify({"success": True, "input": input_desc, "result": result_latex, "steps": steps})
                    except Exception as e:
                        return jsonify({"success": False, "error": f"Could not compute the integral after differentiation: {e}"}), 500
                else:
                    return jsonify({"success": False, "error": "Derivative is not applied to an integral."}), 400

            # If parsed wasn't a Derivative object, continue handling integrate(...) patterns via regex as before
            # Use regex to extract inside integrate(...) if present in the string
            m = re.match(r'\s*integrate\s*\(\s*(.+)\s*,\s*(\(.+\))\s*\)\s*$', integral_str, re.DOTALL)
            if not m:
                m = re.match(r'\s*integrate\s*\(\s*(.+)\s*,\s*(.+)\s*\)\s*$', integral_str, re.DOTALL)

            if m:
                integrand_str = m.group(1).strip()
                limits_str = m.group(2).strip()
                try:
                    limits_obj = sympify(limits_str, locals=COMMON_LOCALS)
                except Exception:
                    limits_obj = None

                try:
                    if hasattr(limits_obj, '__iter__') and len(limits_obj) >= 1:
                        if len(limits_obj) == 3:
                            var_sym = Symbol(str(limits_obj[0]))
                            lower = _parse_limit(limits_obj[1])
                            upper = _parse_limit(limits_obj[2])
                        elif len(limits_obj) == 1:
                            var_sym = Symbol(str(limits_obj[0]))
                            lower = None; upper = None
                        else:
                            var_sym = Symbol(str(limits_obj[0]))
                            lower = None; upper = None
                    else:
                        if isinstance(limits_obj, Symbol):
                            var_sym = Symbol(str(limits_obj))
                            lower = None; upper = None
                        else:
                            var_sym = Symbol('x'); lower = None; upper = None
                except Exception:
                    var_sym = Symbol('x'); lower = None; upper = None

                # Parse integrand
                try:
                    integrand_expr = sympify(integrand_str, locals={**COMMON_LOCALS, str(var_sym): var_sym})
                except Exception:
                    try:
                        integrand_expr = parse_expr(integrand_str, local_dict={**COMMON_LOCALS, str(var_sym): var_sym}, transformations=TRANSFORMS)
                    except Exception:
                        integrand_expr = None

                # Compute integral if possible
                try:
                    if lower is None or upper is None:
                        computed = integrate(integrand_expr, var_sym)
                    else:
                        computed = integrate(integrand_expr, (var_sym, lower, upper))
                    computed_s = simplify(computed)
                except Exception as e:
                    try:
                        computed_s = sympify(integral_str, locals=COMMON_LOCALS)
                    except Exception:
                        return jsonify({"success": False, "error": f"Could not compute integral: {e}"}), 400

                # Detection: Gamma / Beta / sqrt substitution etc. (same as before)
                detected_type = None
                if lower == S.Zero and upper == S.Infinity and integrand_expr is not None:
                    gmatch = _try_match_gamma_form(integrand_expr, var_sym)
                    if gmatch:
                        A, B, C, CONST = gmatch
                        try:
                            formula = (CONST / C) * (B ** (-(A + 1) / C)) * sympy_gamma((A + 1) / C)
                            steps.append("Step 2: Detected Gamma-type integral (form \\(x^{a} e^{-b x^{c}}\\)).")
                            steps.append(rf"Using substitution \(t = {latex(B)} {latex(var_sym)}^{latex(C)}\) or known formula gives:")
                            steps.append(rf"\(\displaystyle \text{{Result}} = \frac{{{latex(CONST)}}}{{{latex(C)}}} {latex(B)}^{{-\frac{{{latex(A+1)}}}{{{latex(C)}}}}} \Gamma\!\left(\frac{{{latex(A+1)}}}{{{latex(C)}}}\right)\)")
                            result_latex = latex(simplify(formula))
                            detected_type = "Gamma Integral"
                        except Exception:
                            result_latex = latex(computed_s)
                            detected_type = "Integral (computed)"
                    else:
                        if integrand_expr is not None and integrand_expr.has(sqrt(var_sym)):
                            steps.append("Step 2: Detected square-root in integrand: trying substitution \(t=\\sqrt{x}\\).")
                            t = Symbol('t')
                            sub_expr = integrand_expr.subs(var_sym, t**2) * (2 * t)
                            try:
                                new_integrand = simplify(sub_expr)
                                steps.append(rf"After substitution \(x=t^2\), integrand becomes {latex(new_integrand)} and limits transform accordingly.")
                                new_comp = integrate(new_integrand, (t, 0, S.Infinity))
                                new_comp_s = simplify(new_comp)
                                steps.append(rf"Compute integral in t: {latex(new_comp_s)}.")
                                result_latex = latex(new_comp_s)
                                detected_type = "Transformed Integral (sqrt substitution)"
                            except Exception:
                                result_latex = latex(computed_s)
                                detected_type = "Integral (computed)"
                        else:
                            result_latex = latex(computed_s)
                            detected_type = "Integral (computed)"
                elif lower == 0 and upper == 1 and integrand_expr is not None:
                    bmatch = _try_match_beta_form(integrand_expr, var_sym)
                    if bmatch:
                        P, Q = bmatch
                        steps.append("Step 2: Detected Beta-type integral (form \\(x^{p-1}(1-x)^{q-1}\\)).")
                        steps.append(rf"Using \(B(p,q)=\dfrac{{\Gamma(p)\Gamma(q)}}{{\Gamma(p+q)}}\).")
                        formula = sympy_gamma(P) * sympy_gamma(Q) / sympy_gamma(P + Q)
                        result_latex = latex(simplify(formula))
                        detected_type = "Beta Integral"
                    else:
                        result_latex = latex(computed_s)
                        detected_type = "Integral (computed)"
                else:
                    result_latex = latex(computed_s)
                    detected_type = "Integral (computed)"

                if detected_type:
                    steps.insert(1, f"Detected type: {detected_type}")
                steps.append(rf"Step N: Computed value (SymPy): {latex(computed_s)}")

                return jsonify({"success": True, "input": input_desc, "result": result_latex, "steps": steps})

            else:
                # Not matching integrate(...) regex — try raw sympify evaluation
                try:
                    expr = sympify(integral_str, locals=COMMON_LOCALS)
                    # If it's an Integral object, evaluate
                    if getattr(expr, 'func', None) is not None and expr.func.__name__ == 'Integral':
                        computed = expr.doit()
                        computed_s = simplify(computed)
                        result_latex = latex(computed_s)
                        steps.append("Step 2: Detected Integral object and evaluated with SymPy.")
                        steps.append(rf"Result: {latex(computed_s)}")
                        return jsonify({"success": True, "input": input_desc, "result": result_latex, "steps": steps})
                    else:
                        return jsonify({"success": False, "error": "Input not recognized as an integral. Use integrate(...) format (or diff(integrate(...), param))."}), 400
                except Exception as e:
                    return jsonify({"success": False, "error": f"Could not parse input: {e}"}), 400

        else:
            return jsonify({"success": False, "error": f"Unknown type '{typ}'."}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
