from sympy import (
    symbols, sympify, sinh, cosh, tanh, asinh, acosh, atanh,
    log as sy_log, I, latex, simplify, Eq, expand, arg, Abs
)
from sympy.core.sympify import SympifyError

x = symbols('x')

# def _safe_sympify(user_input: str):
#     """
#     Convert user input to a SymPy expression safely:
#     - Accept 'i' or 'j' for imaginary unit, convert to 'I'
#     - Strip whitespace
#     """
#     if not isinstance(user_input, str):
#         raise ValueError("Input must be a string.")
#     s = user_input.strip()
#     s = s.replace('i', 'I')  # user may write 2+3i
#     s = s.replace('j', 'I')
#     # Avoid risky constructs - rely on sympy.sympify but catch errors
#     try:
#         expr = sympify(s)
#         return expr
#     except SympifyError as e:
#         raise ValueError(f"Could not parse expression: {user_input}") from e

def _safe_sympify(user_input: str):
    """
    Convert user input to a SymPy expression safely:
    - Accept 'i' or 'j' for imaginary unit, convert to 'I'
    - Strip whitespace
    - Handle simple forms like 2+3i or 2-3i
    """
    if not isinstance(user_input, str):
        raise ValueError("Input must be a string.")
    s = user_input.strip().lower()
    # replace i or j with I
    s = s.replace(' ', '').replace('i', '*I').replace('j', '*I')
    # fix double stars if user typed like 3*i
    s = s.replace('**I', '*I')
    # remove duplicate stars if any
    s = s.replace('**', '*')
    try:
        expr = sympify(s)
        return expr
    except SympifyError as e:
        raise ValueError(f"Could not parse expression: {user_input}") from e


def solve_hyperbolic(problem_type: str, input_value: str, func: str, param1=None, param2=None):
    """
    problem_type: 'hyperbolic', 'inverse', 'complex', 'properties'
    input_value: string representation of the input, e.g., 'x', '2', '2+3i'
    func: operation (frontend uses names like 'sinh', 'cosh', 'tanh', 'ln', 'sinh⁻¹', etc.)
    Returns: dict with keys: success(bool), steps(list of latex strings), result(latex)
    """
    try:
        expr = _safe_sympify(input_value)
    except Exception as e:
        return {"success": False, "error": str(e)}

    steps = []
    result_latex = ""
    try:
        if problem_type == "hyperbolic":
            if func == "sinh":
                steps.append(r"\text{Definition: } \sinh x = \frac{e^{x}-e^{-x}}{2}")
                substituted = sy_log  # placeholder avoid linter warning
                steps.append(r"\text{Substitute } x = " + latex(expr))
                res = sinh(expr)
                steps.append(r"\text{So } \sinh\left(" + latex(expr) + r"\right) = " + latex(res))
                result_latex = latex(res)
            elif func == "cosh":
                steps.append(r"\text{Definition: } \cosh x = \frac{e^{x}+e^{-x}}{2}")
                steps.append(r"\text{Substitute } x = " + latex(expr))
                res = cosh(expr)
                steps.append(r"\text{So } \cosh\left(" + latex(expr) + r"\right) = " + latex(res))
                result_latex = latex(res)
            elif func == "tanh":
                steps.append(r"\text{Definition: } \tanh x = \frac{\sinh x}{\cosh x}")
                steps.append(r"\text{Substitute } x = " + latex(expr))
                res = tanh(expr)
                steps.append(r"\text{So } \tanh\left(" + latex(expr) + r"\right) = " + latex(res))
                result_latex = latex(res)
            else:
                return {"success": False, "error": f"Unknown hyperbolic function '{func}'"}
        elif problem_type == "inverse":
            # Allow names like 'sinh⁻¹' or 'asinh' or 'sinh^-1'
            if func in ("sinh⁻¹", "asinh", "sinh^-1"):
                steps.append(r"\text{Formula: } \sinh^{-1} x = \ln\left(x + \sqrt{x^{2}+1}\right)")
                steps.append(r"\text{Substitute } x = " + latex(expr))
                res = asinh(expr)
                steps.append(r"\text{Therefore } \sinh^{-1}\left(" + latex(expr) + r"\right) = " + latex(res))
                result_latex = latex(res)
            elif func in ("cosh⁻¹", "acosh", "cosh^-1"):
                steps.append(r"\text{Formula: } \cosh^{-1} x = \ln\left(x + \sqrt{x^{2}-1}\right)")
                steps.append(r"\text{Substitute } x = " + latex(expr))
                res = acosh(expr)
                steps.append(r"\text{Therefore } \cosh^{-1}\left(" + latex(expr) + r"\right) = " + latex(res))
                result_latex = latex(res)
            elif func in ("tanh⁻¹", "atanh", "tanh^-1"):
                steps.append(r"\text{Formula: } \tanh^{-1} x = \frac{1}{2}\ln\left(\frac{1+x}{1-x}\right)")
                steps.append(r"\text{Substitute } x = " + latex(expr))
                res = atanh(expr)
                steps.append(r"\text{Therefore } \tanh^{-1}\left(" + latex(expr) + r"\right) = " + latex(res))
                result_latex = latex(res)
            else:
                return {"success": False, "error": f"Unknown inverse hyperbolic function '{func}'"}
        elif problem_type == "complex":
            # Only ln supported in your frontend for complex case
            if func == "ln":
                steps.append(r"\text{Complex logarithm: } \ln z = \ln|z| + i\arg(z)")
                steps.append(r"\text{Write } z = " + latex(expr))
                abs_part = Abs(expr)
                arg_part = arg(expr)
                principal_log = sy_log(expr)  # sympy returns principal branch
                steps.append(r"\text{Magnitude: } |z| = " + latex(abs_part))
                steps.append(r"\text{Argument (principal): } \arg(z) = " + latex(arg_part))
                steps.append(r"\text{Therefore } \ln(z) = " + latex(principal_log))
                result_latex = latex(principal_log)
            else:
                return {"success": False, "error": f"Unknown complex function '{func}'"}
        elif problem_type == "properties":
            # Evaluate/verify common hyperbolic identities symbolically
            if func == "sinh":
                # Example: show cosh^2 - sinh^2 = 1
                expr_identity = simplify(cosh(x) ** 2 - sinh(x) ** 2)
                steps.append(r"\text{Identity to verify: } \cosh^{2}x - \sinh^{2}x = 1")
                steps.append(r"\text{Compute } \cosh^{2}x - \sinh^{2}x")
                steps.append(r"\text{Result: } " + latex(expr_identity))
                result_latex = latex(expr_identity)
            elif func == "cosh":
                # show same identity
                expr_identity = simplify(cosh(x) ** 2 - sinh(x) ** 2)
                steps.append(r"\cosh^{2}x - \sinh^{2}x = " + latex(expr_identity))
                result_latex = latex(expr_identity)
            elif func == "tanh":
                expr_identity = simplify(1 - tanh(x) ** 2)
                steps.append(r"\text{Identity: } 1 - \tanh^{2}x = \operatorname{sech}^{2}x")
                steps.append(r"\text{Compute } 1 - \tanh^{2}x = " + latex(expr_identity))
                result_latex = latex(expr_identity)
            else:
                return {"success": False, "error": f"Unknown property selection '{func}'"}
        else:
            return {"success": False, "error": f"Unknown problem type '{problem_type}'"}

        return {"success": True, "steps": steps, "result": result_latex, "input": latex(expr)}
    except Exception as e:
        return {"success": False, "error": str(e)}