# maxima_minima_solver.py
from sympy import (
    symbols, sympify, diff, solve, Eq, latex, simplify, Matrix, Symbol, S, And, Interval,
    Piecewise, N, Abs, pi, I
)
from sympy.core.sympify import SympifyError
import re

# primary symbols
x, y, lam = symbols('x y lam')

def _parse_range(range_str: str):
    """
    Accept forms like:
      "-1 ≤ x ≤ 1" or "-1 <= x <= 1" or "-1<x<1" or "-1 to 1" or "-1,1"
    Return tuple (low, high) as floats if parseable, else None.
    """
    if not range_str:
        return None
    s = range_str.replace('≤', '<=').replace('–','-').replace('—','-').replace(' ', '')
    # try pattern: a<=x<=b or a<x<b
    m = re.search(r'([\-0-9\.]+)(?:<=|<)(?:x|X)(?:<=|<)([\-0-9\.]+)', s)
    if m:
        try:
            return (float(m.group(1)), float(m.group(2)))
        except:
            return None
    # try simple "a to b" or "a,b" or "a b"
    m2 = re.search(r'([\-0-9\.]+)[, ]+([\-0-9\.]+)', range_str)
    if m2:
        try:
            return (float(m2.group(1)), float(m2.group(2)))
        except:
            return None
    m3 = re.search(r'([\-0-9\.]+)to([\-0-9\.]+)', range_str.replace(' ', ''))
    if m3:
        try:
            return (float(m3.group(1)), float(m3.group(2)))
        except:
            return None
    return None

def _safe_sympify(expr_str: str, local_vars=None):
    """
    Convert user-provided string into SymPy expression.
    - Replaces i/j with I (imag unit)
    - Strips outer whitespace
    - Uses provided local_vars mapping (like {'x': x, 'y': y})
    """
    if not isinstance(expr_str, str):
        raise ValueError("Expression must be a string.")
    s = expr_str.strip()
    # make common imaginary notation acceptable: 2+3i or 2+3*i
    # replace 'i' or 'j' that appear after digits or parentheses with *I
    # but be careful not to replace variables named 'i' (rare here)
    # simplest approach: replace standalone 'i' or trailing i in numbers:
    s = s.replace(' ', '')
    # replace occurrences like 3i -> 3*I
    s = re.sub(r'(?P<num>(\d|\)|[A-Za-z]))i\b', r'\g<num>*I', s)
    s = re.sub(r'(?P<num>(\d|\)|[A-Za-z]))j\b', r'\g<num>*I', s)
    # also allow imaginary unit 'I' directly if user typed it
    s = s.replace('I*I', 'I*I')  # noop to clarify
    # prepare locals
    locals_in = {'x': x, 'y': y, 'I': I, 'pi': pi}
    if local_vars:
        locals_in.update(local_vars)
    try:
        expr = sympify(s, locals=locals_in)
        return expr
    except SympifyError as e:
        # attempt a second pass adding '*' between literal/parenthesis adjacency
        s2 = re.sub(r'(\d)(\()', r'\1*(', s)
        try:
            expr = sympify(s2, locals=locals_in)
            return expr
        except Exception:
            raise ValueError(f"Could not parse expression: {expr_str}") from e

def _latex_point(pt_dict):
    """Return LaTeX for a solution dict {x: val, y: val} or tuple."""
    if isinstance(pt_dict, dict):
        return r"\left(" + latex(pt_dict.get(x, '?')) + r", " + latex(pt_dict.get(y, '?')) + r"\right)"
    elif isinstance(pt_dict, (list, tuple)) and len(pt_dict) >= 2:
        return r"\left(" + latex(pt_dict[0]) + r", " + latex(pt_dict[1]) + r"\right)"
    else:
        return latex(pt_dict)

def _evalf_if_possible(expr):
    try:
        return N(expr)
    except Exception:
        return expr

def solve_maxima_minima(problem_type: str, function_str: str,
                        constraint_str: str = None,
                        x_range_str: str = None, y_range_str: str = None):
    """
    Returns dict:
      { success: bool,
        steps: [latex steps],
        candidates: [ {point: latex, value: latex} ... ],
        result: latex summary,
        input: latex(function) , constraint: latex(constraint if any)
      }
    """
    steps = []
    try:
        if not function_str or function_str.strip() == "":
            return {"success": False, "error": "No objective function provided."}
        f = _safe_sympify(function_str)
        steps.append(r"\text{Objective function: } f(x,y) = " + latex(f))

        constraint = None
        g = None
        if constraint_str and constraint_str.strip():
            # Expect forms like "g(x,y) = c" or "g(x,y)=0"
            # Split at '='
            if '=' in constraint_str:
                left, right = constraint_str.split('=', 1)
                left_expr = _safe_sympify(left)
                right_expr = _safe_sympify(right)
                # convert to g(x,y) = left - right = 0
                g = simplify(left_expr - right_expr)
                steps.append(r"\text{Constraint: } " + latex(left_expr) + r" = " + latex(right_expr))
            else:
                # treat constraint_str as expression = 0
                g = _safe_sympify(constraint_str)
                steps.append(r"\text{Constraint (assumed) } g(x,y) = " + latex(g))
            constraint = latex(g)

        # parse ranges for absolute/boundary
        x_range = _parse_range(x_range_str) if x_range_str else None
        y_range = _parse_range(y_range_str) if y_range_str else None
        if x_range:
            steps.append(r"\text{Domain for } x: " + latex(x_range[0]) + " \\le x \\le " + latex(x_range[1]))
        if y_range:
            steps.append(r"\text{Domain for } y: " + latex(y_range[0]) + " \\le y \\le " + latex(y_range[1]))

        candidates = []  # list of (point_dict, value)

        if problem_type == "unconstrained":
            steps.append(r"\text{Unconstrained optimization: solve } f_x = 0, f_y = 0")
            fx = diff(f, x)
            fy = diff(f, y)
            steps.append(r"f_x = " + latex(fx))
            steps.append(r"f_y = " + latex(fy))
            sol = solve([Eq(fx, 0), Eq(fy, 0)], [x, y], dict=True)
            if not sol:
                steps.append(r"\text{No finite critical points found (system returned no solutions).}")
            else:
                steps.append(r"\text{Critical points:}")
                for s in sol:
                    # compute Hessian and classify
                    fxx = diff(fx, x)
                    fxy = diff(fx, y)
                    fyy = diff(fy, y)
                    subs_map = {x: s.get(x, s.get(Symbol('x'), None)), y: s.get(y, s.get(Symbol('y'), None))}
                    # compute discriminant D = fxx*fyy - fxy^2
                    D = simplify(fxx.subs(s) * fyy.subs(s) - (fxy.subs(s))**2)
                    fxx_val = simplify(fxx.subs(s))
                    # Evaluate numeric approximations if possible
                    D_eval = _evalf_if_possible(D)
                    fxx_eval = _evalf_if_possible(fxx_val)
                    # classification
                    try:
                        if (D_eval.is_real or True) and float(D_eval) > 0:
                            if float(fxx_eval) > 0:
                                classification = "Local minimum"
                            elif float(fxx_eval) < 0:
                                classification = "Local maximum"
                            else:
                                classification = "Inconclusive (f_{xx} = 0)"
                        elif (D_eval.is_real or True) and float(D_eval) < 0:
                            classification = "Saddle point"
                        else:
                            classification = "Inconclusive"
                    except Exception:
                        # fallback symbolic checks
                        if D.is_positive:
                            classification = "Local min or max (D>0) — check f_{xx}"
                        else:
                            classification = "Inconclusive"
                    val = simplify(f.subs(s))
                    candidates.append((s, val, classification))
                    steps.append(r"\text{Point } " + _latex_point(s) + r",\quad D = " + latex(D) +
                                 r",\quad f_{xx} = " + latex(fxx_val) + r"\Rightarrow " + classification)

        elif problem_type == "constrained":
            if g is None:
                return {"success": False, "error": "Constrained problem selected but no constraint provided."}
            steps.append(r"\text{Constrained optimization using Lagrange multipliers}")
            L = f - lam * g
            Lx = diff(L, x)
            Ly = diff(L, y)
            Llambda = diff(L, lam)
            steps.append(r"L(x,y,\lambda) = " + latex(L))
            steps.append(r"\frac{\partial L}{\partial x} = " + latex(Lx))
            steps.append(r"\frac{\partial L}{\partial y} = " + latex(Ly))
            steps.append(r"\frac{\partial L}{\partial \lambda} = " + latex(Llambda))
            # solve Lx=0, Ly=0, g=0
            sol = solve([Eq(Lx, 0), Eq(Ly, 0), Eq(g, 0)], [x, y, lam], dict=True)
            if not sol:
                steps.append(r"\text{No solutions found for Lagrange system.}")
            else:
                steps.append(r"\text{Candidate points (from solving Lx=0, Ly=0, g=0):}")
                for s in sol:
                    # keep only x,y portion
                    s_xy = {x: s.get(x), y: s.get(y)}
                    val = simplify(f.subs(s_xy))
                    candidates.append((s_xy, val, "Candidate (Lagrange multiplier method)"))
                    steps.append(r"\text{Point } " + _latex_point(s_xy) + r",\quad f = " + latex(val))

        elif problem_type in ("absolute", "boundary"):
            steps.append(r"\text{Absolute / boundary extrema (search over domain and boundaries)}")
            # First find interior critical points (same as unconstrained)
            fx = diff(f, x)
            fy = diff(f, y)
            sol = solve([Eq(fx, 0), Eq(fy, 0)], [x, y], dict=True)
            if sol:
                steps.append(r"\text{Interior critical points:}")
                for s in sol:
                    # check if in ranges (if ranges specified)
                    in_domain = True
                    if x_range:
                        xv = s.get(x)
                        try:
                            if float(N(xv)) < x_range[0] - 1e-9 or float(N(xv)) > x_range[1] + 1e-9:
                                in_domain = False
                        except Exception:
                            pass
                    if y_range:
                        yv = s.get(y)
                        try:
                            if float(N(yv)) < y_range[0] - 1e-9 or float(N(yv)) > y_range[1] + 1e-9:
                                in_domain = False
                        except Exception:
                            pass
                    if in_domain:
                        val = simplify(f.subs(s))
                        candidates.append((s, val, "Interior critical point"))
                        steps.append(r"\text{Point } " + _latex_point(s) + r",\quad f = " + latex(val))
            else:
                steps.append(r"\text{No interior critical points found.}")

            # Now check boundaries if ranges present
            if x_range and y_range:
                a, b = x_range
                c, d = y_range
                steps.append(r"\text{Checking boundaries on rectangle } " +
                             latex(a) + r"\le x \le " + latex(b) + r",\quad " +
                             latex(c) + r"\le y \le " + latex(d))
                # edges: x = a (vary y), x = b (vary y), y = c (vary x), y = d (vary x)
                edge_funcs = []
                # edge x=a
                fa = simplify(f.subs(x, a))
                fya = diff(fa, y)
                sol_y = solve(Eq(fya, 0), y)
                # include solutions within [c,d] plus endpoints c and d
                edge_points = []
                for yy in sol_y:
                    try:
                        if float(N(yy)) >= c - 1e-9 and float(N(yy)) <= d + 1e-9:
                            edge_points.append(yy)
                    except Exception:
                        pass
                edge_points += [c, d]
                for yy in set(edge_points):
                    pt = {x: a, y: simplify(yy)}
                    val = simplify(f.subs(pt))
                    candidates.append((pt, val, f"Boundary x={a}"))
                    steps.append(r"\text{Boundary point } " + _latex_point(pt) + r",\quad f = " + latex(val))

                # edge x=b
                fb = simplify(f.subs(x, b))
                fyb = diff(fb, y)
                sol_yb = solve(Eq(fyb, 0), y)
                edge_points = []
                for yy in sol_yb:
                    try:
                        if float(N(yy)) >= c - 1e-9 and float(N(yy)) <= d + 1e-9:
                            edge_points.append(yy)
                    except Exception:
                        pass
                edge_points += [c, d]
                for yy in set(edge_points):
                    pt = {x: b, y: simplify(yy)}
                    val = simplify(f.subs(pt))
                    candidates.append((pt, val, f"Boundary x={b}"))
                    steps.append(r"\text{Boundary point } " + _latex_point(pt) + r",\quad f = " + latex(val))

                # edge y=c
                fc = simplify(f.subs(y, c))
                fxc = diff(fc, x)
                sol_xc = solve(Eq(fxc, 0), x)
                edge_points = []
                for xx in sol_xc:
                    try:
                        if float(N(xx)) >= a - 1e-9 and float(N(xx)) <= b + 1e-9:
                            edge_points.append(xx)
                    except Exception:
                        pass
                edge_points += [a, b]
                for xx in set(edge_points):
                    pt = {x: simplify(xx), y: c}
                    val = simplify(f.subs(pt))
                    candidates.append((pt, val, f"Boundary y={c}"))
                    steps.append(r"\text{Boundary point } " + _latex_point(pt) + r",\quad f = " + latex(val))

                # edge y=d
                fd = simplify(f.subs(y, d))
                fxd = diff(fd, x)
                sol_xd = solve(Eq(fxd, 0), x)
                edge_points = []
                for xx in sol_xd:
                    try:
                        if float(N(xx)) >= a - 1e-9 and float(N(xx)) <= b + 1e-9:
                            edge_points.append(xx)
                    except Exception:
                        pass
                edge_points += [a, b]
                for xx in set(edge_points):
                    pt = {x: simplify(xx), y: d}
                    val = simplify(f.subs(pt))
                    candidates.append((pt, val, f"Boundary y={d}"))
                    steps.append(r"\text{Boundary point } " + _latex_point(pt) + r",\quad f = " + latex(val))
            else:
                steps.append(r"\text{No domain ranges fully specified for boundary checking. (Provide x range and y range.)}")

        else:
            return {"success": False, "error": f"Unknown problem type '{problem_type}'"}

        # produce final summary: list candidates with numeric values where possible
        if not candidates:
            steps.append(r"\text{No candidate points found.}")
            return {"success": True, "steps": steps, "candidates": [], "result": r"\text{No extrema found on given input.}", "input": latex(f), "constraint": constraint}

        # evaluate numeric approximations and determine global min/max if possible
        evaluated = []
        for (pt, val, note) in candidates:
            try:
                val_num = N(val)
            except Exception:
                val_num = val
            evaluated.append((pt, val, val_num, note))
        # find min and max among numeric ones
        numeric_vals = [(idx, ev[2]) for idx, ev in enumerate(evaluated) if hasattr(ev[2], 'is_real') or (not isinstance(ev[2], (str, type(None))) and str(ev[2]).replace(' ','').lstrip('-').replace('.', '').isdigit())]
        # try to convert to floats where possible
        best_min = None
        best_max = None
        try:
            # attempt float comparisons where possible
            numeric_eval_pairs = []
            for i, ev in enumerate(evaluated):
                try:
                    fl = float(N(ev[2]))
                    numeric_eval_pairs.append((i, fl))
                except Exception:
                    pass
            if numeric_eval_pairs:
                min_idx, min_val = min(numeric_eval_pairs, key=lambda t: t[1])
                max_idx, max_val = max(numeric_eval_pairs, key=lambda t: t[1])
                best_min = (evaluated[min_idx][0], evaluated[min_idx][1], min_val, evaluated[min_idx][3])
                best_max = (evaluated[max_idx][0], evaluated[max_idx][1], max_val, evaluated[max_idx][3])
        except Exception:
            pass

        # prepare candidate summary latex
        cand_list = []
        for pt, val, val_num, note in evaluated:
            cand_list.append({"point": _latex_point(pt), "value": latex(val), "value_approx": str(val_num), "note": note})

        result_summary = ""
        if best_min and best_max:
            result_summary = (r"\text{Absolute minimum (approx): } f\big(" + _latex_point(best_min[0]) +
                              r"\big) = " + latex(best_min[1]) + r" \approx " + latex(S(best_min[2])) + r" \\ " +
                              r"\text{Absolute maximum (approx): } f\big(" + _latex_point(best_max[0]) +
                              r"\big) = " + latex(best_max[1]) + r" \approx " + latex(S(best_max[2])))
        else:
            # fallback: list candidate points and values
            summary_lines = []
            for c in cand_list:
                summary_lines.append(r"f\left" + c["point"] + r"\right) = " + c["value"] + r" \quad (" + c["note"] + r")")
            result_summary = r"\\ ".join(summary_lines)

        return {
            "success": True,
            "steps": steps,
            "candidates": cand_list,
            "result": result_summary,
            "input": latex(f),
            "constraint": constraint
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
