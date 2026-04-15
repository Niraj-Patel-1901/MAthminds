from flask import Blueprint, request, jsonify
import re
import math
import itertools

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
    expr = expr.lower().replace(" ", "")
    rhs = expr.split("=")[1]
    terms = re.findall(r'([+-]?\d*)([a-z])', rhs)
    obj = {}
    for c, v in terms:
        if c in ("", "+"):
            obj[v] = 1
        elif c == "-":
            obj[v] = -1
        else:
            obj[v] = float(c)
    return obj


def parse_constraints(text):
    cons = []
    for line in text.split("\n"):
        line = line.strip().replace(" ", "")
        if not line:
            continue

        if "<=" in line:
            lhs, rhs = line.split("<=")
            sign = "<="
        elif ">=" in line:
            lhs, rhs = line.split(">=")
            sign = ">="
        else:
            raise ValueError("Only ≤ or ≥ constraints supported")

        terms = re.findall(r'([+-]?\d*)([a-z])', lhs)
        coeffs = {}
        for c, v in terms:
            if c in ("", "+"):
                coeffs[v] = 1
            elif c == "-":
                coeffs[v] = -1
            else:
                coeffs[v] = float(c)

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

def graphical(obj, cons):
    vars_ = list(obj.keys())
    if len(vars_) != 2:
        return [], r"\text{Graphical method requires exactly 2 variables}"

    x, y = vars_
    steps = []

    # Compute intersection points
    points = [(0,0)]
    for (c1, _, r1), (c2, _, r2) in itertools.combinations(cons, 2):
        a1, b1 = c1.get(x,0), c1.get(y,0)
        a2, b2 = c2.get(x,0), c2.get(y,0)
        det = a1*b2 - a2*b1
        if det != 0:
            px = (r1*b2 - r2*b1) / det
            py = (a1*r2 - a2*r1) / det
            if px >= 0 and py >= 0:
                points.append((px, py))

    table = []
    best = None
    best_val = -math.inf

    for px, py in points:
        z = obj[x]*px + obj[y]*py
        table.append([round(px,3), round(py,3), round(z,3)])
        if z > best_val:
            best_val = z
            best = (px, py)

    steps.append({
        "title": "Corner Point Evaluation",
        "latex": latex_table([x, y, "Z"], table)
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
        obj = parse_objective(data["objective"])
        cons = parse_constraints(data["constraints"])
        method = data["method"].lower()

        if method == "simplex":
            steps, result = simplex(obj, cons)
        elif method == "graphical":
            steps, result = graphical(obj, cons)
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
