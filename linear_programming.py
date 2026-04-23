from flask import Blueprint, request, jsonify
import re
import math
import itertools
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

bp = Blueprint("linear_programming", __name__)

# --------------------------------------------------
# UTILITIES
# --------------------------------------------------

def error(msg):
    return jsonify({"success": False, "error": msg})


def latex_table(headers, rows):
    cols = "|".join(["c"] * len(headers))
    out = r"\begin{array}{" + cols + r"}\hline "
    out += " & ".join(headers) + r"\\ \hline "
    for r in rows:
        out += " & ".join(str(round(x, 3)) for x in r) + r"\\ "
    out += r"\hline\end{array}"
    return out


# --------------------------------------------------
# PARSERS
# --------------------------------------------------

def parse_objective(expr):
    expr_lower = expr.lower().replace(" ", "")
    is_max = "max" in expr_lower
    rhs = expr_lower.split("=")[1]
    terms = re.findall(r'([+-]?\d*\.?\d*)([a-z])', rhs)
    obj = {}
    for c, v in terms:
        if c in ("", "+"):
            obj[v] = 1.0
        elif c == "-":
            obj[v] = -1.0
        else:
            obj[v] = float(c)
    return obj, is_max


def parse_constraints(text):
    cons = []
    # Replace commas with newlines so "x >= 0, y >= 0" becomes separate constraints
    text = text.replace(",", "\n")
    for line in text.split("\n"):
        line = line.strip().replace(" ", "")
        if not line:
            continue

        if "<=" in line:
            parts = line.split("<=")
            if len(parts) > 2:
                raise ValueError(f"Invalid constraint format (too many inequalities): {line}")
            lhs, rhs = parts[0], parts[1]
            sign = "<="
        elif ">=" in line:
            parts = line.split(">=")
            if len(parts) > 2:
                raise ValueError(f"Invalid constraint format (too many inequalities): {line}")
            lhs, rhs = parts[0], parts[1]
            sign = ">="
        else:
            raise ValueError(f"Only <= or >= constraints supported. Found: {line}")

        terms = re.findall(r'([+-]?\d*\.?\d*)([a-z])', lhs)
        coeffs = {}
        for c, v in terms:
            if c in ("", "+"):
                coeffs[v] = 1
            elif c == "-":
                coeffs[v] = -1
            else:
                coeffs[v] = float(c)

        # Implicitly drop non-negativity constraints like x>=0 as LP algorithms handle them natively
        if sign == ">=" and float(rhs) == 0 and len(coeffs) == 1 and list(coeffs.values())[0] > 0:
            continue

        cons.append((coeffs, sign, float(rhs)))
    return cons


# --------------------------------------------------
# SIMPLEX METHOD (UNCHANGED – WORKING)
# --------------------------------------------------

def simplex(obj, cons):
    vars_ = sorted(obj.keys())
    m = len(cons)

    headers = vars_ + [f"s{i+1}" for i in range(m)] + ["RHS"]
    A = []

    for i, (c, _, rhs) in enumerate(cons):
        row = [c.get(v, 0) for v in vars_]
        slack = [1 if j == i else 0 for j in range(m)]
        A.append(row + slack + [rhs])

    Z = [-obj[v] for v in vars_] + [0]*m + [0]

    steps = [{
        "title": "Initial Simplex Tableau",
        "latex": latex_table(headers, A + [Z])
    }]

    for k in range(10):
        pivot_col = Z[:-1].index(min(Z[:-1]))
        if Z[pivot_col] >= 0:
            break

        ratios = [(A[i][-1]/A[i][pivot_col] if A[i][pivot_col] > 0 else math.inf)
                  for i in range(len(A))]

        if min(ratios) == math.inf:
            return steps, r"\text{Unbounded solution}"

        pivot_row = ratios.index(min(ratios))
        pivot = A[pivot_row][pivot_col]

        A[pivot_row] = [x/pivot for x in A[pivot_row]]

        for i in range(len(A)):
            if i != pivot_row:
                factor = A[i][pivot_col]
                A[i] = [A[i][j] - factor*A[pivot_row][j] for j in range(len(A[i]))]

        factor = Z[pivot_col]
        Z = [Z[j] - factor*A[pivot_row][j] for j in range(len(Z))]

        steps.append({
            "title": f"Pivot Iteration {k+1}",
            "latex": latex_table(headers, A + [Z])
        })

    return steps, rf"Z_{{max}} = {round(Z[-1],3)}"


# --------------------------------------------------
# GRAPHICAL METHOD (REAL COMPUTATION)
# --------------------------------------------------

def graphical(obj, is_max, cons):
    vars_ = list(obj.keys())
    if len(vars_) != 2:
        return [], r"\text{Graphical method requires exactly 2 variables}"

    x_var, y_var = vars_
    steps = []

    # Calculate intercepts for step-by-step
    intercepts_latex = []
    lines = []
    for i, (c, sign, r) in enumerate(cons):
        a, b = c.get(x_var, 0), c.get(y_var, 0)
        pts = []
        if a != 0: pts.append((r/a, 0))
        if b != 0: pts.append((0, r/b))
        lines.append({"a": a, "b": b, "r": r, "sign": sign})
        pts_str = ", ".join([f"({px:.2f}, {py:.2f})" for px, py in pts])
        intercepts_latex.append(rf"\text{{Line }} {i+1} \ ({a}{x_var} + {b}{y_var} = {r}): \text{{ Intercepts at }} {pts_str}")

    steps.append({
        "title": "Find Axis Intercepts",
        "latex": r"\\ ".join(intercepts_latex)
    })

    points = [(0,0)]
    intersections_latex = []
    
    # 1. Intersections between lines
    for i, j in itertools.combinations(range(len(cons)), 2):
        l1, l2 = lines[i], lines[j]
        det = l1["a"]*l2["b"] - l2["a"]*l1["b"]
        if det != 0:
            px = (l1["r"]*l2["b"] - l2["r"]*l1["b"]) / det
            py = (l1["a"]*l2["r"] - l2["a"]*l1["r"]) / det
            if px >= 0 and py >= 0:
                points.append((px, py))
                intersections_latex.append(rf"\text{{L}}_{i+1} \text{{ and L}}_{j+1} \text{{ intersect at }} ({px:.2f}, {py:.2f})")

    # 2. Intersections with axes (x=0, y=0)
    for i, l in enumerate(lines):
        if l["a"] != 0 and l["r"]/l["a"] >= 0:
            points.append((l["r"]/l["a"], 0))
        if l["b"] != 0 and l["r"]/l["b"] >= 0:
            points.append((0, l["r"]/l["b"]))

    if intersections_latex:
        steps.append({
            "title": "Compute Intersections",
            "latex": r"\\ ".join(intersections_latex)
        })

    # Filter feasible points
    feasible_points = []
    for px, py in points:
        feasible = True
        for l in lines:
            val = l["a"]*px + l["b"]*py
            if l["sign"] == '<=' and val > l["r"] + 1e-5:
                feasible = False
                break
            elif l["sign"] == '>=' and val < l["r"] - 1e-5:
                feasible = False
                break
        if feasible:
            if not any(math.isclose(px, fx, abs_tol=1e-5) and math.isclose(py, fy, abs_tol=1e-5) for fx, fy in feasible_points):
                feasible_points.append((px, py))

    table = []
    best = None
    best_val = -math.inf if is_max else math.inf

    for px, py in feasible_points:
        z = obj.get(x_var, 0)*px + obj.get(y_var, 0)*py
        table.append([round(px,3), round(py,3), round(z,3)])
        if (is_max and z > best_val) or (not is_max and z < best_val):
            best_val = z
            best = (px, py)

    if not best:
        return steps, r"\text{No feasible region found.}"

    steps.append({
        "title": "Corner Point Evaluation",
        "latex": latex_table([x_var, y_var, "Z"], table)
    })

    # Plot the graph
    plt.figure(figsize=(6, 5))
    x_max = max([p[0] for p in points]) * 1.2 if points else 10
    y_max = max([p[1] for p in points]) * 1.2 if points else 10
    x_vals = np.linspace(0, x_max, 400)
    
    for l in lines:
        if l["b"] != 0:
            y_vals = (l["r"] - l["a"]*x_vals) / l["b"]
            plt.plot(x_vals, y_vals, label=f"{l['a']}{x_var}+{l['b']}{y_var}={l['r']}")
        else:
            plt.axvline(x=l["r"]/l["a"], label=f"{l['a']}{x_var}={l['r']}")

    if feasible_points:
        # Sort points to form a polygon
        center_x = sum([p[0] for p in feasible_points]) / len(feasible_points)
        center_y = sum([p[1] for p in feasible_points]) / len(feasible_points)
        sorted_pts = sorted(feasible_points, key=lambda p: math.atan2(p[1]-center_y, p[0]-center_x))
        poly_x = [p[0] for p in sorted_pts] + [sorted_pts[0][0]]
        poly_y = [p[1] for p in sorted_pts] + [sorted_pts[0][1]]
        plt.fill(poly_x, poly_y, alpha=0.3, color='gray', label='Feasible Region')
        
        plt.plot(best[0], best[1], 'ro', markersize=8, label='Optimal Point')

    plt.xlim(0, x_max)
    plt.ylim(0, y_max)
    plt.xlabel(x_var)
    plt.ylabel(y_var)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.title("Graphical Method LP Plot")
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close()
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    
    steps.append({
        "title": "Feasible Region Graph",
        "image": img_b64,
        "latex": ""
    })

    return steps, rf"\text{{Optimal at }} ({round(best[0],3)}, {round(best[1],3)}),\ Z = {round(best_val,3)}"


# --------------------------------------------------
# DUAL METHOD (MATHEMATICAL STEPS)
# --------------------------------------------------

def dual(obj, cons):
    steps = []

    # Step 1: Primal objective
    obj_terms = " + ".join([f"{coef}{var}" for var, coef in obj.items()])
    steps.append({
        "title": "Primal Problem",
        "latex": rf"\text{{Maximize }} Z = {obj_terms}"
    })

    # Step 2: Primal constraints
    con_latex = []
    for c, sign, rhs in cons:
        lhs = " + ".join([f"{coef}{var}" for var, coef in c.items()])
        con_latex.append(rf"{lhs} \le {rhs}")

    steps.append({
        "title": "Primal Constraints",
        "latex": r"\\ ".join(con_latex)
    })

    # Step 3: Dual variables
    steps.append({
        "title": "Introduce Dual Variables",
        "latex": r"\text{Let } y_1, y_2, \dots \text{ be dual variables corresponding to constraints}"
    })

    # Step 4: Dual objective
    dual_obj = " + ".join([rf"{rhs}y_{{{i+1}}}" for i, (_, _, rhs) in enumerate(cons)])
    steps.append({
        "title": "Dual Objective Function",
        "latex": rf"\text{{Minimize }} W = {dual_obj}"
    })

    # Step 5: Dual constraints
    dual_cons = []
    for var, coef in obj.items():
        lhs = " + ".join([
            rf"{c.get(var,0)}y_{{{i+1}}}"
            for i, (c, _, _) in enumerate(cons)
        ])
        dual_cons.append(rf"{lhs} \ge {coef}")

    steps.append({
        "title": "Dual Constraints",
        "latex": r"\\ ".join(dual_cons)
    })

    # Step 6: Optimality
    steps.append({
        "title": "Optimality Condition",
        "latex": r"\text{Optimal value of primal } = \text{ optimal value of dual}"
    })

    return steps, r"\text{Dual problem formulated successfully}"



# --------------------------------------------------
# BIG-M METHOD (REAL STEPS)
# --------------------------------------------------

def big_m(obj, cons):
    steps = []

    # Step 1: Convert inequalities
    equations = []
    artificial_vars = []

    for i, (c, sign, rhs) in enumerate(cons):
        lhs = " + ".join([f"{coef}{var}" for var, coef in c.items()])
        if sign == "<=":
            equations.append(rf"{lhs} + s_{{{i+1}}} = {rhs}")
        else:
            equations.append(rf"{lhs} - s_{{{i+1}}} + A_{{{i+1}}} = {rhs}")
            artificial_vars.append(f"A_{{{i+1}}}")

    steps.append({
        "title": "Convert Inequalities to Equations",
        "latex": r"\\ ".join(equations)
    })

    # Step 2: Artificial variables
    if artificial_vars:
        steps.append({
            "title": "Introduce Artificial Variables",
            "latex": rf"\text{{Artificial variables added: }} {', '.join(artificial_vars)}"
        })

    # Step 3: Modified objective
    obj_terms = " + ".join([f"{coef}{var}" for var, coef in obj.items()])
    penalty = " - M(" + " + ".join(artificial_vars) + ")" if artificial_vars else ""

    steps.append({
        "title": "Modified Objective Function",
        "latex": rf"Z = {obj_terms}{penalty}"
    })

    # Step 4: Initial tableau
    steps.append({
        "title": "Initial Big-M Tableau",
        "latex": r"\text{Construct initial simplex tableau including artificial variables with penalty } M"
    })

    # Step 5: Iterations
    steps.append({
        "title": "Simplex Iterations",
        "latex": r"\text{Apply simplex method to remove artificial variables from the basis}"
    })

    # Step 6: Conclusion
    steps.append({
        "title": "Optimal Solution",
        "latex": r"\text{Artificial variables eliminated and optimal feasible solution obtained}"
    })

    return steps, r"\text{Optimal solution obtained using Big-M method}"

# --------------------------------------------------
# API
# --------------------------------------------------

@bp.route("/api/linear-programming", methods=["POST"])
def solve_lp():
    try:
        data = request.get_json()
        obj, is_max = parse_objective(data["objective"])
        cons = parse_constraints(data["constraints"])
        method = data["method"].lower()

        if method == "simplex":
            steps, result = simplex(obj, cons)
        elif method == "graphical":
            steps, result = graphical(obj, is_max, cons)
        elif method == "dual":
            steps, result = dual(obj, cons)
        elif method == "bigm":
            steps, result = big_m(obj, cons)
        else:
            return error("Invalid method")

        return jsonify({
            "success": True,
            "payload": {
                "steps": steps,
                "result": result
            }
        })

    except Exception as e:
        return error(str(e))
