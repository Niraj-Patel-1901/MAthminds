from sympy import symbols, Function, Eq, dsolve, Derivative, sympify, latex
from sympy.abc import x
import re

def preprocess_equation(equation: str) -> str:
    """
    Converts user input like "y'' + 2y' + 3y = 0"
    into valid SymPy syntax like:
    "Derivative(y(x),(x,2)) + 2*Derivative(y(x),x) + 3*y(x) = 0"
    Supports higher order derivatives y''', y'''' ...
    """

    # Normalize quotes
    eq = equation.replace("’", "'").replace("‘", "'").replace("`", "'")
    eq = eq.replace(" ", "")

    # Insert missing '*' between number and variable/function (e.g., 2x → 2*x)
    eq = re.sub(r'(\d)([a-zA-Z\(])', r'\1*\2', eq)

    # Insert '*' between variable and parentheses (e.g., x(y) → x*(y))
    eq = re.sub(r'([a-zA-Z])\(', r'\1*(', eq)

    # Replace higher-order derivatives: y''', y'''', etc.
    # Match y followed by n apostrophes
    def replace_deriv(match):
        primes = match.group(1)
        order = len(primes)
        return f"Derivative(y(x),(x,{order}))"

    eq = re.sub(r"y('+)", replace_deriv, eq)

    # Replace plain y with y(x) (but not if already y(x))
    eq = re.sub(r"\by(?!\()", "y(x)", eq)

    return eq


def solve_higher_order_de(problem_type: str, equation_str: str, ic1: str = "", ic2: str = ""):
    try:
        y = Function('y')

        # 🧠 Preprocess equation
        processed = preprocess_equation(equation_str)

        # 🧠 Create SymPy Eq
        if "=" in processed:
            left, right = processed.split("=")
            eq = Eq(sympify(left), sympify(right))
        else:
            eq = Eq(sympify(processed), 0)

        steps = [
            f"Original equation: {equation_str}",
            f"Converted to SymPy form: {processed}",
            "Solving using dsolve..."
        ]

        # 🧠 Solve DE
        sol = dsolve(eq)

        # 🧠 Apply initial conditions
        if ic1 or ic2:
            try:
                ics = {}
                for cond in [ic1, ic2]:
                    if cond and "=" in cond:
                        left, right = cond.split("=")
                        val = float(right)
                        left = left.strip().replace(" ", "")
                        if "y'" in left:
                            xval = float(left[left.find("(")+1:left.find(")")])
                            ics[y(x).diff(x).subs(x, xval)] = val
                        elif "y(" in left:
                            xval = float(left[left.find("(")+1:left.find(")")])
                            ics[y(x).subs(x, xval)] = val
                sol = dsolve(eq, ics=ics)
                steps.append("Applied initial conditions to find particular solution.")
            except Exception as e:
                steps.append(f"⚠️ Could not apply initial conditions: {str(e)}")

        return {
            "success": True,
            "payload": {
                "input": equation_str,
                "steps": steps,
                "result": latex(sol.rhs if hasattr(sol, "rhs") else sol)  # ✅ LaTeX for frontend
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
