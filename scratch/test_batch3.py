import sys
import os
import traceback

sys.path.append('d:/Desktop/MAJORRR/MAthminds')

from laplace_solver import solve_laplace
from inverse_laplace import solve_inverse_laplace
from complex_solver import analytic_check, complex_derivative, power_series

def log_res(name, result):
    if "error" in result or result.get("success") is False:
        print(f"[FAIL] {name} FAILED: {result.get('error', result.get('message', 'Unknown Error'))}")
    else:
        print(f"[PASS] {name} PASSED")
        # For complex solver, it might return a tuple (steps, result)
        if isinstance(result, tuple):
            print(f"   Result: {str(result[1])[:50]}")
        else:
            steps = result.get("steps") or (result.get("payload") and result["payload"].get("steps")) or []
            if steps:
                print(f"   First step snippet: {str(steps[0])[:50]}...")

print("========== BATCH 3 QA ==========")

# 1. Laplace Transform
try:
    print("\n--- Laplace Transfom ---")
    log_res("Laplace Standard", solve_laplace('sin(t)'))
    log_res("Inverse Laplace", solve_inverse_laplace('1/(s^2+1)'))
except Exception as e:
    print(f"Laplace crash: {e}")
    traceback.print_exc()

# 2. Complex Variables
try:
    print("\n--- Complex Variables ---")
    steps, res = analytic_check('x^2 - y^2 + 2*I*x*y')
    log_res("Analytic Check", (steps, res))
    
    steps, res = complex_derivative('z^2', '2')
    log_res("Derivative", (steps, res))
    
    steps, res = power_series('exp(z)', '0', '3')
    log_res("Power Series", (steps, res))
except Exception as e:
    print(f"Complex Variables crash: {e}")
    traceback.print_exc()

# Z-Transform and Fourier are inside blueprints needing Flask Context or internal endpoints testing. 
# Z-Transform methods:
from z_transform import compute_ztransform_of_expr
try:
    print("\n--- Z Transform Internals ---")
    res = compute_ztransform_of_expr('a**k')
    print("[PASS] Z-Transform Internals PASSED")
except Exception as e:
    print(f"[FAIL] Z-Transform crash: {e}")

print("\n========== END BATCH 3 QA ==========")
