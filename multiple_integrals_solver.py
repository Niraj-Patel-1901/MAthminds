import matplotlib
matplotlib.use('Agg')
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import uuid
import os

# Symbols
x, y, z, r, theta, rho, phi = sp.symbols('x y z r theta rho phi')

# Plot folder
PLOT_FOLDER = "static/plots"
os.makedirs(PLOT_FOLDER, exist_ok=True)

# -----------------------------
# Utility: Save plot
# -----------------------------
def save_plot():
    fname = f"{uuid.uuid4().hex}.png"
    path = os.path.join(PLOT_FOLDER, fname)
    plt.savefig(path)
    plt.close()
    return "/static/plots/" + fname


# -----------------------------
# Rectangular region plot
# -----------------------------
def plot_rectangular(x1, x2, y1, y2):
    X = np.linspace(float(x1), float(x2), 300)
    plt.fill_between(X, float(y1), float(y2), alpha=0.3)
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Rectangular Region")
    return save_plot()


# -----------------------------
# Curved region plot
# -----------------------------
def plot_curved(x1, x2, ylow, yhigh):
    X = np.linspace(float(x1), float(x2), 400)
    y1 = np.ones_like(X) * float(ylow) if not hasattr(ylow, "free_symbols") else sp.lambdify(x, ylow)(X)

    y2 = np.ones_like(X) * float(yhigh) if not hasattr(yhigh, "free_symbols") else sp.lambdify(x, yhigh)(X)


    plt.plot(X, y1, 'r', label="Lower curve")
    plt.plot(X, y2, 'b', label="Upper curve")
    plt.fill_between(X, y1, y2, alpha=0.3)
    plt.legend()
    plt.title("Curved Region")
    return save_plot()


# -----------------------------
# Polar region plot (circle)
# -----------------------------
def plot_polar(expr_r, thetalim):
    theta_vals = np.linspace(
        float(sp.sympify(thetalim[0])),
        float(sp.sympify(thetalim[1])),
        500
    )

    r_expr = sp.sympify(expr_r)
    r_func = sp.lambdify(theta, r_expr, 'numpy')

    r_vals = r_func(theta_vals)

    x = r_vals * np.cos(theta_vals)
    y = r_vals * np.sin(theta_vals)

    plt.fill(x, y, alpha=0.3)
    plt.gca().set_aspect('equal')
    plt.title("Polar Region")

    fname = f"{uuid.uuid4().hex}.png"
    path = os.path.join(PLOT_FOLDER, fname)
    plt.savefig(path)
    plt.close()

    return "/static/plots/" + fname



# ===================================
# DOUBLE INTEGRALS
# ===================================

def double_rectangular(expr, xlim, ylim):
    f = sp.sympify(expr)
    steps = []

    I1 = sp.integrate(f, (x, xlim[0], xlim[1]))
    I2 = sp.integrate(I1, (y, ylim[0], ylim[1]))

    steps.append(r"\int_{%s}^{%s} %s\,dx = %s" %
                 (xlim[0], xlim[1], sp.latex(f), sp.latex(I1)))
    steps.append(r"\int_{%s}^{%s} %s\,dy = %s" %
                 (ylim[0], ylim[1], sp.latex(I1), sp.latex(I2)))

    plot = plot_rectangular(xlim[0], xlim[1], ylim[0], ylim[1])

    return {"result": sp.latex(I2), "steps": steps, "plot": plot}


def double_curved(expr, xlim, ylow, yhigh):
    f = sp.sympify(expr)
    y1 = sp.sympify(ylow)
    y2 = sp.sympify(yhigh)

    I1 = sp.integrate(f, (y, y1, y2))
    I2 = sp.integrate(I1, (x, xlim[0], xlim[1]))

    steps = [
        r"\int_{%s}^{%s} %s\,dy = %s" % (sp.latex(y1), sp.latex(y2), sp.latex(f), sp.latex(I1)),
        r"\int_{%s}^{%s} %s\,dx = %s" % (xlim[0], xlim[1], sp.latex(I1), sp.latex(I2))
    ]

    plot = plot_curved(xlim[0], xlim[1], y1, y2)

    return {"result": sp.latex(I2), "steps": steps, "plot": plot}


# ===================================
# POLAR DOUBLE INTEGRAL
# ===================================

def double_polar(expr, rlim, thetalim):
    f = sp.sympify(expr)
    fp = f.subs({x: r*sp.cos(theta), y: r*sp.sin(theta)}) * r

    I1 = sp.integrate(fp, (r, rlim[0], rlim[1]))
    I2 = sp.integrate(I1, (theta, thetalim[0], thetalim[1]))

    steps = [
        r"f(r,\theta) = %s" % sp.latex(fp),
        r"\int_{%s}^{%s} %s\,dr = %s" % (rlim[0], rlim[1], sp.latex(fp), sp.latex(I1)),
        r"\int_{%s}^{%s} %s\,d\theta = %s" % (thetalim[0], thetalim[1], sp.latex(I1), sp.latex(I2))
    ]

    plot = plot_polar(rlim[1], thetalim)

    return {"result": sp.latex(I2), "steps": steps, "plot": plot}


# ===================================
# AREA BETWEEN CURVES
# ===================================

def area_between(xlim, ylow, yhigh):
    y1 = sp.sympify(ylow)
    y2 = sp.sympify(yhigh)
    A = sp.integrate(y2 - y1, (x, xlim[0], xlim[1]))

    steps = [
        r"Area = \int_{%s}^{%s} (%s - %s)\,dx" %
        (xlim[0], xlim[1], sp.latex(y2), sp.latex(y1)),
        r"= %s" % sp.latex(A)
    ]

    plot = plot_curved(xlim[0], xlim[1], y1, y2)
    return {"result": sp.latex(A), "steps": steps, "plot": plot}


# ===================================
# TRIPLE INTEGRALS
# ===================================

def triple_cartesian(expr, xlim, ylim, zlim):
    f = sp.sympify(expr)
    I1 = sp.integrate(f, (x, xlim[0], xlim[1]))
    I2 = sp.integrate(I1, (y, ylim[0], ylim[1]))
    I3 = sp.integrate(I2, (z, zlim[0], zlim[1]))

    steps = [
        r"\int %s\,dx = %s" % (sp.latex(f), sp.latex(I1)),
        r"\int %s\,dy = %s" % (sp.latex(I1), sp.latex(I2)),
        r"\int %s\,dz = %s" % (sp.latex(I2), sp.latex(I3))
    ]

    return {"result": sp.latex(I3), "steps": steps}


def triple_cylindrical(expr, rlim, thetalim, zlim):
    f = sp.sympify(expr)
    fc = f.subs({x: r*sp.cos(theta), y: r*sp.sin(theta)}) * r

    I1 = sp.integrate(fc, (r, rlim[0], rlim[1]))
    I2 = sp.integrate(I1, (theta, thetalim[0], thetalim[1]))
    I3 = sp.integrate(I2, (z, zlim[0], zlim[1]))

    steps = [
        r"f = %s" % sp.latex(fc),
        r"\int %s\,dr = %s" % (sp.latex(fc), sp.latex(I1)),
        r"\int %s\,d\theta = %s" % (sp.latex(I1), sp.latex(I2)),
        r"\int %s\,dz = %s" % (sp.latex(I2), sp.latex(I3))
    ]

    return {"result": sp.latex(I3), "steps": steps}


def triple_spherical(expr, rlim, philim, thetalim):
    f = sp.sympify(expr)
    fs = f.subs({
        x: rho*sp.sin(phi)*sp.cos(theta),
        y: rho*sp.sin(phi)*sp.sin(theta),
        z: rho*sp.cos(phi)
    }) * rho**2 * sp.sin(phi)

    I1 = sp.integrate(fs, (rho, rlim[0], rlim[1]))
    I2 = sp.integrate(I1, (phi, philim[0], philim[1]))
    I3 = sp.integrate(I2, (theta, thetalim[0], thetalim[1]))

    steps = [
        r"f = %s" % sp.latex(fs),
        r"\int %s\,d\rho = %s" % (sp.latex(fs), sp.latex(I1)),
        r"\int %s\,d\phi = %s" % (sp.latex(I1), sp.latex(I2)),
        r"\int %s\,d\theta = %s" % (sp.latex(I2), sp.latex(I3))
    ]

    return {"result": sp.latex(I3), "steps": steps}


def change_order(expr, x_from, x_to, y_from, y_to):
    f = sp.sympify(expr)

    # Original integral:  ∫(y=y_from to y_to) ∫(x=x_from(y) to x_to) f dx dy
    x1 = sp.sympify(x_from)
    x2 = sp.sympify(x_to)

    # Region: x from 0 to x2, y from 0 to x
    y_lower = 0
    y_upper = x

    I1 = sp.integrate(f, (y, y_lower, y_upper))
    I2 = sp.integrate(I1, (x, 0, x2))

    steps = [
        r"\text{Original: } \int_{%s}^{%s} \int_{%s}^{%s} %s \, dx \, dy"
        % (sp.latex(y_from), sp.latex(y_to), sp.latex(x1), sp.latex(x2), sp.latex(f)),

        r"\text{Changed: } \int_0^{%s} \int_0^x %s \, dy \, dx"
        % (sp.latex(x2), sp.latex(f)),

        r"\int_0^x %s \, dy = %s"
        % (sp.latex(f), sp.latex(I1)),

        r"\int_0^{%s} %s \, dx = %s"
        % (sp.latex(x2), sp.latex(I1), sp.latex(I2))
    ]

    plot = plot_curved(0, x2, 0, x)

    return {"result": sp.latex(I2), "steps": steps, "plot": plot}
