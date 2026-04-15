import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import io, base64

z = sp.symbols('z')

def parse(expr):
    return sp.sympify(expr.replace("^","**"))

def find_singularities(f):
    den = sp.denom(f)
    return sp.solve(den, z)


def cauchy_integral(f, a):
    steps = []
    steps.append(r"\oint \frac{f(z)}{z-a} dz = 2\pi i f(a)")
    val = f.subs(z, a)
    result = 2*sp.pi*sp.I*val
    steps.append(r"f("+sp.latex(a)+") = " + sp.latex(val))
    steps.append(r"\oint = 2\pi i \times " + sp.latex(val))
    return steps, sp.latex(result), None
def residue_solver(f, z0, R):
    steps = []
    poles = find_singularities(f)
    steps.append(r"\text{Singularities} = " + sp.latex(poles))

    inside = []
    for p in poles:
        if abs(complex(p)) < float(R):
            inside.append(p)

    steps.append(r"\text{Poles inside contour} = " + sp.latex(inside))

    total = 0
    for p in inside:
        r = sp.residue(f, z, p)
        steps.append(r"\text{Res}(f,"+sp.latex(p)+") = " + sp.latex(r))
        total += r

    I = sp.I
    result = 2*sp.pi*I*total
    steps.append(r"\oint f(z)dz = 2\pi i \sum Res = " + sp.latex(result))

    plot = contour_plot(inside, float(R))
    return steps, sp.latex(result), plot

def contour_plot(poles, R):
    t = np.linspace(0,2*np.pi,400)
    x = R*np.cos(t)
    y = R*np.sin(t)

    fig, ax = plt.subplots()
    ax.plot(x,y)
    for p in poles:
        ax.scatter(float(sp.re(p)), float(sp.im(p)), color='red')
        ax.text(float(sp.re(p)), float(sp.im(p)), str(p))

    ax.set_aspect('equal')
    ax.set_title("Contour and Poles")

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def series_solver(f, z0, n, mode):
    if mode=="taylor":
        s = sp.series(f, z, z0, int(n)).removeO()
        return [r"\text{Taylor series} = " + sp.latex(s)], sp.latex(s), None
    else:
        s = sp.series(f, z, z0, int(n)).removeO()
        return [r"\text{Laurent series} = " + sp.latex(s)], sp.latex(s), None

def singular_solver(f):
    poles = find_singularities(f)
    steps=[r"\text{Singularities} = " + sp.latex(poles)]
    for p in poles:
        ord = sp.order(f, z, p)
        steps.append(r"\text{Pole at } "+sp.latex(p)+" \text{ of order } "+sp.latex(ord))
    return steps, "Done", None
