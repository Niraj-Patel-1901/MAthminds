from flask import Flask, render_template, request, send_from_directory, jsonify
from laplace_solver import solve_laplace
from inverse_laplace import solve_inverse_laplace  
import os
from flask_cors import CORS
from matrix_solver import solve_matrix_problem
from regression_solver import solve_regression_problem
from partial_diff_solver import solve_partial_diff
from partial_diff_solver_v2 import solve_partial_diff
from fourier_solver import fourier_bp
from probability_solver import probability_bp
from linear_algebra_solver import solve_linear_algebra
from beta_gamma import beta_gamma_bp
from numerical_methods import bp as numerical_methods_bp
from numerical_odes import bp as numerical_odes_bp
from hyperbolic_log_solver import solve_hyperbolic
from maxima_minima_solver import solve_maxima_minima
from first_order_odes_solver import solve_first_order_ode
from higher_order_des_solver import solve_higher_order_de
from z_transform import bp as z_transform_bp
from complex_numbers import bp as complex_numbers_bp
from multiple_integrals_solver import *
from rectification_solver import *
from complex_solver import *
from complex_integration_solver import *
from inverse_z_transform import bp as inverse_z_transform_bp
from linear_programming import bp as lp_bp
from service import OCRService
# === MathBot Gemini Setup ===
from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


app = Flask(__name__)
CORS(app)
#ocr handling
ocr_service=OCRService()


app.register_blueprint(z_transform_bp)
app.register_blueprint(fourier_bp)
app.register_blueprint(complex_numbers_bp)
app.register_blueprint(probability_bp)
app.register_blueprint(beta_gamma_bp)
app.register_blueprint(numerical_methods_bp)
app.register_blueprint(numerical_odes_bp)
app.register_blueprint(inverse_z_transform_bp)
app.register_blueprint(lp_bp)

# Route for static files (CSS, JS)
@app.route('/styles.css')
def styles():
    return send_from_directory('static', 'styles.css')

@app.route('/js/<path:filename>')
def js_files(filename):
    return send_from_directory('templates/js', filename)

# Route for Main Index Page (root route)
@app.route("/")
def main_index():
    return render_template("index.html")

# Route for Laplace Transform (moved to /laplace)
@app.route("/laplace", methods=["GET", "POST"])
def laplace_transform():
    result = {}
    if request.method == "POST":
        expr = request.form["expression"]
        result = solve_laplace(expr)
    return render_template("pages/laplace-transform.html", result=result)

# Route for Inverse Laplace Transform
@app.route("/inverse-laplace", methods=["GET", "POST"])
def inverse_laplace():
    result = {}
    expression = ""
    if request.method == "POST":
        expr = request.form["expression"]
        expression = expr
        result = solve_inverse_laplace(expr)
    return render_template("pages/inverse-laplace.html", result=result, expression=expression)

# Semester Routes
@app.route("/semester1")
def semester1():
    return render_template("pages/semester1.html")

@app.route("/semester2")
def semester2():
    return render_template("pages/semester2.html")

@app.route("/semester3")
def semester3():
    return render_template("pages/semester3.html")

@app.route("/semester4")
def semester4():
    return render_template("pages/semester4.html")

# Module Routes - Pages folder
@app.route("/probability")
def probability():
    return render_template("pages/probability.html")

@app.route("/regression")
def regression():
    return render_template("pages/regression.html")

@app.route("/complex-variables")
def complex_variables():
    return render_template("pages/complex-variables.html")

@app.route("/fourier-series")
def fourier_series():
    return render_template("pages/fourier-series.html")

@app.route("/complex-numbers")
def complex_numbers():
    return render_template("pages/complex-numbers.html")

@app.route("/matrices")
def matrices():
    return render_template("pages/matrices.html")

@app.route("/numerical-integration")
def numerical_integration():
    return render_template("pages/numerical-integration.html")

@app.route("/rectification")
def rectification():
    return render_template("pages/rectification.html")

@app.route("/beta-gamma")
def beta_gamma():
    return render_template("pages/beta-gamma.html")

@app.route("/linear-programming")
def linear_programming():
    return render_template("pages/linear-programming.html")

@app.route("/multiple-integrals")
def multiple_integrals():
    return render_template("pages/multiple-integrals.html")

@app.route("/z-transform")
def z_transform():
    return render_template("pages/z-transform.html")

@app.route("/higher-order-des")
def higher_order_des():
    return render_template("pages/higher-order-des.html")

@app.route("/inverse-z-transform")
def inverse_z_transform():
    return render_template("pages/inverse-z-transform.html")

@app.route("/eigenvalues")
def eigenvalues():
    return render_template("pages/eigenvalues.html")

@app.route("/complex-integration")
def complex_integration():
    return render_template("pages/complex-integration.html")

@app.route("/numerical-methods")
def numerical_methods():
    return render_template("pages/numerical-methods.html")

@app.route("/maxima-minima")
def maxima_minima():
    return render_template("pages/maxima-minima.html")

@app.route("/partial-diff")
def partial_diff():
    return render_template("pages/partial-diff.html")

@app.route("/hyperbolic-log")
def hyperbolic_log():
    return render_template("pages/hyperbolic-log.html")

@app.route("/nonlinear-programming")
def nonlinear_programming():
    return render_template("pages/nonlinear-programming.html")

@app.route("/first-order-odes")
def first_order_odes():
    return render_template("pages/first-order-odes.html")

@app.route('/api/matrix', methods=['POST'])
def api_matrix():
    try:
        data = request.get_json()
        result = solve_matrix_problem(data)
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/regression', methods=['POST'])
def api_regression():
    try:
        data = request.get_json()
        payload = solve_regression_problem(data)
        return jsonify({"success": True, "payload": payload})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})



# @app.route('/api/partial_diff', methods=['POST'])
# def api_partial_diff():
#     try:
#         data = request.get_json()
#         result = solve_partial_diff(data)
#         return jsonify({"success": True, **result})
#     except Exception as e:
#         return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/linear-algebra", methods=["POST"])
def api_linear_algebra():
    try:
        data = request.get_json(force=True)
        result = solve_linear_algebra(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/partial_diff', methods=['POST'])
def api_partial_diff():
    try:
        data = request.get_json()
        payload = solve_partial_diff(data)
        # follow project pattern: return {"success": True, **payload}
        return jsonify({"success": True, **payload})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400



@app.route('/api/hyperbolic-log', methods=['POST'])
def api_hyperbolic_log():
    """
    Expects JSON:
    {
      "problemType": "hyperbolic" | "inverse" | "complex" | "properties",
      "inputVal": "2+3i",
      "func": "sinh" or "cosh" or "tanh" or "ln" or inverse names,
      "param1": optional,
      "param2": optional
    }
    Returns JSON with steps (latex) and result (latex).
    """
    try:
        data = request.get_json(force=True)
        problem_type = data.get("problemType")
        input_val = data.get("inputVal", "")
        func = data.get("func", "")
        param1 = data.get("param1")
        param2 = data.get("param2")

        payload = solve_hyperbolic(problem_type, input_val, func, param1, param2)
        if not payload.get("success"):
            return jsonify({"success": False, "error": payload.get("error", "Unknown error")}), 400
        return jsonify({"success": True, "payload": payload})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/api/maxima-minima', methods=['POST'])
def api_maxima_minima():
    """
    Expects JSON:
    {
      "problemType": "unconstrained" | "constrained" | "absolute" | "boundary",
      "function": "f(x,y) expression string",
      "constraint": "g(x,y)=c" (optional, required for constrained),
      "xRange": "-1 <= x <= 1" (optional),
      "yRange": "0 <= y <= 2" (optional)
    }
    """
    try:
        data = request.get_json(force=True)
        problem_type = data.get("problemType", "unconstrained")
        function_str = data.get("function", "")
        constraint_str = data.get("constraint", "")
        x_range = data.get("xRange", "")
        y_range = data.get("yRange", "")

        payload = solve_maxima_minima(problem_type, function_str, constraint_str, x_range, y_range)
        if not payload.get("success"):
            return jsonify({"success": False, "error": payload.get("error", "Unknown error")}), 400
        return jsonify({"success": True, "payload": payload})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/api/first-order-odes', methods=['POST'])
def api_first_order_odes():
    try:
        data = request.get_json()

        problem_type = data.get("problemType")
        equation = data.get("equation")
        initial_condition = data.get("initialCondition")

        result = solve_first_order_ode(problem_type, equation, initial_condition)

        if not result["success"]:
            return jsonify({"success": False, "error": result["error"]})

        return jsonify({
            "success": True,
            "payload": result
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/higher-order-des", methods=["POST"])
def api_higher_order_des():
    data = request.get_json()
    problem_type = data.get("problemType", "")
    equation = data.get("equation", "")
    ic1 = data.get("ic1", "")
    ic2 = data.get("ic2", "")

    result = solve_higher_order_de(problem_type, equation, ic1, ic2)
    return jsonify(result)

@app.route('/api/multiple-integrals', methods=['POST'])
def api_multiple_integrals():
    try:
        data = request.get_json()
        t = data.get("type")

        # Rectangular Double Integral
        if t == "double":
            res = double_rectangular(
                data["function"],
                data["xlim"],
                data["ylim"]
            )

        # Curved Region Double Integral
        elif t == "curved":
            res = double_curved(
                data["function"],
                data["xlim"],
                data["ylow"],
                data["yhigh"]
            )

        # Polar Double Integral
        elif t == "polar":
            res = double_polar(
                data["function"],
                data["rlim"],
                data["thetalim"]
            )

        # Area between curves
        elif t == "area":
            res = area_between(
                data["xlim"],
                data["ylow"],
                data["yhigh"]
            )

        # Triple Cartesian
        elif t == "triple":
            res = triple_cartesian(
                data["function"],
                data["xlim"],
                data["ylim"],
                data["zlim"]
            )

        # Triple Cylindrical
        elif t == "cylindrical":
            res = triple_cylindrical(
                data["function"],
                data["rlim"],
                data["thetalim"],
                data["zlim"]
            )

        # Triple Spherical
        elif t == "spherical":
            res = triple_spherical(
                data["function"],
                data["rholim"],
                data["philim"],
                data["thetalim"]
            )

        elif t == "change":
            res = change_order(
                data["function"],
                data["xfrom"],
                data["xto"],
                data["yfrom"],
                data["yto"]
    )

        else:
            return jsonify({"success": False, "error": "Invalid problem type"})

        return jsonify({"success": True, "payload": res})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/rectification', methods=['POST'])
def api_rectification():
    try:
        data = request.get_json()
        t = data["type"]

        if t == "cartesian":
            res = cartesian_arc_length(
                data["function"],
                data["a"],
                data["b"]
            )

        elif t == "polar":
            res = polar_arc_length(
                data["function"],
                data["a"],
                data["b"]
            )

        else:
            return jsonify({"success": False, "error": "Invalid type"})

        return jsonify({"success": True, "payload": res})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/complex", methods=["POST"])
def complex_api():
    data = request.json
    t = data["type"]

    try:
        if t == "analytic":
            steps, result = analytic_check(data["function"])
        elif t == "derivative":
            steps, result = complex_derivative(data["function"], data["point"])
        elif t == "series":
            steps, result = power_series(data["function"], data["point"], data["terms"])
        elif t == "mapping":
            steps, result = conformal_map(data["function"], data["point"])
        elif t == "milne":
            steps, result = milne_thomson(data["u"], data["v"])
        else:
            return jsonify(success=False, error="Unknown type")

        return jsonify(success=True, payload={
            "steps": steps,
            "result": result
        })

    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route("/api/complex-integration", methods=["POST"])
def complex_integration_api():
    data = request.json
    try:
        f = parse(data["fz"])
        mode = data["mode"]

        if mode == "cauchy":
            a = sp.sympify(data["z0"])
            steps, result, plot = cauchy_integral(f, a)

        elif mode == "residue":
            steps, result, plot = residue_solver(f, 0, data["radius"])

        elif mode in ["taylor", "laurent"]:
            steps, result, plot = series_solver(f, float(data["z0"]), data["terms"], mode)

        elif mode == "singular":
            steps, result, plot = singular_solver(f)

        else:
            return jsonify(success=False, error="Unknown mode")

        return jsonify(success=True, payload={
            "steps": steps,
            "result": result,
            "plot": plot
        })

    except Exception as e:
        return jsonify(success=False, error=str(e))

#FOR MATHBOT
@app.route("/api/mathbot", methods=["POST"])
def mathbot():
    data = request.get_json()

    question = data.get("question", "")
    module = data.get("module", "")
    step = data.get("step", "")

    prompt = f"""
You are MathBot, an AI tutor for Engineering Mathematics (Mumbai University).

Current Module: {module}

STRICT RULES:
1. If the user asks about the current module, reply with ONLY the module name.
   - No explanation
   - No formatting
   - No bullet points

2. If the question is conceptual or numerical:
   - Explain step-by-step
   - Use clear math notation
   - Follow Mumbai University exam style
   - Keep answers concise and structured
3. If a specific step is given:
    - Explain ONLY that step
    - Explain WHY it is done
    - Keep it short and exam-oriented
    - Avoid repeating the full solution

4. Do NOT add introductions like "Hello", "I am MathBot", etc.
5. Do NOT add unnecessary theory unless asked.

Student Question:
{question}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        return jsonify({
            "success": True,
            "reply": response.text
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })
#Ocr handling
@app.route("/api/ocr-image", methods=["POST"])
def api_ocr_image():
    """
    Handle image upload and extract text/LaTeX using OCR
    Returns: {
        "success": true/false,
        "original_text": extracted text,
        "latex": extracted LaTeX formula,
        "readable": human-readable version,
        "warnings": any warnings from OCR models
    }
    """
    try:
        if 'image' not in request.files:
            return jsonify({"success": False, "error": "No image provided"}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"success": False, "error": "No image selected"}), 400
        
        # Read image bytes
        image_bytes = image_file.read()
        
        # Process image with OCR (async function needs to be awaited)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            ocr_service.process_image_bytes(image_bytes)
        )
        loop.close()

        
        import re

        readable = result.get('readable', '')

        # readable = re.sub(r'(sin|cos|tan)(\d+[a-zA-Z])', r' \1(\2)', readable)
        # # 2. Add multiplication before trig function
        # readable = re.sub(r'([a-zA-Z0-9\^])\s*(sin|cos|tan)', r'\1 * \2', readable)
        # sin3t -> sin(3*t)
        readable = re.sub(r'(sin|cos|tan)(\d+)([a-zA-Z])', r'\1(\2*\3)', readable)

        # sin4x -> sin(4*x)
        readable = re.sub(r'(sin|cos|tan)(\d+)', r'\1(\2)', readable)

        # t^2sin -> t^2*sin
        readable = re.sub(r'([a-zA-Z0-9\^])\s*(sin|cos|tan)', r'\1*\2', readable)

        # 2t -> 2*t
        readable = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', readable)

        # xsin -> x*sin
        readable = re.sub(r'([a-zA-Z])(?=(sin|cos|tan))', r'\1*', readable)

        # clean spaces
        readable = re.sub(r'\s+', ' ', readable).strip()

        extracted_formula = readable

        return jsonify({
            "success": True,
            "original_text": result.get('original_text', ''),
            "latex": result.get('latex', ''),
            "readable": readable,
            "extracted_formula": extracted_formula,
            "warnings": result.get('warnings')
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
#ocrservice for regression module
from regression_ocrservice import RegressionOCRService

regression_ocr = RegressionOCRService()

@app.route("/api/ocr-regression", methods=["POST"])
def ocr_regression():
    try:
        if 'image' not in request.files:
            return jsonify({"success": False, "error": "No image provided"}), 400

        image_file = request.files['image']
        image_bytes = image_file.read()

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            regression_ocr.process_image_bytes(image_bytes)
        )

        loop.close()

        print("OCR RESULT:", result)

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
    
if __name__ == "__main__":
    print(" Starting Flask app...")
    app.run(debug=True)



