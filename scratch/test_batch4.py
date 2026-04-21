import sys
import os
import traceback

sys.path.append('d:/Desktop/MAJORRR/MAthminds')

from regression_solver import solve_regression_problem
from numerical_methods import newton_method, regula_falsi_method
from numerical_odes import rk4_method, euler_method
from linear_programming import solve_lp

def log_res(name, result):
    if isinstance(result, dict) and ("error" in result or result.get("success") is False):
        print(f"[FAIL] {name} FAILED: {result.get('error', result.get('message', 'Unknown Error'))}")
    else:
        print(f"[PASS] {name} PASSED")
        # Extract first step snippet
        if isinstance(result, dict):
            steps = result.get("steps") or (result.get("payload") and result["payload"].get("steps")) or []
            if steps:
                print(f"   First step snippet: {str(steps[0])[:50]}...")
        elif isinstance(result, list):
            if result:
                 print(f"   First step snippet: {str(result[0])[:50]}...")

print("========== BATCH 4 QA ==========")

# 1. Regression
try:
    print("\n--- Regression ---")
    data = {
        "problemType": "linear",
        "points": [{"x": 1, "y": 2}, {"x": 2, "y": 4}, {"x": 3, "y": 5}],
    }
    log_res("Linear Regression", solve_regression_problem(data))
except Exception as e:
    print(f"Regression crash: {e}")
    traceback.print_exc()

# 2. Numerical Methods
try:
    print("\n--- Numerical Methods ---")
    log_res("Newton Method", newton_method("x^2 - 4", "3", 5, 0.001))
    log_res("Regula Falsi", regula_falsi_method("x^2 - 4", "0", "3", 5, 0.001))
except Exception as e:
    print(f"Numerical Methods crash: {e}")
    traceback.print_exc()

# 3. Numerical ODEs
try:
    print("\n--- Numerical ODEs ---")
    log_res("RK4", rk4_method("x+y", "0", "1", "0.1", 2))
    log_res("Euler", euler_method("x+y", "0", "1", "0.1", 2))
except Exception as e:
    print(f"Numerical ODEs crash: {e}")
    traceback.print_exc()

# 4. Linear Programming
try:
    print("\n--- Linear Programming ---")
    lp_data = {
        "method": "simplex",
        "objective_type": "max",
        "objective": "Z = 3*x1 + 2*x2",
        "constraints": [
            "x1 + x2 <= 4",
            "x1 - x2 <= 2"
        ]
    }
    # Wait, solve_lp might take payload dictionary
    # we don't know the signature, let's just use try except fallback inside
    # print dir(linear_programming)
    log_res("Simplex Method", solve_lp(lp_data))
except Exception as e:
    print(f"Linear Programming crash: {e}")
    traceback.print_exc()

print("\n========== END BATCH 4 QA ==========")
