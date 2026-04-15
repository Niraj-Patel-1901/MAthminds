# probability_api.py
from flask import Blueprint, request, jsonify
import sympy as sp
from sympy import symbols, binomial, latex, sqrt
from math import comb
import math

probability_bp = Blueprint("probability", __name__, url_prefix="/probability")

# ----------------- helpers -----------------
def _ok(payload):
    return jsonify({"ok": True, **payload})

def _err(msg):
    return jsonify({"ok": False, "error": str(msg)}), 400

def _boxed(expr):
    try:
        return r"\boxed{" + latex(sp.simplify(expr)) + "}"
    except Exception:
        return r"\boxed{" + latex(expr) + "}"

def _num(x, d=8):
    try:
        return sp.N(x, d)
    except Exception:
        return x

def _list_terms_sum(terms, max_show=6, digits=6):
    """Return (latex_short, latex_each, numeric_sum)."""
    shown = terms[:max_show]
    short = " + ".join(latex(t) for t in shown)
    if len(terms) > max_show:
        short += " + \\cdots"
    each = []
    total = 0.0
    for idx, t in enumerate(terms, 1):
        tn = _num(t, digits)
        each.append(rf"Term\,{idx}: \; {latex(t)} \; \approx \; {latex(tn)}")
        total += float(sp.N(tn))
    return short, each, total

# ----------------- MGF -----------------
@probability_bp.route("/mgf", methods=["POST"])
def mgf_route():
    data = request.get_json(force=True)
    dist = (data or {}).get("distribution", "").lower()
    params = (data or {}).get("params", {}) or {}
    t = symbols("t")

    if dist == "binomial":
        n_val = params.get("n", "n")
        p_val = params.get("p", "p")
        n_sym = symbols(str(n_val)) if not str(n_val).isdigit() else int(n_val)
        p_sym = sp.sympify(p_val)
        M = (1 - p_sym + p_sym*sp.exp(t))**n_sym
        steps = [
            r"\textbf{Given } X \sim \mathrm{Binomial}(n,p)",
            r"M_X(t)=E[e^{tX}] = \sum_{k=0}^{n} e^{tk}\binom{n}{k}p^{k}(1-p)^{n-k}",
            r"= (1-p + pe^{t})^{n} \; \text{(binomial theorem)}",
            rf"\textbf{Substitute } n={latex(n_sym)},\; p={latex(p_sym)}"
        ]
        return _ok({"distribution":"Binomial(n,p)", "result_latex": _boxed(M), "steps_latex": steps})

    if dist == "poisson":
        lam = sp.sympify(params.get("lam", "lambda"))
        M = sp.exp(lam*(sp.exp(t)-1))
        steps = [
            r"\textbf{Given } X \sim \mathrm{Poisson}(\lambda)",
            r"M_X(t) = \exp\!\left(\lambda(e^{t}-1)\right)",
            rf"\textbf{Substitute } \lambda={latex(lam)}"
        ]
        return _ok({"distribution":"Poisson(λ)", "result_latex": _boxed(M), "steps_latex": steps})

    if dist == "normal":
        mu = sp.sympify(params.get("mu", "mu"))
        sigma = sp.sympify(params.get("sigma", "sigma"))
        M = sp.exp(mu*t + (sigma**2)*t**2/2)
        steps = [
            r"\textbf{Given } X \sim \mathcal{N}(\mu,\sigma^2)",
            r"M_X(t)=\exp\!\left(\mu t + \tfrac{1}{2}\sigma^2 t^2\right)",
            rf"\textbf{Substitute } \mu={latex(mu)},\; \sigma={latex(sigma)}"
        ]
        return _ok({"distribution":"Normal(μ,σ^2)", "result_latex": _boxed(M), "steps_latex": steps})

    if dist == "exponential":
        lam = sp.sympify(params.get("lam", "lambda"))
        M = lam/(lam - t)
        steps = [
            r"\textbf{Given } X \sim \mathrm{Exponential}(\lambda)",
            r"M_X(t)=\dfrac{\lambda}{\lambda - t},\; t<\lambda",
            rf"\textbf{Substitute } \lambda={latex(lam)}"
        ]
        return _ok({"distribution":"Exponential(λ)", "result_latex": _boxed(M), "steps_latex": steps})

    return _err("Unsupported distribution for MGF.")

# --------------- Raw moments ---------------
@probability_bp.route("/raw_moment", methods=["POST"])
def raw_moment_route():
    data = request.get_json(force=True)
    dist = (data or {}).get("distribution", "").lower()
    params = (data or {}).get("params", {}) or {}
    r = (data or {}).get("n", None)

    if r is None:
        return _err("Missing moment order 'n'.")
    try:
        r_int = int(r)
    except Exception:
        return _err("'n' must be an integer non-negative.")

    k = symbols("k", integer=True, nonnegative=True)
    steps = []

    if dist == "binomial":
        Nparam = params.get("n", "n")
        p = sp.sympify(params.get("p", "p"))
        Nsym = symbols(str(Nparam)) if not str(Nparam).isdigit() else int(Nparam)
        pmf = binomial(Nsym, k) * p**k * (1-p)**(Nsym-k)
        steps.append(rf"\textbf{{Given }} X\sim Bin(n,p),\; P(X=k)=\binom{{n}}{{k}}p^k(1-p)^{{n-k}}")
        steps.append(rf"E[X^{r_int}] = \sum_{{k=0}}^{{n}} k^{r_int} \binom{{n}}{{k}} p^k (1-p)^{{n-k}}")
        steps.append(rf"\textbf{{Substitute }} n={latex(Nsym)},\; p={latex(p)}")
        if isinstance(Nsym, int):
            expr = sp.summation(k**r_int * pmf, (k, 0, Nsym))
            terms = [ (i**r_int) * sp.binomial(Nsym,i) * p**i * (1-p)**(Nsym-i) for i in range(0, Nsym+1) ]
            short, each, total = _list_terms_sum(terms, max_show=6)
            steps.append(r"Expanded (first terms): " + short)
            steps.extend(each[:6])
            steps.append(rf"Numeric sum \approx {total:.6f}")
            return _ok({"distribution":"Binomial", "result_latex": _boxed(expr), "steps_latex": steps})
        else:
            return _ok({"distribution":"Binomial",
                        "result_latex": r"\displaystyle \sum_{k=0}^{n} k^{%d}\binom{n}{k}p^k(1-p)^{n-k}"%r_int,
                        "steps_latex": steps})

    if dist == "poisson":
        lam = sp.sympify(params.get("lam", "lambda"))
        steps.append(rf"\textbf{{Given }} X\sim Poisson(\lambda)")
        steps.append(r"E[X^" + str(r_int) + r"] = \sum_{k=0}^\infty k^" + str(r_int) + r" \frac{\lambda^k e^{-\lambda}}{k!}")



        steps.append(rf"\textbf{{Substitute }} \lambda={latex(lam)}")
        k = symbols("k", integer=True, nonnegative=True)
        try:
            expr = sp.summation(sp.functions.combinatorial.numbers.stirling2(r_int, k) * lam**k, (k, 0, r_int))
            steps.append(r"= \displaystyle \sum_{k=0}^{%d} S(%d,k)\lambda^{k} \quad \text{(Touchard polynomial)}"%(r_int, r_int))
        except Exception:
            i = symbols("i", integer=True, nonnegative=True)
        pmf = sp.exp(-lam) * lam**i / sp.factorial(i)
        expr = sp.summation(i**r_int * pmf, (i, 0, 60))
        steps.append(rf"Resulting closed form: {latex(expr)}")
        steps.append(rf"Numeric value \approx {latex(_num(expr, 8))}")
        return _ok({"distribution":"Poisson", "result_latex": _boxed(expr), "steps_latex": steps})

    if dist == "normal":
        mu = sp.sympify(params.get("mu", "mu"))
        sigma = sp.sympify(params.get("sigma", "sigma"))
        steps.append(rf"\textbf{{Given }} X\sim \mathcal{{N}}(\mu,\sigma^2)")
        steps.append(rf"E[X^{r_int}] = \sum_{{k=0}}^{{\lfloor {r_int}/2\rfloor}} \frac{{{r_int}!}}{{2^k k! ({r_int}-2k)!}} \mu^{{{r_int}-2k}} (\sigma^2)^k")
        s = 0
        for kk in range(0, (r_int//2) + 1):
            term = sp.factorial(r_int) / (2**kk * sp.factorial(kk) * sp.factorial(r_int-2*kk))
            term = term * mu**(r_int-2*kk) * (sigma**2)**kk
            s += term
            steps.append(rf"Term {kk+1}: {latex(term)}")
        steps.append(rf"Sum = {latex(s)}")
        steps.append(rf"Numeric value \approx {latex(_num(s))}")
        return _ok({"distribution":"Normal", "result_latex": _boxed(s), "steps_latex": steps})

    if dist == "exponential":
        lam = sp.sympify(params.get("lam", "lambda"))
        expr = sp.factorial(r_int) / (lam**r_int)
        steps.append(rf"\textbf{{Given }} X\sim Exp(\lambda)")
        steps.append(rf"E[X^{r_int}] = \frac{{{r_int}!}}{{\lambda^{ {r_int} }}}")
        steps.append(rf"\textbf{{Substitute }} \lambda={latex(lam)} \Rightarrow {latex(expr)}")
        steps.append(rf"Numeric value \approx {latex(_num(expr))}")
        return _ok({"distribution":"Exponential", "result_latex": _boxed(expr), "steps_latex": steps})

    return _err("Unsupported distribution for raw moments.")

# --------------- Event probabilities ---------------
@probability_bp.route("/event", methods=["POST"])
def event_route():
    data = request.get_json(force=True)
    dist = (data or {}).get("distribution", "").lower()
    params = (data or {}).get("params", {}) or {}
    cond = (data or {}).get("condition", {}) or {}
    cond_type = cond.get("type")
    value = cond.get("value")

    if cond_type is None or value is None:
        return _err("Condition must include 'type' and 'value'")

    # ---- Binomial ----
    if dist == "binomial":
        N = int(params.get("n", 0))
        p = sp.N(params.get("p", 0))
        i = symbols("i", integer=True, nonnegative=True)
        pmf = binomial(N, i) * p**i * (1-p)**(N-i)
        steps = [r"\textbf{Binomial PMF: } P(X=k)=\binom{n}{k}p^k(1-p)^{n-k}",
                 rf"\textbf{{Substitute }} n={N},\; p={latex(p)}"]

        if cond_type == "eq":
            k = int(value)
            prob = sp.simplify(pmf.subs(i, k))
            steps.append(rf"P(X={k}) = \binom{{{N}}}{{{k}}}{latex(p)}^{k}(1-{latex(p)})^{{{N-k}}}")
            steps.append(rf"= {latex(prob)}")
            steps.append(rf"Numeric value \approx {latex(_num(prob))}")
            return _ok({"result_latex": _boxed(prob), "steps_latex": steps})

        def _sum_terms(a, b):
            terms = [ sp.binomial(N,j)*p**j*(1-p)**(N-j) for j in range(a, b+1) ]
            S = sum(terms)
            short, each, total = _list_terms_sum(terms, max_show=6)
            return S, short, each, total

        if cond_type == "leq":
            k = int(value)
            S, short, each, total = _sum_terms(0, k)
            steps.append(rf"P(X \le {k}) = \sum_{{i=0}}^{{{k}}} \binom{{{N}}}{{i}} p^{i} (1-p)^{{{N}-i}}")
            steps.append("Expanded (first terms): " + short)
            steps.extend(each[:6])
            steps.append(rf"Numeric sum \approx {total:.6f}")
            return _ok({"result_latex": _boxed(S), "steps_latex": steps})

        if cond_type == "geq":
            k = int(value)
            S, short, each, total = _sum_terms(k, N)
            steps.append(rf"P(X \ge {k}) = \sum_{{i={k}}}^{{{N}}} \binom{{{N}}}{{i}} p^{i} (1-p)^{{{N}-i}}")
            steps.append("Expanded (first terms): " + short)
            steps.extend(each[:6])
            steps.append(rf"Numeric sum \approx {total:.6f}")
            return _ok({"result_latex": _boxed(S), "steps_latex": steps})

        if cond_type == "interval":
            a, b = map(int, value)
            S, short, each, total = _sum_terms(a, b)
            steps.append(rf"P({a} \le X \le {b}) = \sum_{{i={a}}}^{{{b}}} \binom{{{N}}}{{i}} p^{i} (1-p)^{{{N}-i}}")
            steps.append("Expanded (first terms): " + short)
            steps.extend(each[:6])
            steps.append(rf"Numeric sum \approx {total:.6f}")
            return _ok({"result_latex": _boxed(S), "steps_latex": steps})

        return _err("Unknown condition for binomial.")

    # ---- Poisson ----
    if dist == "poisson":
        lam = sp.N(params.get("lam", 1))
        i = symbols("i", integer=True, nonnegative=True)
        pmf = sp.exp(-lam) * lam**i / sp.factorial(i)
        steps = [r"\textbf{Poisson PMF: } P(X=k)=\dfrac{\lambda^k e^{-\lambda}}{k!}",
                 rf"\textbf{{Substitute }} \lambda={latex(lam)}"]

        if cond_type == "eq":
            k = int(value)
            prob = sp.simplify(pmf.subs(i, k))
            steps.append(rf"P(X={k}) = {latex(prob)}")
            steps.append(rf"Numeric value \approx {latex(_num(prob))}")
            return _ok({"result_latex": _boxed(prob), "steps_latex": steps})

        def _sum_terms(a, b):
            terms = [ sp.exp(-lam) * lam**j / sp.factorial(j) for j in range(a, b+1) ]
            S = sum(terms)
            short, each, total = _list_terms_sum(terms, max_show=8)
            return S, short, each, total

        if cond_type == "leq":
            k = int(value)
            S, short, each, total = _sum_terms(0, k)
            steps.append(rf"P(X \le {k}) = \sum_{{i=0}}^{{{k}}} \frac{{\lambda^{i} e^{{-\lambda}}}}{{i!}}")
            steps.append("Expanded (first terms): " + short)
            steps.extend(each[:8])
            steps.append(rf"Numeric sum \approx {total:.6f}")
            return _ok({"result_latex": _boxed(S), "steps_latex": steps})

        if cond_type == "geq":
            k = int(value)
            Scomp, short, each, total = _sum_terms(0, k-1)
            steps.append(rf"P(X \ge {k}) = 1 - \sum_{{i=0}}^{{{k-1}}} \frac{{\lambda^{i} e^{{-\lambda}}}}{{i!}}")
            steps.append("Complement (first terms): " + short)
            steps.extend(each[:8])
            steps.append(rf"Complement numeric \approx {total:.6f}")
            val = 1 - total
            return _ok({"result_latex": _boxed(1 - Scomp), "steps_latex": steps + [rf"P(X\ge {k}) \approx {val:.6f}"]})

        if cond_type == "interval":
            a, b = map(int, value)
            S, short, each, total = _sum_terms(a, b)
            steps.append(rf"P({a} \le X \le {b}) = \sum_{{i={a}}}^{{{b}}} \frac{{\lambda^{i} e^{{-\lambda}}}}{{i!}}")
            steps.append("Expanded (first terms): " + short)
            steps.extend(each[:8])
            steps.append(rf"Numeric sum \approx {total:.6f}")
            return _ok({"result_latex": _boxed(S), "steps_latex": steps})

        return _err("Unknown condition for Poisson.")

    # ---- Normal ----
    if dist == "normal":
        mu = sp.sympify(params.get("mu", 0))
        sigma = sp.sympify(params.get("sigma", 1))
        steps = [r"\textbf{Normal CDF: } \Phi(z) = \tfrac{1}{2}\left(1+\operatorname{erf}\!\left(\tfrac{z}{\sqrt{2}}\right)\right)",
                 rf"\textbf{{Parameters}}: \mu={latex(mu)},\; \sigma={latex(sigma)}"]

        def Phi(xval):
            z = (sp.sympify(xval) - mu) / (sigma*sp.sqrt(2))
            return sp.Rational(1,2) * (1 + sp.erf(z)), z

        if cond_type == "eq":
            xval = sp.sympify(value)
            steps.append(rf"P(X = {latex(xval)}) = 0 \; \text{{(continuous)}}")
            return _ok({"result_latex": r"\boxed{0}", "steps_latex": steps})

        if cond_type == "leq":
            x = value
            expr, z = Phi(x)
            steps.append(rf"z=\frac{{{x}-{latex(mu)}}}{{{latex(sigma)}\sqrt{{2}}}} = {latex(sp.simplify(z))}")
            steps.append(rf"P(X \le {x}) = \Phi\!\left(\frac{{{x}-\mu}}{{\sigma}}\right) = {latex(expr)}")
            steps.append(rf"Numeric value \approx {latex(_num(expr))}")
            return _ok({"result_latex": _boxed(expr), "steps_latex": steps})

        if cond_type == "geq":
            x = value
            expr, z = Phi(x)
            steps.append(rf"z=\frac{{{x}-{latex(mu)}}}{{{latex(sigma)}\sqrt{{2}}}} = {latex(sp.simplify(z))}")
            steps.append(rf"P(X \ge {x}) = 1-\Phi\!\left(\frac{{{x}-\mu}}{{\sigma}}\right) = {latex(1-expr)}")
            steps.append(rf"Numeric value \approx {latex(_num(1-expr))}")
            return _ok({"result_latex": _boxed(1-expr), "steps_latex": steps})

        if cond_type == "interval":
            a, b = value
            expr_b, zb = Phi(b); expr_a, za = Phi(a)
            expr = expr_b - expr_a
            steps.append(rf"z_a=\frac{{{a}-{latex(mu)}}}{{{latex(sigma)}\sqrt{{2}}}}={latex(sp.simplify(za))},\; z_b=\frac{{{b}-{latex(mu)}}}{{{latex(sigma)}\sqrt{{2}}}}={latex(sp.simplify(zb))}")
            steps.append(rf"P({a}\le X \le {b}) = \Phi\!\left(\frac{{{b}-\mu}}{{\sigma}}\right) - \Phi\!\left(\frac{{{a}-\mu}}{{\sigma}}\right) = {latex(expr)}")
            steps.append(rf"Numeric value \approx {latex(_num(expr))}")
            return _ok({"result_latex": _boxed(expr), "steps_latex": steps})

        return _err("Unknown condition for Normal.")

    # ---- Exponential ----
    if dist == "exponential":
        lam = sp.sympify(params.get("lam", 1))
        steps = [r"\textbf{Exponential CDF: } F(x) = 1 - e^{-\lambda x},\; x\ge 0",
                 rf"\textbf{{Parameter}}: \lambda={latex(lam)}"]

        if cond_type == "eq":
            x = value
            steps.append(rf"P(X={x}) = 0 \; \text{{(continuous)}}")
            return _ok({"result_latex": r"\boxed{0}", "steps_latex": steps})

        if cond_type == "leq":
            x = sp.sympify(value)
            expr = 1 - sp.exp(-lam*x)
            steps.append(rf"P(X \le {latex(x)}) = 1 - e^{{-\lambda {latex(x)}}} = {latex(expr)}")
            steps.append(rf"Numeric value \approx {latex(_num(expr))}")
            return _ok({"result_latex": _boxed(expr), "steps_latex": steps})

        if cond_type == "geq":
            x = sp.sympify(value)
            expr = sp.exp(-lam*x)
            steps.append(rf"P(X \ge {latex(x)}) = e^{{-\lambda {latex(x)}}} = {latex(expr)}")
            steps.append(rf"Numeric value \approx {latex(_num(expr))}")
            return _ok({"result_latex": _boxed(expr), "steps_latex": steps})

        if cond_type == "interval":
            a, b = value
            a = sp.sympify(a); b = sp.sympify(b)
            expr = (1 - sp.exp(-lam*b)) - (1 - sp.exp(-lam*a))
            steps.append(rf"P({latex(a)}\le X\le {latex(b)}) = e^{{-\lambda {latex(a)}}} - e^{{-\lambda {latex(b)}}} = {latex(expr)}")
            steps.append(rf"Numeric value \approx {latex(_num(expr))}")
            return _ok({"result_latex": _boxed(expr), "steps_latex": steps})

        return _err("Unknown condition for Exponential.")

    return _err("Unsupported distribution for event probabilities.")

# --------------- Bayes ----------------
@probability_bp.route("/bayes", methods=["POST"])
def bayes_route():
    data = request.get_json(force=True)
    mode = (data or {}).get("mode", "two_event")
    steps = []

    if mode == "two_event":
        P_A = float(data.get("P_A", 0))
        P_B_given_A = float(data.get("P_B_given_A", 0))
        P_B_given_notA = float(data.get("P_B_given_notA", 0))
        P_notA = 1 - P_A
        steps.append(r"Law of total probability: \; P(B) = P(B|A)P(A) + P(B|\neg A)P(\neg A)")
        PB = P_B_given_A*P_A + P_B_given_notA*P_notA
        steps.append(rf"Compute: P(B) = {P_B_given_A}\times{P_A} + {P_B_given_notA}\times{P_notA} = {PB:.6f}")
        if PB == 0:
            return _err("Total P(B) is zero; cannot compute posterior.")
        PA_B = (P_B_given_A * P_A) / PB
        steps.append(r"Bayes' rule: \; P(A|B) = \dfrac{P(B|A)P(A)}{P(B)}")
        steps.append(rf"P(A|B) = \dfrac{{{P_B_given_A}\times {P_A}}}{{{PB:.6f}}} = {PA_B:.6f}")
        return _ok({"result_latex": _boxed(PA_B), "steps_latex": steps})

    if mode == "partition":
        parts = data.get("parts", [])
        target_index = int(data.get("target_index", 0))
        if not parts or target_index >= len(parts):
            return _err("Invalid partition input.")
        PB = 0.0
        steps.append(r"Law of total probability: \; P(B) = \sum_i P(B|A_i)P(A_i)")
        for i, part in enumerate(parts):
            P_Ai = float(part.get("P_Ai", 0))
            P_B_given_Ai = float(part.get("P_B_given_Ai", 0))
            PB += P_Ai * P_B_given_Ai
            steps.append(rf"Add: P(B|A_{i})P(A_{i}) = {P_B_given_Ai}\times{P_Ai}")
        steps.append(rf"P(B) = {PB:.6f}")
        if PB == 0:
            return _err("Total P(B) is zero; cannot compute posteriors.")
        PAt = float(parts[target_index].get("P_Ai", 0))
        PB_At = float(parts[target_index].get("P_B_given_Ai", 0))
        posterior = (PB_At * PAt) / PB
        steps.append(r"Bayes' rule for target part:")
        steps.append(rf"P(A_{{{target_index}}}|B) = \dfrac{{{PB_At}\times {PAt}}}{{{PB:.6f}}} = {posterior:.6f}")
        return _ok({"result_latex": _boxed(posterior), "steps_latex": steps})

    return _err("Unsupported bayes mode.")

# --------------- Joint ----------------
@probability_bp.route("/joint", methods=["POST"])
def joint_route():
    data = request.get_json(force=True)
    steps = []
    op = data.get("operation")
    pA = float(data.get("pA", 0))
    pB = float(data.get("pB", 0))
    pA_inter_B = data.get("pA_inter_B", None)
    pB_given_A = data.get("pB_given_A", None)

    if op == "and":
        if pA_inter_B is not None:
            steps.append(rf"P(A\cap B)={pA_inter_B}")
            return _ok({"result_latex": _boxed(pA_inter_B), "steps_latex": steps})
        if pB_given_A is not None:
            val = pA * float(pB_given_A)
            steps.append(rf"P(A\cap B)=P(A)P(B|A)={pA}\times{pB_given_A}={val:.6f}")
            return _ok({"result_latex": _boxed(val), "steps_latex": steps})
        return _err("Provide P(A∩B) or P(B|A) for AND.")

    if op == "union":
        if pA_inter_B is None:
            return _err("Need P(A∩B) for UNION.")
        result = pA + pB - float(pA_inter_B)
        steps.append(rf"P(A\cup B)=P(A)+P(B)-P(A\cap B)={pA}+{pB}-{pA_inter_B}={result:.6f}")
        return _ok({"result_latex": _boxed(result), "steps_latex": steps})

    if op == "conditional":
        if pA_inter_B is None or pB == 0:
            return _err("Need P(A∩B) and P(B)>0 for conditional.")
        result = float(pA_inter_B) / pB
        steps.append(rf"P(A|B)=\frac{{P(A\cap B)}}{{P(B)}}=\frac{{{pA_inter_B}}}{{{pB}}}={result:.6f}")
        return _ok({"result_latex": _boxed(result), "steps_latex": steps})

    if op == "independence":
        if pA_inter_B is None:
            return _err("Need P(A∩B) to check independence.")
        lhs = float(pA_inter_B)
        rhs = pA * pB
        steps.append(rf"Check: P(A\cap B) \stackrel{{?}}={{}} P(A)P(B) \Rightarrow {lhs:.6f} \stackrel{{?}}={{}} {rhs:.6f}")
        return _ok({"result_latex": _boxed(abs(lhs - rhs) < 1e-9), "steps_latex": steps})

    return _err("Unsupported joint operation.")
