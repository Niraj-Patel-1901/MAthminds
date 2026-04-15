from sympy import symbols, simplify, apart, latex, residue
from sympy.abc import z, n
from sympy import expand, Mul


def solve_inverse_z_transform(expression: str, method: str):
    steps = []

    try:
        Xz = simplify(expression)

        steps.append({
            "title": "Given Z-transform",
            "latex": rf"X(z) = {latex(Xz)}"
        })

        # ---------------- PARTIAL FRACTIONS ----------------
        if method == "partial":
            steps.append({
                "title": "Method Used",
                "latex": r"\text{Partial Fraction Method}"
            })

            Xz_pf = apart(Xz, z)

            steps.append({
                "title": "Partial Fraction Expansion",
                "latex": rf"X(z) = {latex(Xz_pf)}"
            })

            denom = Xz_pf.as_numer_denom()[1]
            poles = denom.as_poly(z).all_roots()

            x_n = 0
            for p in poles:
                x_n += residue(Xz_pf * z**(n-1), z, p)

        # ---------------- POWER SERIES ----------------
        elif method == "power":
            steps.append({
                "title": "Method Used",
                "latex": r"\text{Power Series Method}"
            })

            x_n = Xz.series(z, 0, 6).removeO()

        # ---------------- CONVOLUTION ----------------
        elif method == "convolution":
            steps.append({
                "title": "Method Used",
                "latex": r"\text{Convolution Method}"
            })

            factors = Xz.as_ordered_factors()

            if len(factors) != 2:
                return {
                    "success": False,
                    "error": "Convolution method requires product of two Z-transforms"
                }

            X1, X2 = factors

            steps.append({
                "title": "Factorization",
                "latex": rf"X(z) = ({latex(X1)})({latex(X2)})"
            })

            steps.append({
                "title": "Inverse Z-transform property",
                "latex": r"\mathcal{Z}^{-1}\{X_1(z)X_2(z)\} = x_1[n] * x_2[n]"
            })

            steps.append({
                "title": "Discrete Convolution Formula",
                "latex": r"x[n] = \sum_{k=0}^{n} x_1[k]x_2[n-k]"
            })

            x_n = r"x_1[n] * x_2[n]"

            return {
                "success": True,
                "steps": steps,
                "result": x_n
            }

        else:
            return {"success": False, "error": "Invalid method"}

        steps.append({
            "title": "Final Answer",
            "latex": rf"\boxed{{x[n] = {latex(x_n)}}}"
        })

        return {
            "success": True,
            "steps": steps,
            "result": latex(x_n)
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
