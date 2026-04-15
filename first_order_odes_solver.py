# first_order_odes_solver.py

from sympy import (
    symbols,
    Function,
    Eq,
    Derivative,
    dsolve,
    sympify,
    latex
)
from sympy.core.sympify import SympifyError

x = symbols('x')
y = Function('y')


def normalize_equation(eq_str: str):
    """
    Converts common student input formats into SymPy format.
    """

    eq_str = eq_str.strip()
    eq_str = eq_str.replace("^", "**")

    # Replace dy/dx
    eq_str = eq_str.replace("dy/dx", "Derivative(y(x), x)")
    eq_str = eq_str.replace("y'", "Derivative(y(x), x)")

    # Replace standalone y with y(x)
    eq_str = eq_str.replace(" y ", " y(x) ")
    eq_str = eq_str.replace("+y", "+y(x)")
    eq_str = eq_str.replace("-y", "-y(x)")
    eq_str = eq_str.replace("*y", "*y(x)")
    eq_str = eq_str.replace("(y)", "(y(x))")

    return eq_str


def solve_first_order_ode(problem_type, equation_str, initial_condition_str=None):

    try:
        if "=" not in equation_str:
            return {"success": False, "error": "Equation must contain '='."}

        equation_str = normalize_equation(equation_str)

        left_str, right_str = equation_str.split("=", 1)

        left_expr = sympify(left_str)
        right_expr = sympify(right_str)

        eq = Eq(left_expr, right_expr)

        # Parse Initial Condition
        ics = None
        if initial_condition_str and "=" in initial_condition_str:
            try:
                left_ic, right_ic = initial_condition_str.split("=")
                left_ic = left_ic.strip()

                if "y(" in left_ic:
                    x0 = float(left_ic.replace("y(", "").replace(")", ""))
                    y0 = float(right_ic.strip())
                    ics = {y(x0): y0}
            except:
                ics = None

        # Solve
        sol = dsolve(eq, ics=ics)

        return {
            "success": True,
            "steps": [],  # empty steps (frontend safe)
            "result": latex(sol.rhs),
            "input": latex(eq)
        }

    except SympifyError:
        return {"success": False, "error": "Invalid mathematical expression."}
    except Exception as e:
        return {"success": False, "error": str(e)}
