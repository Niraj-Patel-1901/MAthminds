from sympy import Pow, Integer
from sympy.printing.str import StrPrinter

class PrettyPrinter(StrPrinter):
    def _print_Pow(self, expr):
        base, exp = expr.args
        if exp == 2 and isinstance(base, Integer):
            root = int(base**0.5)
            if root * root == base:
                return f"{root}^2"
        if exp == 2:
            return f"{self._print(base)}^2"
        return super()._print_Pow(expr)

def pretty(expr):
    return PrettyPrinter().doprint(expr)
