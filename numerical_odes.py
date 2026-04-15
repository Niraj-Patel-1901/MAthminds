# numerical_odes.py
from flask import Blueprint, request, jsonify
import math
import numpy as np

try:
    import sympy as sp
except Exception as e:
    sp = None

bp = Blueprint("numerical_odes", __name__)

# ----------------- Utilities -----------------
def sanitize_expr(expr):
    if expr is None:
        return None
    return str(expr).replace("\u2212", "-").strip()

def format_num(x, prec=8):
    try:
        return float(x) if x is not None else None
    except:
        return x

# safe parse f(x,y)
def parse_f_xy(expr_str):
    if sp is None:
        raise RuntimeError("SymPy is required (pip install sympy).")
    expr_str = sanitize_expr(expr_str)
    x, y = sp.symbols('x y')
    f_sym = sp.sympify(expr_str)
    f = sp.lambdify((x, y), f_sym, modules=["math", "numpy"])
    latex = sp.latex(f_sym)
    return f, latex

# safe parse f(x)
def parse_f_x(expr_str):
    if sp is None:
        raise RuntimeError("SymPy is required (pip install sympy).")
    expr_str = sanitize_expr(expr_str)
    x = sp.symbols('x')
    f_sym = sp.sympify(expr_str)
    f = sp.lambdify(x, f_sym, modules=["math", "numpy"])
    latex = sp.latex(f_sym)
    return f, latex

# ----------------- ODE solvers -----------------
def euler_method(expr, x0, y0, h, xn, max_iter=10000):
    f, latex_f = parse_f_xy(expr)
    x = float(x0); y = float(y0); h = float(h); xn = float(xn)
    steps = []
    table = []
    steps.append(rf"Euler: \ y_0 = {y},\ x_0 = {x},\ h = {h}")
    table.append({"k": 0, "x": x, "y": y})
    k = 0
    while x + 1e-12 < xn and k < max_iter:
        k += 1
        fy = float(f(x, y))
        y_next = y + h * fy
        x_next = x + h
        table.append({"k": k, "x": format_num(x_next), "y": format_num(y_next)})
        steps.append(rf"Step\ {k}:\ y_{{{k}}} = y_{{{k-1}}} + h f(x_{{{k-1}}},y_{{{k-1}}}) = {format_num(y)} + {h} \cdot {format_num(fy)} = {format_num(y_next)}")
        x, y = x_next, y_next
    return {"method":"euler","result":format_num(y),"steps":steps,"table":table,"latex_f":latex_f}

def improved_euler_method(expr, x0, y0, h, xn, max_iter=10000):
    f, latex_f = parse_f_xy(expr)
    x = float(x0); y = float(y0); h = float(h); xn = float(xn)
    steps = []
    table = []
    steps.append(rf"Modified\ Euler\ (Heun):\ y_0={y},\ x_0={x},\ h={h}")
    table.append({"k":0,"x":x,"y":y})
    k = 0
    while x + 1e-12 < xn and k < max_iter:
        k += 1
        k1 = float(f(x, y))
        y_tilde = y + h * k1
        k2 = float(f(x + h, y_tilde))
        y_next = y + (h/2.0)*(k1 + k2)
        x_next = x + h
        table.append({"k":k,"x":format_num(x_next),"y":format_num(y_next),"k1":format_num(k1),"k2":format_num(k2)})
        steps.append(rf"Step\ {k}:\ k_1={format_num(k1)},\ k_2={format_num(k2)},\ y_{{{k}}}={format_num(y_next)}")
        x, y = x_next, y_next
    return {"method":"improved","result":format_num(y),"steps":steps,"table":table,"latex_f":latex_f}

def rk4_method(expr, x0, y0, h, xn, max_iter=10000):
    f, latex_f = parse_f_xy(expr)
    x = float(x0); y = float(y0); h = float(h); xn = float(xn)
    steps = []
    table = []
    steps.append(rf"RK4:\ y_0={y},\ x_0={x},\ h={h}")
    table.append({"k":0,"x":x,"y":y})
    k = 0
    while x + 1e-12 < xn and k < max_iter:
        k += 1
        k1 = float(f(x, y))
        k2 = float(f(x + h/2.0, y + (h/2.0)*k1))
        k3 = float(f(x + h/2.0, y + (h/2.0)*k2))
        k4 = float(f(x + h, y + h*k3))
        y_next = y + (h/6.0)*(k1 + 2*k2 + 2*k3 + k4)
        x_next = x + h
        table.append({"k":k,"x":format_num(x_next),"y":format_num(y_next),"k1":format_num(k1),"k2":format_num(k2),"k3":format_num(k3),"k4":format_num(k4)})
        steps.append(rf"Step\ {k}:\ k_1={format_num(k1)},\ k_2={format_num(k2)},\ k_3={format_num(k3)},\ k_4={format_num(k4)},\ y_{{{k}}}={format_num(y_next)}")
        x, y = x_next, y_next
    return {"method":"rk4","result":format_num(y),"steps":steps,"table":table,"latex_f":latex_f}

# ----------------- Integration methods -----------------
def trapezoidal_rule(expr, a, b, n):
    f, latex_f = parse_f_x(expr)
    a = float(a); b = float(b); n = int(n)
    h = (b-a)/n
    xs = [a + i*h for i in range(n+1)]
    fx = [float(f(xi)) for xi in xs]
    s = fx[0] + fx[-1] + 2 * sum(fx[1:-1])
    integral = (h/2.0)*s
    steps = []
    table = []
    steps.append(rf"h=\frac{{{b}-{a}}}{{{n}}}={format_num(h)}")
    steps.append(rf"\text{{Trapezoidal}}:\ \int_a^b f(x)\,dx \approx \frac{{h}}{2}[f(x_0)+2\sum_{{i=1}}^{{n-1}}f(x_i)+f(x_n)] = {format_num(integral)}")
    for i, xi in enumerate(xs):
        table.append({"i": i, "x": format_num(xi), "f(x)": format_num(fx[i])})
    return {"method":"trapezoidal","result":format_num(integral),"steps":steps,"table":table,"latex_f":latex_f}

def simpson_one_third(expr, a, b, n):
    f, latex_f = parse_f_x(expr)
    a = float(a); b = float(b); n = int(n)
    if n % 2 != 0:
        return {"success": False, "message": "Simpson 1/3 requires n to be even."}
    h = (b-a)/n
    xs = [a + i*h for i in range(n+1)]
    fx = [float(f(xi)) for xi in xs]
    s = fx[0] + fx[-1] + 4*sum(fx[i] for i in range(1,n,2)) + 2*sum(fx[i] for i in range(2,n-1,2))
    integral = (h/3.0)*s
    steps = [rf"h={format_num(h)}", rf"Simpson\ 1/3:\ \int_a^b f(x)\,dx \approx \frac{{h}}{3}[f_0 + 4f_1 + 2f_2 + \ldots + f_n] = {format_num(integral)}"]
    table = [{"i": i, "x": format_num(xs[i]), "f(x)": format_num(fx[i])} for i in range(n+1)]
    return {"method":"simpson13","result":format_num(integral),"steps":steps,"table":table,"latex_f":latex_f}

def simpson_38(expr, a, b, n):
    f, latex_f = parse_f_x(expr)
    a = float(a); b = float(b); n = int(n)
    if n % 3 != 0:
        return {"success": False, "message": "Simpson 3/8 requires n to be a multiple of 3."}
    h = (b-a)/n
    xs = [a + i*h for i in range(n+1)]
    fx = [float(f(xi)) for xi in xs]
    s = fx[0] + fx[-1]
    for i in range(1, n):
        coeff = 3 if i % 3 != 0 else 2
        s += coeff * fx[i]
    integral = (3*h/8.0) * s
    steps = [rf"h={format_num(h)}", rf"Simpson\ 3/8:\ \int_a^b f(x)\,dx \approx \frac{{3h}}{8}[...] = {format_num(integral)}"]
    table = [{"i": i, "x": format_num(xs[i]), "f(x)": format_num(fx[i])} for i in range(n+1)]
    return {"method":"simpson38","result":format_num(integral),"steps":steps,"table":table,"latex_f":latex_f}

# ----------------- Flask endpoint -----------------
@bp.route("/api/ode_integration", methods=["POST"])
def api_ode_integration():
    
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({"success": False, "message": f"Invalid JSON: {e}"}), 400

    # Accept either flat inputs or {action, payload}
    if isinstance(data, dict) and "action" in data and "payload" in data:
        action = data["action"]
        payload = data["payload"] or {}
    else:
        # backwards-compatible: data might be flat
        action = data.get("action") or ("integration" if data.get("a") is not None else "ode")
        payload = data

    try:
        if action == "ode":
            method = payload.get("method")
            expr = payload.get("expr") or payload.get("func")
            x0 = payload.get("x0")
            y0 = payload.get("y0")
            h = payload.get("h")
            xn = payload.get("xn")
            if None in (method, expr, x0, y0, h, xn):
                return jsonify({"success": False, "message": "Missing fields for ODE: method, expr, x0, y0, h, xn required."}), 400
            # route to method
            if method == "euler":
                res = euler_method(expr, x0, y0, h, xn)
            elif method == "improved":
                res = improved_euler_method(expr, x0, y0, h, xn)
            elif method == "rk4":
                res = rk4_method(expr, x0, y0, h, xn)
            else:
                return jsonify({"success": False, "message": "Unknown ODE method."}), 400
            res["success"] = True
            return jsonify(res)

        elif action == "integration":
            method = payload.get("method")
            expr = payload.get("expr") or payload.get("func")
            a = payload.get("a")
            b = payload.get("b")
            n = payload.get("n")
            if None in (method, expr, a, b, n):
                return jsonify({"success": False, "message": "Missing fields for integration: method, expr, a, b, n."}), 400
            if method == "trapezoidal":
                res = trapezoidal_rule(expr, a, b, n)
            elif method == "simpson13":
                res = simpson_one_third(expr, a, b, n)
            elif method == "simpson38":
                res = simpson_38(expr, a, b, n)
            else:
                return jsonify({"success": False, "message": "Unknown integration method."}), 400

            # If the integration function returned an error-like dict (e.g. simpson parity), pass it through
            if isinstance(res, dict) and not res.get("result") and not res.get("success"):
                # keep structure
                return jsonify(res)
            res["success"] = True
            return jsonify(res)
        else:
            return jsonify({"success": False, "message": "Unknown action (use 'ode' or 'integration')."}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {e}"}), 500
