import sys
import os
import json
import traceback

sys.path.append('d:/Desktop/MAJORRR/MAthminds')

from first_order_odes_solver import solve_first_order_ode
from higher_order_des_solver import solve_higher_order_de
from multiple_integrals_solver import double_rectangular, triple_cartesian

def log_res(name, result):
    if "error" in result or result.get("success") is False:
        print(f"[FAIL] {name} FAILED: {result.get('error', result.get('message', 'Unknown Error'))}")
    else:
        print(f"[PASS] {name} PASSED")
        # print first step to check format
        steps = result.get("steps") or (result.get("payload") and result["payload"].get("steps")) or []
        if steps:
            print(f"   First step snippet: {str(steps[0])[:50]}...")

print("========== BATCH 2 QA ==========")

# 1. First-Order ODEs
try:
    print("\n--- First-Order ODE ---")
    log_res("Separable", solve_first_order_ode('separable', 'dy/dx = y*x'))
    log_res("Linear", solve_first_order_ode('linear', "y' + y/x = x"))
    log_res("Exact", solve_first_order_ode('exact', 'dy/dx = (x+y)/(x-y)'))
except Exception as e:
    print(f"First-Order crash: {e}")
    traceback.print_exc()

# 2. Higher-Order ODEs
try:
    print("\n--- Higher-Order ODE ---")
    log_res("Homogeneous", solve_higher_order_de('linear_constant', "y'' - 5*y' + 6*y = 0"))
    log_res("Non-Homogeneous", solve_higher_order_de('linear_constant', "y'' + y = sin(x)"))
except Exception as e:
    print(f"Higher-Order crash: {e}")
    traceback.print_exc()

# 3. Multiple Integrals
try:
    print("\n--- Multiple Integrals ---")
    log_res("Double Integral", double_rectangular('x*y', [0, 1], [0, 2]))
    log_res("Triple Integral", triple_cartesian('x*y*z', [0, 1], [0, 2], [0, 3]))
except Exception as e:
    print(f"Multiple Integrals crash: {e}")
    traceback.print_exc()

print("\n========== END BATCH 2 QA ==========")
