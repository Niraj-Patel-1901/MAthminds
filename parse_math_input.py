
# import re

# def parse_math_input(user_input):
#     expr = user_input.strip()

#     # Replace caret (^) with exponentiation (**)
#     expr = expr.replace("^", "**")

#     # Insert multiplication where missing (e.g. 2t -> 2*t)
#     expr = re.sub(r"(?<=[0-9])(?=[a-zA-Z(])", "*", expr)

#     # Fix missing multiplication between variables (e.g. at -> a*t)
#     expr = re.sub(r"(?<=[a-zA-Z)])(?=[a-zA-Z(])", "*", expr)

#     # Ensure function calls like sin(t) are preserved
#     expr = re.sub(r"(sin|cos|tan|exp|sinh|cosh|Heaviside|diff)\s*\(\s*([^)]*?)\s*\)", r"\1(\2)", expr)

#     return expr
import re

def parse_math_input(user_input):
    expr = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", user_input)
    expr = re.sub(r"([a-zA-Z])(\d)", r"\1*\2", expr)
    expr = expr.replace("^", "**")
    expr = re.sub(r"(sin|cos|tan|exp|sinh|cosh|diff)(?!\()", r"\1", expr)
    expr = re.sub(r"(sin|cos|tan|exp|sinh|cosh|diff)\s*([a-zA-Z0-9*+\-/^]+)", r"\1(\2)", expr)
    return expr

