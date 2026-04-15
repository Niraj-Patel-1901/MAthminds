# regression_solver.py (full with tables + 3 decimal formatting)

import math
from typing import List, Dict, Any
from sympy import latex
from sympy.parsing.sympy_parser import parse_expr
import numpy as np

# ---- Helpers ----
def _parse_number(s):
    if s is None:
        raise ValueError("Empty value encountered")
    if isinstance(s, (int, float)):
        return float(s)
    t = str(s).strip()
    if t == '':
        raise ValueError('Empty string')
    val = parse_expr(t)  # allows expressions like 1/2, 3+4/5
    if val.is_real is False:
        raise ValueError(f'Non-real value not supported: {t}')
    return float(val)

def _to_num_list(arr):
    return [_parse_number(x) for x in arr]

def _format(x: float, ndigits: int = 3) -> str:
    if x is None:
        return 'None'
    if abs(x - round(x)) < 1e-12:
        return str(int(round(x)))
    return f"{x:.{ndigits}f}"

# ---- Ranking with average ranks for ties ----
def rankdata(values: List[float]) -> List[float]:
    n = len(values)
    pairs = sorted([(v, i) for i, v in enumerate(values)], key=lambda p: (p[0], p[1]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        v = pairs[i][0]
        j = i
        indices = []
        while j < n and pairs[j][0] == v:
            indices.append(pairs[j][1])
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for idx in indices:
            ranks[idx] = avg_rank
        i = j
    return ranks

def _has_ties(values: List[float]) -> bool:
    s = set()
    for v in values:
        if v in s:
            return True
        s.add(v)
    return False

# ---- Pearson correlation ----
def pearson_correlation(x_in: List[Any], y_in: List[Any]) -> Dict[str, Any]:
    x = _to_num_list(x_in)
    y = _to_num_list(y_in)
    if len(x) != len(y):
        raise ValueError("x and y must have same length")
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(a * b for a, b in zip(x, y))
    sum_x2 = sum(a * a for a in x)
    sum_y2 = sum(b * b for b in y)
    numerator = n * sum_xy - sum_x * sum_y
    denom_term1 = n * sum_x2 - sum_x * sum_x
    denom_term2 = n * sum_y2 - sum_y * sum_y
    denominator = math.sqrt(max(0.0, denom_term1 * denom_term2))
    r = None
    if denominator != 0:
        r = numerator / denominator

    steps = [
        r"Given: \quad x = %s,\; y = %s" % (latex(str(x)), latex(str(y))),
        r"n = %d" % n,
        r"\sum x = %s" % _format(sum_x),
        r"\sum y = %s" % _format(sum_y),
        r"\sum xy = %s" % _format(sum_xy),
        r"\sum x^2 = %s" % _format(sum_x2),
        r"\sum y^2 = %s" % _format(sum_y2),
        r"\text{Numerator} = n\sum xy - (\sum x)(\sum y) = %s" % _format(numerator),
        r"\text{Denominator} = \sqrt{[n\sum x^2 - (\sum x)^2][n\sum y^2 - (\sum y)^2]} = %s" % _format(denominator)
    ]
    if r is None:
        steps.append(r"\text{Correlation is undefined (division by zero)}")
        result = {"r": None}
    else:
        steps.append(r"r = \dfrac{%s}{%s} = %s" % (_format(numerator), _format(denominator), _format(r)))
        result = {"r": float(r)}

    table = {
        "headers": ["x", "y", "x²", "y²", "xy"],
        "rows": [[_format(a), _format(b), _format(a*a), _format(b*b), _format(a*b)] for a, b in zip(x, y)]
    }

    return {"type": "pearson", "table": table, "result": result, "steps": steps}

# ---- Spearman correlation ----
def spearman_correlation(x_in: List[Any], y_in: List[Any]) -> Dict[str, Any]:
    x = _to_num_list(x_in)
    y = _to_num_list(y_in)
    if len(x) != len(y):
        raise ValueError("x and y must have same length")
    n = len(x)
    rx = rankdata(x)
    ry = rankdata(y)
    d = [rx_i - ry_i for rx_i, ry_i in zip(rx, ry)]
    d2 = [di * di for di in d]
    sum_d2 = sum(d2)

    steps = [
        r"Ranks: \quad r_x = %s,\; r_y = %s" % (latex(str([_format(v) for v in rx])), latex(str([_format(v) for v in ry]))),
        r"d_i = r_{x_i} - r_{y_i} = %s" % latex(str([_format(v) for v in d])),
        r"\sum d_i^2 = %s" % _format(sum_d2)
    ]

    ties_in_x = _has_ties(x)
    ties_in_y = _has_ties(y)
    if not ties_in_x and not ties_in_y:
        rs = 1.0 - (6.0 * sum_d2) / (n * (n * n - 1))
        steps.append(r"\text{No ties detected; use formula } r_s = 1 - \dfrac{6\sum d^2}{n(n^2-1)}")
        steps.append(r"r_s = %s" % _format(rs))
        result = {"r_s": float(rs)}
    else:
        steps.append(r"\text{Ties detected; computing Pearson correlation on ranks}")
        pear = pearson_correlation(rx, ry)
        result = {"r_s": pear["result"]["r"]}
        steps.extend([r"(on ranks) " + s for s in pear["steps"]])

    table = {
        "headers": ["x", "y", "r_x", "r_y", "d", "d²"],
        "rows": [[_format(xi), _format(yi), _format(rxi), _format(ryi), _format(di), _format(di2)]
                 for xi, yi, rxi, ryi, di, di2 in zip(x, y, rx, ry, d, d2)]
    }

    return {"type": "spearman", "table": table, "result": result, "steps": steps}

# ---- Linear regression ----
def linear_regression(x_in: List[Any], y_in: List[Any]) -> Dict[str, Any]:
    x = _to_num_list(x_in)
    y = _to_num_list(y_in)
    if len(x) != len(y):
        raise ValueError("x and y must have same length")
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    Sxx = sum((xi - mean_x) ** 2 for xi in x)
    Syy = sum((yi - mean_y) ** 2 for yi in y)
    Sxy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))

    steps = [
        r"\bar{x} = %s,\; \bar{y} = %s" % (_format(mean_x), _format(mean_y)),
        r"S_{xx} = \sum (x - \bar{x})^2 = %s" % _format(Sxx),
        r"S_{yy} = \sum (y - \bar{y})^2 = %s" % _format(Syy),
        r"S_{xy} = \sum (x - \bar{x})(y - \bar{y}) = %s" % _format(Sxy)
    ]

    if abs(Sxx) < 1e-15:
        raise ValueError("Variance of x is zero; cannot compute regression of y on x")

    b_y_on_x = Sxy / Sxx
    a_y_on_x = mean_y - b_y_on_x * mean_x

    if abs(Syy) < 1e-15:
        b_x_on_y = None
        a_x_on_y = None
    else:
        b_x_on_y = Sxy / Syy
        a_x_on_y = mean_x - b_x_on_y * mean_y

    y_hat = [a_y_on_x + b_y_on_x * xi for xi in x]
    residuals = [yi - yhi for yi, yhi in zip(y, y_hat)]
    SSE = sum(r * r for r in residuals)
    SSR = sum((yhi - mean_y) ** 2 for yhi in y_hat)
    SST = SSR + SSE
    R2 = SSR / SST if SST != 0 else None

    pear = pearson_correlation(x, y)
    pearson_r = pear['result']['r']

    steps.extend([
        r"b_{y\mid x} = \dfrac{S_{xy}}{S_{xx}} = %s" % _format(b_y_on_x),
        r"a_{y\mid x} = \bar{y} - b_{y\mid x}\bar{x} = %s" % _format(a_y_on_x),
        r"\text{Regression line (y on x): } \hat{y} = %s + %s x" % (_format(a_y_on_x), _format(b_y_on_x))
    ])

    if b_x_on_y is not None:
        steps.extend([
            r"b_{x\mid y} = \dfrac{S_{xy}}{S_{yy}} = %s" % _format(b_x_on_y),
            r"a_{x\mid y} = \bar{x} - b_{x\mid y}\bar{y} = %s" % _format(a_x_on_y),
            r"\text{Regression line (x on y): } \hat{x} = %s + %s y" % (_format(a_x_on_y), _format(b_x_on_y))
        ])
    else:
        steps.append(r"\text{Cannot compute regression of x on y (variance of y is zero)}")

    steps.extend([
        r"\text{Predicted values } \hat{y}: %s" % latex(str([_format(v) for v in y_hat])),
        r"\text{Residuals } e: %s" % latex(str([_format(v) for v in residuals])),
        r"SSE = %s,\; SSR = %s,\; SST = %s" % (_format(SSE), _format(SSR), _format(SST)),
        r"R^2 = %s" % (_format(R2) if R2 is not None else 'undefined'),
        r"\text{Pearson } r = %s" % (_format(pearson_r) if pearson_r is not None else 'undefined')
    ])

    result = {
        "y_on_x": {"a": float(a_y_on_x), "b": float(b_y_on_x)},
        "x_on_y": {"a": float(a_x_on_y) if a_x_on_y is not None else None, "b": float(b_x_on_y) if b_x_on_y is not None else None},
        "predicted_y": [float(v) for v in y_hat],
        "residuals": [float(v) for v in residuals],
        "SSE": float(SSE),
        "SSR": float(SSR),
        "SST": float(SST),
        "R2": float(R2) if R2 is not None else None,
        "pearson_r": float(pearson_r) if pearson_r is not None else None,
    }

    table = {
        "headers": ["x", "y", "ŷ", "Residual"],
        "rows": [[_format(xi), _format(yi), _format(yhi), _format(res)]
                 for xi, yi, yhi, res in zip(x, y, y_hat, residuals)]
    }

    return {"type": "regression", "table": table, "result": result, "steps": steps}

# ---- Dispatcher ----
def solve_regression_problem(data: Dict[str, Any]) -> Dict[str, Any]:
    typ = data.get('type', 'regression')
    x = data.get('x')
    y = data.get('y')
    if x is None or y is None:
        raise ValueError('Both x and y must be provided')

    if typ == 'pearson':
        return pearson_correlation(x, y)
    elif typ == 'spearman':
        return spearman_correlation(x, y)
    elif typ == 'regression':
        return linear_regression(x, y)
    elif typ == 'all':
        return {
            'pearson': pearson_correlation(x, y),
            'spearman': spearman_correlation(x, y),
            'regression': linear_regression(x, y)
        }
    else:
        raise ValueError(f'Unknown type: {typ}')
