import matplotlib
matplotlib.use("Agg")

import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import uuid
import os

# Symbols
x, theta, t = sp.symbols('x theta t')

# Plot folder
PLOT_FOLDER = "static/plots"
os.makedirs(PLOT_FOLDER, exist_ok=True)

# -------------------------
# Utility to save plots
# -------------------------
def save_plot():
    name = f"{uuid.uuid4().hex}.png"
    path = os.path.join(PLOT_FOLDER, name)
    plt.savefig(path)
    plt.close()
    return "/static/plots/" + name


# -------------------------
# Cartesian: y = f(x)
# -------------------------
def cartesian_arc_length(expr, a, b):
    f = sp.sympify(expr)
    dydx = sp.diff(f, x)

    integrand = sp.sqrt(1 + dydx**2)
    L = sp.simplify(sp.integrate(integrand, (x, a, b)))

    steps = [
        r"y = " + sp.latex(f),
        r"\frac{dy}{dx} = " + sp.latex(dydx),
        r"L = \int_{%s}^{%s} \sqrt{1+\left(\frac{dy}{dx}\right)^2} dx"
        % (a, b),
        r"= \int_{%s}^{%s} %s \, dx"
        % (a, b, sp.latex(integrand)),
        r"= " + sp.latex(sp.simplify(L))
    ]

    # Plot
    X = np.linspace(float(a), float(b), 400)
    f_func = sp.lambdify(x, f, "numpy")
    Y = f_func(X)

    plt.plot(X, Y)
    plt.title("y = " + expr)

    return {"result": sp.latex(L), "steps": steps, "plot": save_plot()}


# -------------------------
# Polar: r = f(theta)
# -------------------------
def polar_arc_length(expr, t1, t2):
    r = sp.sympify(expr)
    dr = sp.diff(r, theta)

    integrand = sp.sqrt(r**2 + dr**2)
    L = sp.simplify(sp.integrate(integrand, (theta, t1, t2)))

    steps = [
        r"r = " + sp.latex(r),
        r"\frac{dr}{d\theta} = " + sp.latex(dr),
        r"L = \int_{%s}^{%s} \sqrt{r^2+\left(\frac{dr}{d\theta}\right)^2} d\theta"
        % (t1, t2),
        r"= \int_{%s}^{%s} %s \, d\theta"
        % (t1, t2, sp.latex(integrand)),
        r"= " + sp.latex(sp.simplify(L))
    ]

    # Plot polar curve
    T = np.linspace(float(sp.sympify(t1)), float(sp.sympify(t2)), 400)
    r_func = sp.lambdify(theta, r, "numpy")
    R = r_func(T)

    X = R * np.cos(T)
    Y = R * np.sin(T)

    plt.plot(X, Y)
    plt.gca().set_aspect('equal')
    plt.title("r = " + expr)

    return {"result": sp.latex(L), "steps": steps, "plot": save_plot()}
