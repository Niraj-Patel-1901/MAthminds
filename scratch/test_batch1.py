import sys
import os
import json
import traceback

sys.path.append('d:/Desktop/MAJORRR/MAthminds')

from matrix_solver import handle_operations, handle_echelon, handle_determinant, parse_matrix
from linear_algebra_solver import solve_linear_algebra
from partial_diff_solver_v2 import solve_partial_diff
from maxima_minima_solver import solve_maxima_minima
from hyperbolic_log_solver import solve_hyperbolic
from rectification_solver import cartesian_arc_length

def log_res(name, result):
    if "error" in result or result.get("success") is False:
        print(f"[FAIL] {name} FAILED: {result.get('error', result.get('message', 'Unknown Error'))}")
    else:
        print(f"[PASS] {name} PASSED")
        # print first step to check format
        steps = result.get("steps") or (result.get("payload") and result["payload"].get("steps")) or []
        if steps:
            print(f"   First step snippet: {str(steps[0])[:50]}...")

print("========== BATCH 1 QA ==========")

# 1. Matrices
try:
    print("\n--- Matrix Solver ---")
    m_data = [['1', '2'], ['3', '4']]
    m = parse_matrix(m_data)
    log_res("Matrix Add", handle_operations(m, B=m, operation='add'))
    log_res("Matrix Mult", handle_operations(m, B=m, operation='multiply'))
    log_res("Matrix Det", handle_determinant(m))
    log_res("Matrix Echelon", handle_echelon(m))
except Exception as e:
    print(f"Matrix crash: {e}")
    traceback.print_exc()

# 2. Linear Algebra
try:
    print("\n--- Eigen & Linear Algebra ---")
    log_res("Eigenvalues", solve_linear_algebra({'task': 'eigen', 'A': [['1', '2'], ['2', '1']]}))
    log_res("Cayley-Hamilton", solve_linear_algebra({'task': 'cayley', 'A': [['1', '2'], ['2', '1']]}))
except Exception as e:
    print(f"Linear Algebra crash: {e}")
    traceback.print_exc()

# 3. Partial Diff
try:
    print("\n--- Partial Differentiation ---")
    log_res("First Order", solve_partial_diff({'mode': 'first', 'function': 'x^2 + y^2', 'var': 'x'}))
    log_res("Higher Order", solve_partial_diff({'mode': 'higher', 'function': 'x^2*y', 'sequence': ['x', 'y']}))
except Exception as e:
    print(f"Partial Diff crash: {e}")
    traceback.print_exc()

# 4. Maxima Minima
try:
    print("\n--- Maxima Minima ---")
    log_res("Unconstrained", solve_maxima_minima('unconstrained', 'x^2 + y^2 - 2*x - 4*y'))
    log_res("Constrained", solve_maxima_minima('constrained', 'x*y', 'x + y - 10'))
except Exception as e:
    print(f"Maxima crash: {e}")
    traceback.print_exc()

# 5. Hyperbolic & Log
try:
    print("\n--- Hyperbolic & Log ---")
    log_res("Hyperbolic", solve_hyperbolic('hyperbolic', 'x+I*y', 'sinh'))
    log_res("Logarithmic", solve_hyperbolic('complex', 'x+I*y', 'ln'))
except Exception as e:
    print(f"Hyperbolic crash: {e}")
    traceback.print_exc()

# 6. Rectification
try:
    print("\n--- Rectification ---")
    log_res("Cartesian", cartesian_arc_length('x^2', '0', '1'))
    # Note: rectification uses lambda so tracebacks might catch inside
except Exception as e:
    print(f"Rectification crash: {e}")
    traceback.print_exc()

print("\n========== END BATCH 1 QA ==========")
