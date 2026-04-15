import sympy as sp

x, y = sp.symbols('x y', real=True)
z = sp.symbols('z')
i = sp.I

def parse_fz(fz):
    return sp.sympify(fz.replace("^","**"))

def get_u_v(fz):
    f = parse_fz(fz).subs(z, x + i*y)
    u = sp.re(f)
    v = sp.im(f)
    return u, v

def analytic_check(fz):
    u, v = get_u_v(fz)
    ux = sp.diff(u, x)
    uy = sp.diff(u, y)
    vx = sp.diff(v, x)
    vy = sp.diff(v, y)

    steps = [
        r"u = " + sp.latex(u),
        r"v = " + sp.latex(v),
        r"u_x = " + sp.latex(ux),
        r"u_y = " + sp.latex(uy),
        r"v_x = " + sp.latex(vx),
        r"v_y = " + sp.latex(vy)
    ]

    cr1 = sp.simplify(ux - vy)
    cr2 = sp.simplify(uy + vx)

    if cr1 == 0 and cr2 == 0:
        steps.append("Cauchy–Riemann equations satisfied ⇒ Analytic")
        result = "Analytic"
    else:
        steps.append("Cauchy–Riemann equations not satisfied ⇒ Not analytic")
        result = "Not Analytic"

    return steps, result

def complex_derivative(fz, z0):
    f = parse_fz(fz)
    df = sp.diff(f, z)
    val = df.subs(z, sp.sympify(z0.replace("i","I")))
    return [r"f'(z) = " + sp.latex(df)], sp.latex(val)

def power_series(fz, z0, n):
    f = parse_fz(fz)
    z0 = sp.sympify(z0.replace("i","I"))
    series = sp.series(f, z, z0, int(n)).removeO()
    return [r"Taylor series about z_0 = " + sp.latex(z0)], sp.latex(series)

def conformal_map(fz, z0):
    f = parse_fz(fz.replace("w=",""))
    z0 = sp.sympify(z0.replace("i","I"))
    w = f.subs(z, z0)
    return [r"w = f(z) = " + sp.latex(f)], sp.latex(w)
def milne_thomson(u_expr, v_expr):
    u = sp.sympify(u_expr.replace("^","**"))
    v = sp.sympify(v_expr.replace("^","**"))

    ux = sp.diff(u, x)
    uy = sp.diff(u, y)
    vx = sp.diff(v, x)
    vy = sp.diff(v, y)

    steps = [
        r"u(x,y) = " + sp.latex(u),
        r"v(x,y) = " + sp.latex(v),
        r"u_x = " + sp.latex(ux),
        r"u_y = " + sp.latex(uy),
        r"v_x = " + sp.latex(vx),
        r"v_y = " + sp.latex(vy)
    ]

    # Cauchy–Riemann check
    if sp.simplify(ux - vy) != 0 or sp.simplify(uy + vx) != 0:
        return steps, "Cauchy–Riemann equations NOT satisfied ⇒ Not analytic"

    steps.append("Cauchy–Riemann equations satisfied ⇒ Analytic")

    # Construct f(z) correctly
    fxy = u + sp.I*v
    z = sp.symbols("z")
    fz = fxy.subs({x: z, y: 0})
    fz = sp.simplify(fz)

    fprime = sp.diff(fz, z)

    steps.append(r"f(x,y) = u + iv = " + sp.latex(fxy))
    steps.append(r"Substitute y=0, x=z ⇒ f(z) = " + sp.latex(fz))
    steps.append(r"f'(z) = " + sp.latex(fprime))

    return steps, sp.latex(fz)
