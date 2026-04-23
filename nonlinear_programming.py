from flask import Blueprint, request, jsonify
import sympy as sp
import re

bp = Blueprint("nonlinear_programming_bp", __name__)

def parse_objective(obj_str):
    obj_str = obj_str.strip().lower()
    is_max = False
    if obj_str.startswith("max"):
        is_max = True
        obj_str = obj_str[3:].strip()
    elif obj_str.startswith("min"):
        obj_str = obj_str[3:].strip()
    
    obj_str = obj_str.replace('^', '**')
    
    # Extract variable name like "Z = "
    if "=" in obj_str:
        parts = obj_str.split("=")
        obj_str = parts[-1].strip()
        
    return is_max, sp.sympify(obj_str)

def parse_constraint(c_str):
    c_str = c_str.strip().replace('^', '**')
    if "<=" in c_str or "≤" in c_str:
        left, right = re.split(r'<=|≤', c_str)
        # left <= right => left - right <= 0
        return sp.sympify(left) - sp.sympify(right), "<="
    elif ">=" in c_str or "≥" in c_str:
        left, right = re.split(r'>=|≥', c_str)
        # left >= right => right - left <= 0
        return sp.sympify(right) - sp.sympify(left), "<="
    elif "=" in c_str:
        left, right = c_str.split("=")
        # left = right => left - right = 0
        return sp.sympify(left) - sp.sympify(right), "="
    else:
        # assume it's an expression meant to be <= 0
        return sp.sympify(c_str), "<="

@bp.route("/api/nonlinear", methods=["POST"])
def solve_nlp():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid JSON: {e}"}), 400

    prob_type = data.get("problemType", "kuhn")
    obj_input = data.get("objective", "")
    cons_input = data.get("constraints", "")
    
    if not obj_input:
        return jsonify({"success": False, "error": "Objective function is required."}), 400
        
    steps_latex = []
    
    try:
        is_max, f = parse_objective(obj_input)
        
        # Standardize to minimization
        f_standard = -f if is_max else f
        
        steps_latex.append(r"\textbf{Objective Function:}")
        obj_type = "Maximize" if is_max else "Minimize"
        steps_latex.append(rf"\text{{{obj_type}}} \quad f = {sp.latex(f)}")
        
        if is_max:
            steps_latex.append(rf"\text{{Convert to minimize:}} \quad f' = -f = {sp.latex(f_standard)}")
        
        # Parse constraints
        raw_constraints = [c for c in cons_input.split('\n') if c.strip()]
        g_funcs = [] # inequality <= 0
        h_funcs = [] # equality = 0
        
        if raw_constraints:
            steps_latex.append(r"\textbf{Constraints (Standardized to } \le 0 \text{ or } = 0 \textbf{):}")
            for rc in raw_constraints:
                expr, ctype = parse_constraint(rc)
                if ctype == "<=":
                    g_funcs.append(expr)
                    steps_latex.append(rf"g(x): \quad {sp.latex(expr)} \le 0")
                else:
                    h_funcs.append(expr)
                    steps_latex.append(rf"h(x): \quad {sp.latex(expr)} = 0")
        
        # Extract variables
        vars_set = f.free_symbols
        for g in g_funcs: vars_set.update(g.free_symbols)
        for h in h_funcs: vars_set.update(h.free_symbols)
        variables = sorted(list(vars_set), key=lambda x: x.name)
        
        if prob_type == "kuhn":
            steps_latex.append(r"\hr")
            steps_latex.append(r"\textbf{Kuhn-Tucker (KKT) Formulation}")
            
            lambdas = [sp.symbols(f'\\lambda_{i+1}', real=True) for i in range(len(g_funcs))]
            mus = [sp.symbols(f'\\mu_{i+1}', real=True) for i in range(len(h_funcs))]
            
            L = f_standard
            for l, g in zip(lambdas, g_funcs):
                L += l * g
            for m, h in zip(mus, h_funcs):
                L += m * h
                
            steps_latex.append(r"\textbf{Lagrangian: } L = f(X) + \sum \lambda_i g_i(X) + \sum \mu_j h_j(X)")
            steps_latex.append(rf"L = {sp.latex(L)}")
            
            steps_latex.append(r"\textbf{KKT Conditions:}")
            
            eqs = []
            
            # 1. Gradient of L = 0
            for v in variables:
                dL_dv = sp.diff(L, v)
                eqs.append(dL_dv)
                steps_latex.append(rf"\frac{{\partial L}}{{\partial {v.name}}} = {sp.latex(dL_dv)} = 0")
                
            # 2. Complementary Slackness
            for l, g in zip(lambdas, g_funcs):
                eqs.append(l * g)
                steps_latex.append(rf"\lambda \cdot g: \quad {sp.latex(l)} \left( {sp.latex(g)} \right) = 0")
                
            # 3. Equality constraints
            for h in h_funcs:
                eqs.append(h)
                steps_latex.append(rf"h(x): \quad {sp.latex(h)} = 0")
                
            steps_latex.append(r"\textbf{Primal & Dual Feasibility:}")
            steps_latex.append(r"g_i(X) \le 0, \quad \lambda_i \ge 0")
            
            # Solve the system
            solve_vars = variables + lambdas + mus
            steps_latex.append(r"\text{Solving the system of equations...}")
            
            try:
                solutions = sp.solve(eqs, solve_vars, dict=True)
                
                valid_solutions = []
                for sol in solutions:
                    # check feasibility
                    is_valid = True
                    for l in lambdas:
                        l_val = sol.get(l, 0)
                        try:
                            if float(l_val) < -1e-6:
                                is_valid = False
                        except:
                            pass
                            
                    for g in g_funcs:
                        g_val = g.subs(sol)
                        try:
                            if float(g_val) > 1e-6:
                                is_valid = False
                        except:
                            pass
                            
                    if is_valid:
                        valid_solutions.append(sol)
                        
                if valid_solutions:
                    steps_latex.append(r"\textbf{Feasible KKT Points Found:}")
                    best_f = float('inf')
                    best_sol = None
                    
                    for idx, sol in enumerate(valid_solutions):
                        sol_str = ", ".join([rf"{sp.latex(k)} = {sp.latex(v)}" for k, v in sol.items() if k in variables])
                        val_f = f.subs(sol)
                        val_f_eval = float(val_f)
                        
                        steps_latex.append(rf"\text{{Point }} {idx+1}: \quad {sol_str} \implies f = {sp.latex(val_f)}")
                        
                        if is_max:
                            if val_f_eval < best_f: # wait, for max we want highest f, but best_f logic below is inverted.
                                pass
                            
                        # Correct min/max logic
                        if (is_max and val_f_eval > best_f if best_f != float('inf') else True) or \
                           (not is_max and val_f_eval < best_f):
                            best_f = val_f_eval
                            best_sol = (sol_str, val_f)
                            
                    steps_latex.append(r"\textbf{Optimal Solution:}")
                    steps_latex.append(rf"{best_sol[0]} \implies \text{{Optimal Value }} = {sp.latex(best_sol[1])}")
                else:
                    steps_latex.append(r"\text{No valid points found satisfying all KKT conditions.}")
                    
            except Exception as e:
                steps_latex.append(rf"\text{{Equation solving encountered complexity or error: }} {e}")
                
        elif prob_type == "penalty":
            steps_latex.append(r"\hr")
            steps_latex.append(r"\textbf{Penalty Method Formulation}")
            
            r = sp.symbols('r', positive=True)
            
            P = f_standard
            penalty_terms = []
            for g in g_funcs:
                # Penalty is r * max(0, g)^2
                # We show the formal expression
                term = rf"\left( \max(0, {sp.latex(g)}) \right)^2"
                penalty_terms.append(term)
                
            for h in h_funcs:
                term = rf"\left( {sp.latex(h)} \right)^2"
                penalty_terms.append(term)
                
            P_latex = sp.latex(f_standard) + " + r \\sum " + " + r \\sum ".join(penalty_terms) if penalty_terms else sp.latex(f_standard)
            
            steps_latex.append(r"\textbf{Penalty Function: } P(X, r) = f(X) + r \sum (\max(0, g_i(X)))^2 + r \sum h_j(X)^2")
            steps_latex.append(rf"P(X, r) = {P_latex}")
            
            steps_latex.append(r"\text{The optimal solution is found by minimizing } P(X, r) \text{ and taking the limit as } r \to \infty.")
            steps_latex.append(r"\text{Note: Symbolic limits for multidimensional piecewise penalties are highly complex. Formulated above.}")
            
        else:
            steps_latex.append(r"\text{Method not fully implemented for symbolic steps yet.}")
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
        
    return jsonify({
        "success": True,
        "steps_latex": steps_latex
    })
