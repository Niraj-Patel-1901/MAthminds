from flask import Blueprint, request, jsonify
from sympy import symbols, integrate, cos, sin, pi, sympify, latex, simplify, Abs

fourier_bp = Blueprint('fourier', __name__)

@fourier_bp.route("/fourier/compute", methods=["POST"])
def fourier_compute():
    data = request.get_json()
    f_str = data.get("function", "")
    period_type = data.get("period_type", "2pi")
    L = data.get("L", None)
    N = int(data.get("N", 5))
    even_odd = data.get("even_odd", None)

    # Convert |x| to Abs(x) for SymPy
    f_str = f_str.replace("|x|", "Abs(x)").replace("|", "")

    x = symbols('x')
    try:
        f = sympify(f_str, locals={"Abs": Abs})
    except Exception as e:
        return jsonify({"error": f"Invalid function: {e}"}), 400

    # Determine L
    if period_type == "2pi":
        L_val = pi
    else:
        L_val = sympify(str(L)) if L else pi

    steps_latex = []

    # Step 0: General formula
    steps_latex.append(
        r"\textbf{General Fourier Series:} \quad "
        r"f(x) = \frac{a_0}{2} + \sum_{n=1}^{\infty} \left[ a_n \cos\left(\frac{n\pi x}{L}\right) + b_n \sin\left(\frac{n\pi x}{L}\right) \right]"
    )

    # Step 1: Dirichlet’s conditions
    steps_latex.append(
        r"\textbf{Step 1: Dirichlet's Conditions:} \quad f(x) \text{ is periodic, piecewise continuous, and has a finite number of maxima and minima in } [-L,L]."
    )

    # Step 2: a0 calculation
    a0_expr = (1/L_val) * integrate(f, (x, -L_val, L_val))
    a0_simplified = simplify(a0_expr)
    steps_latex.append(
        rf"\textbf{{Step 2: Compute }} a_0: \quad a_0 = \frac{{1}}{{L}} \int_{{-L}}^L f(x) \, dx = {latex(a0_simplified)}"
    )

    # Step 3 & 4: an and bn calculation
    an_list = []
    bn_list = []

    if even_odd != 'odd':  # compute an
        steps_latex.append(
            r"\textbf{Step 3: Compute } a_n: \quad a_n = \frac{1}{L} \int_{-L}^L f(x) \cos\left(\frac{n \pi x}{L}\right) dx"
        )
        for n in range(1, N+1):
            an_expr = (1/L_val) * integrate(f * cos(n * pi * x / L_val), (x, -L_val, L_val))
            an_simplified = simplify(an_expr)
            an_list.append({"n": n, "expr": an_simplified})
            steps_latex.append(rf"a_{{{n}}} = {latex(an_simplified)}")

    if even_odd != 'even':  # compute bn
        steps_latex.append(
            r"\textbf{Step 4: Compute } b_n: \quad b_n = \frac{1}{L} \int_{-L}^L f(x) \sin\left(\frac{n \pi x}{L}\right) dx"
        )
        for n in range(1, N+1):
            bn_expr = (1/L_val) * integrate(f * sin(n * pi * x / L_val), (x, -L_val, L_val))
            bn_simplified = simplify(bn_expr)
            bn_list.append({"n": n, "expr": bn_simplified})
            steps_latex.append(rf"b_{{{n}}} = {latex(bn_simplified)}")

    # Step 5: Partial sum
    series_expr = a0_simplified
    for item in an_list:
        series_expr += item["expr"] * cos(item["n"] * pi * x / L_val)
    for item in bn_list:
        series_expr += item["expr"] * sin(item["n"] * pi * x / L_val)

    series_latex = latex(simplify(series_expr))
    steps_latex.append(rf"\textbf{{Step 5: Partial Sum (N={N}):}} \quad S_{{N}}(x) = {series_latex}")

    return jsonify({
        "coefficients": {
            "a0": {"latex": latex(a0_simplified)},
            "an": [{"n": item["n"], "latex": latex(item["expr"])} for item in an_list],
            "bn": [{"n": item["n"], "latex": latex(item["expr"])} for item in bn_list],
        },
        "partial_sum": {"latex": series_latex},
        "steps_latex": steps_latex
    })
