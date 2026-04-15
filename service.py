from __future__ import annotations

import io
import os
from typing import Any

import numpy as np
from PIL import Image
import re

# PaddleOCR for generic text
try:
    from paddleocr import PaddleOCR  # type: ignore
    PADDLEOCR_AVAILABLE = True
except Exception:  # noqa: BLE001
    PaddleOCR = None
    PADDLEOCR_AVAILABLE = False

# pix2tex for math LaTeX
try:
    import torch
    from pix2tex.cli import LatexOCR  # type: ignore
    PIX2TEX_AVAILABLE = True
except ImportError:
    torch = None
    LatexOCR = None
    PIX2TEX_AVAILABLE = False

# EasyOCR as fallback for better symbol recognition
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    easyocr = None
    EASYOCR_AVAILABLE = False

# SymPy for LaTeX to readable conversion
try:
    from sympy.parsing.latex import parse_latex  # type: ignore
    from sympy import srepr
    SYMPY_AVAILABLE = True
except Exception:  # noqa: BLE001
    parse_latex = None
    srepr = None
    SYMPY_AVAILABLE = False


class OCRService:
	def __init__(self) -> None:
		self._warnings: list[str] = []
		# Lazy init: heavy models are created on first request
		self.text_ocr = None
		self.math_ocr = None
		self.easy_ocr = None
		self._models_ready = False

	def _init_models(self) -> None:
		# Only initialize if models aren't already loaded
		if self._models_ready:
			return
			
		self._warnings.clear()
		print("[OCR DEBUG] Initializing OCR models...")
		
		# Initialize PaddleOCR
		if not PADDLEOCR_AVAILABLE:
			self.text_ocr = None
			msg = "PaddleOCR not available - install paddleocr"
			self._warnings.append(msg)
			print(f"[OCR DEBUG] {msg}")
		elif self.text_ocr is None:
			try:
				print("[OCR DEBUG] Loading PaddleOCR model (this may take a moment)...")
				self.text_ocr = PaddleOCR(use_angle_cls=True, lang="en")
				print("[OCR DEBUG] PaddleOCR loaded successfully!")
			except Exception as e:  # noqa: BLE001
				self.text_ocr = None
				msg = f"PaddleOCR init failed: {e}"
				self._warnings.append(msg)
				print(f"[OCR DEBUG] {msg}")
		
		# Initialize EasyOCR as fallback
		if not EASYOCR_AVAILABLE:
			self.easy_ocr = None
			msg = "EasyOCR not available - install easyocr"
			self._warnings.append(msg)
			print(f"[OCR DEBUG] {msg}")
		elif self.easy_ocr is None:
			try:
				print("[OCR DEBUG] Loading EasyOCR model...")
				self.easy_ocr = easyocr.Reader(['en'])
				print("[OCR DEBUG] EasyOCR loaded successfully!")
			except Exception as e:  # noqa: BLE001
				self.easy_ocr = None
				msg = f"EasyOCR init failed: {e}"
				self._warnings.append(msg)
				print(f"[OCR DEBUG] {msg}")
		
		# Initialize pix2tex - only if not already initialized
		if not PIX2TEX_AVAILABLE:
			if self.math_ocr is None:
				self.math_ocr = None
				msg = "pix2tex not available - install pix2tex"
				self._warnings.append(msg)
				print(f"[OCR DEBUG] {msg}")
		elif self.math_ocr is None:
			try:
				print("[OCR DEBUG] Loading pix2tex model...")
				# Try without device parameter first (newer versions)
				self.math_ocr = LatexOCR()
				print("[OCR DEBUG] pix2tex loaded successfully!")
			except Exception as e1:  # noqa: BLE001
				try:
					# Fallback: try with device parameter for older versions
					device = "cuda" if torch.cuda.is_available() else "cpu"
					self.math_ocr = LatexOCR(device=device)
					print("[OCR DEBUG] pix2tex loaded with device parameter!")
				except Exception as e2:  # noqa: BLE001
					self.math_ocr = None
					msg = f"pix2tex init failed: {e1}, fallback also failed: {e2}"
					self._warnings.append(msg)
					print(f"[OCR DEBUG] {msg}")

	def _ensure_initialized(self) -> None:
		if not self._models_ready:
			self._init_models()
			self._models_ready = True
		# Double-check: if models failed to initialize but flag is set, don't retry
		# This prevents infinite retry loops while ensuring models are loaded when possible

	def _looks_like_math(self, text: str) -> bool:
		"""Detect if text looks like a mathematical expression"""
		if not text or len(text.strip()) < 2:
			return False
		
		text_lower = text.lower().strip()
		
		# Math indicators (strong signals)
		math_indicators = [
			'sin', 'cos', 'tan', 'sec', 'csc', 'cot',
			'ln', 'log', 'exp', 'sqrt',
			'frac', '\\frac', '\\sqrt', '\\sin', '\\cos', '\\tan',
			'=', '+', '-', '*', '/', '^', '**',
			'\\', '(', ')', '[', ']',
			'integral', 'sum', 'product', 'limit',
			'dx', 'dy', 'dt', 'ds',
			# Common OCR errors that indicate math
			'sir',  # OCR error for "sin"
			'operatornamesir', 'operatornamesin', 'operatornamecos',
		]
		
		# Check for math indicators
		has_math_indicator = any(indicator in text_lower for indicator in math_indicators)
		
		# Check for patterns like "3t", "x^2", "f(x)", "sin3t", etc.
		has_math_pattern = bool(re.search(
			r'\d+[a-zA-Z]|[a-zA-Z]\d+|\^|\*\*|\([^)]*\)|'
			r'\b(sir|sin|cos|tan|log|ln|exp|sqrt)\s*\d+[a-zA-Z]',
			text_lower
		))
		
		# Check for common math functions (even with OCR errors like "sir")
		has_math_function = bool(re.search(
			r'\b(sir|sin|cos|tan|log|ln|exp|sqrt|sec|csc|cot)\b',
			text_lower
		))
		
		# Check for LaTeX-like patterns
		has_latex = bool(re.search(r'\\[a-zA-Z]+|\\frac|\\sqrt|\\sin|\\cos|\\tan', text))
		
		# If it has math indicators, patterns, functions, or LaTeX, it's likely math
		return has_math_indicator or has_math_pattern or has_math_function or has_latex

	async def process_image_bytes(self, image_bytes: bytes) -> dict[str, Any]:
		print(f"[OCR DEBUG] process_image_bytes called with {len(image_bytes)} bytes")
		self._ensure_initialized()
		
		try:
			image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
			print(f"[OCR DEBUG] Image loaded: size={image.size}, mode={image.mode}")
		except Exception as e:
			print(f"[OCR DEBUG] Error loading image: {e}")
			return {"original_text": "", "latex": None, "readable": None, "warnings": [f"Error loading image: {e}"]}
		
		# Step 1: Quick text probe to detect if it's math
		print("[OCR DEBUG] Running text OCR probe...")
		text_probe = self._run_text_ocr(image)
		print(f"[OCR DEBUG] Text OCR probe result: {repr(text_probe[:100])}")
		
		# Step 2: Check if it looks like math
		is_math = self._looks_like_math(text_probe)
		print(f"[OCR DEBUG] Looks like math: {is_math}")
		
		# Step 3: Always run pix2tex for math expressions (or if text probe suggests math)
		latex = None
		if is_math or self.math_ocr is not None:
			print("[OCR DEBUG] Running math OCR (pix2tex)...")
			latex = self._run_math_ocr(image)
			print(f"[OCR DEBUG] Math OCR result (raw): {repr(latex[:100] if latex else 'None')}")
			
			# Fix OCR errors in LaTeX before processing
			if latex:
				latex = self._fix_latex_ocr_errors(latex)
				print(f"[OCR DEBUG] Math OCR result (cleaned): {repr(latex[:100])}")
		
		# Step 4: If we have good LaTeX from pix2tex, prioritize it (don't let PaddleOCR corrupt it)
		if latex and latex.strip():
			# We have LaTeX output from pix2tex, use it as primary
			# Don't let PaddleOCR text interfere with math expressions
			readable = self._latex_to_readable(latex)
			print(f"[OCR DEBUG] Readable from LaTeX: {repr(readable[:100] if readable else 'None')}")
			
			# Post-process text only as fallback reference, but don't use it for math
			# If text probe has math indicators, ignore it to avoid corruption
			processed_text = ""
			if text_probe and not is_math:
				# Only use text if it's clearly not math
				processed_text = self._post_process_math_text(text_probe)
			else:
				# For math expressions, don't use PaddleOCR text (it has errors like "sir")
				processed_text = ""
			
			result = {
				"original_text": processed_text,  # Keep for reference but don't use as primary
				"latex": latex,
				"readable": readable or latex,  # Prefer readable, fallback to latex
				"warnings": self._warnings or None,
			}
			print(f"[OCR DEBUG] Final result (math mode - pix2tex prioritized): {result}")
			return result
		
		# Step 5: If no LaTeX or not math, use text OCR output
		processed_text = self._post_process_math_text(text_probe)
		print(f"[OCR DEBUG] Processed text: {repr(processed_text[:100])}")
		
		result = {
			"original_text": processed_text,
			"latex": latex,  # May be None
			"readable": processed_text,  # Use processed text as readable
			"warnings": self._warnings or None,
		}
		print(f"[OCR DEBUG] Final result (text mode): {result}")
		return result

	def _run_text_ocr(self, image: Image.Image) -> str:
		if self.text_ocr is None:
			print("[OCR DEBUG] PaddleOCR not initialized")
			return ""
		
		try:
			img_np = np.array(image)
			print(f"[OCR DEBUG] Image shape: {img_np.shape}, dtype: {img_np.dtype}")
			
			result = self.text_ocr.ocr(img_np, cls=True)
			print(f"[OCR DEBUG] OCR Result: {result}")
			
			if result is None:
				print("[OCR DEBUG] OCR returned None")
				return ""
			
			lines: list[str] = []
			total_detections = 0
			
			for page_idx, page in enumerate(result or []):
				print(f"[OCR DEBUG] Processing page {page_idx}")
				for detection in page:
					total_detections += 1
					try:
						# Handle different result formats
						if isinstance(detection, (list, tuple)) and len(detection) >= 2:
							_, text_info = detection[0], detection[1]
							if isinstance(text_info, str):
								text = text_info
							elif isinstance(text_info, (list, tuple)) and len(text_info) > 0:
								text = str(text_info[0])
							else:
								text = str(text_info)
							
							if text and text.strip():
								lines.append(text.strip())
								print(f"[OCR DEBUG] Extracted text: {text}")
						else:
							print(f"[OCR DEBUG] Unexpected detection format: {detection}")
					except Exception as e:
						print(f"[OCR DEBUG] Error parsing detection: {e}")
						continue
			
			print(f"[OCR DEBUG] Total detections: {total_detections}, Extracted lines: {len(lines)}")
			final_text = "\n".join(lines).strip()
			print(f"[OCR DEBUG] Final text output: {final_text}")
			return final_text
			
		except Exception as e:
			print(f"[OCR DEBUG] Error in _run_text_ocr: {type(e).__name__}: {e}")
			import traceback
			traceback.print_exc()
			return ""

	def _run_math_ocr(self, image: Image.Image) -> str | None:
		if self.math_ocr is None:
			return None
		try:
			result = self.math_ocr(image)
			return result if result else None
		except Exception as e:  # noqa: BLE001
			print(f"[OCR DEBUG] pix2tex runtime error: {e}")
			# Don't reset the model on runtime errors, just return None
			return None
	
	def _post_process_math_text(self, text: str) -> str:
		"""Post-process OCR text to improve math symbol recognition"""
		if not text:
			return text
		
		processed = text
		
		# Fix common trig function OCR errors (sir -> sin, etc.)
		# Use regex to handle word boundaries
		processed = re.sub(r'\bsir\b', 'sin', processed, flags=re.IGNORECASE)
		processed = re.sub(r'\bsin\b', 'sin', processed, flags=re.IGNORECASE)
		processed = re.sub(r'\bcos\b', 'cos', processed, flags=re.IGNORECASE)
		processed = re.sub(r'\btan\b', 'tan', processed, flags=re.IGNORECASE)
		processed = re.sub(r'\bsec\b', 'sec', processed, flags=re.IGNORECASE)
		processed = re.sub(r'\bcsc\b', 'csc', processed, flags=re.IGNORECASE)
		processed = re.sub(r'\bcot\b', 'cot', processed, flags=re.IGNORECASE)
		
		# Fix operatorname patterns in text
		processed = re.sub(r'operatornamesir', 'sin', processed, flags=re.IGNORECASE)
		processed = re.sub(r'operatornamesin', 'sin', processed, flags=re.IGNORECASE)
		processed = re.sub(r'operatornamecos', 'cos', processed, flags=re.IGNORECASE)
		processed = re.sub(r'operatornametan', 'tan', processed, flags=re.IGNORECASE)
		
		# Fix common patterns like sin3t -> sin(3t)
		# Pattern: sin followed by number then letter -> sin(number*letter)
		processed = re.sub(r'\bsin(\d+)([a-zA-Z])\b', r'sin(\1*\2)', processed, flags=re.IGNORECASE)
		processed = re.sub(r'\bcos(\d+)([a-zA-Z])\b', r'cos(\1*\2)', processed, flags=re.IGNORECASE)
		processed = re.sub(r'\btan(\d+)([a-zA-Z])\b', r'tan(\1*\2)', processed, flags=re.IGNORECASE)
		
		# Fix sin(3t) pattern variations
		processed = re.sub(r'\bsin\((\d+)([a-zA-Z])\)', r'sin(\1*\2)', processed, flags=re.IGNORECASE)
		
		# Common OCR mistakes and their corrections
		replacements = {
			# Common character misrecognitions
			'!': '1',  # Often misread as 1
			'|': '1',  # Often misread as 1
			# Math symbols
			'X': 'x',  # Convert uppercase X to lowercase x in math context
			# Fix common patterns
			'fx=': 'f(x) = ',
			'f(x)=': 'f(x) = ',
			'=': ' = ',
			'+': ' + ',
			'-': ' - ',
			'*': ' * ',
			'/': ' / ',
			'(': ' (',
			')': ') ',
			# Fix superscripts (common OCR issues)
			'x2': 'x^2',
			'x3': 'x^3',
			'x4': 'x^4',
			# Fix square root
			'sqrt': 'sqrt',
			'sqrt(': 'sqrt(',
			# Fix fractions
			'1/x': '1/x',
			# Fix summation
			'sigma': 'sum',
			'sum': 'sum',
		}
		
		for wrong, correct in replacements.items():
			processed = processed.replace(wrong, correct)
		
		# Clean up extra spaces but preserve structure
		processed = ' '.join(processed.split())
		
		return processed

	def _latex_to_readable(self, latex: str) -> str | None:
		if not SYMPY_AVAILABLE or not latex:
			# Try plaintext fallback if SymPy is unavailable
			return self._latex_plaintext_fallback(latex) or None
		try:
			# Sanitize LaTeX before parsing
			sanitized = self._sanitize_latex_for_sympy(latex)
			# Parse LaTeX into SymPy expression
			expr = parse_latex(sanitized)
			# Convert to a spoken-like form;
			# for now use str(expr) which is human-readable in most cases
			text = str(expr)
			# Minor prettifications
			text = text.replace("**", "^")
			# Fix implicit multiplication (2t -> 2*t)
			text = self._fix_implicit_multiplication(text)
			return text
		except Exception:  # noqa: BLE001
			# Fallback to plaintext conversion if SymPy parsing fails
			return self._latex_plaintext_fallback(latex)
	def _fix_implicit_multiplication(self, text: str) -> str:
		"""Insert explicit multiplication like 2t -> 2*t"""
		if not text:
			return text

		# 2t -> 2*t
		text = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', text)

		# 3(x+1) -> 3*(x+1)
		text = re.sub(r'(\d)\(', r'\1*(', text)

		return text
	def _fix_latex_ocr_errors(self, latex: str) -> str:
		"""Fix common OCR errors in LaTeX output"""
		if not latex:
			return latex
		
		l = latex
		
		# Fix common operatorname OCR errors (sin -> sir, etc.)
		# Pattern: \operatornamesir -> \sin, handle with or without braces
		trig_fixes = [
			(r'\\operatornamesir(\()', r'\\sin\1'),  # \operatornamesir( -> \sin(
			(r'\\operatornamesir\{', r'\\sin{'),     # \operatornamesir{ -> \sin{
			(r'\\operatornamesir\b', r'\\sin'),       # \operatornamesir -> \sin
			(r'\\operatornamesin(\()', r'\\sin\1'),
			(r'\\operatornamesin\{', r'\\sin{'),
			(r'\\operatornamesin\b', r'\\sin'),
			(r'\\operatornamecos(\()', r'\\cos\1'),
			(r'\\operatornamecos\{', r'\\cos{'),
			(r'\\operatornamecos\b', r'\\cos'),
			(r'\\operatornametan(\()', r'\\tan\1'),
			(r'\\operatornametan\{', r'\\tan{'),
			(r'\\operatornametan\b', r'\\tan'),
			(r'\\operatornamesec(\()', r'\\sec\1'),
			(r'\\operatornamesec\{', r'\\sec{'),
			(r'\\operatornamesec\b', r'\\sec'),
			(r'\\operatornamecsc(\()', r'\\csc\1'),
			(r'\\operatornamecsc\{', r'\\csc{'),
			(r'\\operatornamecsc\b', r'\\csc'),
			(r'\\operatornamecot(\()', r'\\cot\1'),
			(r'\\operatornamecot\{', r'\\cot{'),
			(r'\\operatornamecot\b', r'\\cot'),
			(r'\\operatornameln(\()', r'\\ln\1'),
			(r'\\operatornameln\{', r'\\ln{'),
			(r'\\operatornameln\b', r'\\ln'),
			(r'\\operatornamelog(\()', r'\\log\1'),
			(r'\\operatornamelog\{', r'\\log{'),
			(r'\\operatornamelog\b', r'\\log'),
			(r'\\operatornameexp(\()', r'\\exp\1'),
			(r'\\operatornameexp\{', r'\\exp{'),
			(r'\\operatornameexp\b', r'\\exp'),
		]
		
		for pattern, replacement in trig_fixes:
			l = re.sub(pattern, replacement, l, flags=re.IGNORECASE)
		
		# Fix \mathbf, \mathit, \mathrm OCR errors
		# Pattern: \mathbft -> t, \mathbf{t} -> t, \mathbfx -> x
		l = re.sub(r'\\mathbf\{([a-zA-Z])\}', r'\1', l)  # \mathbf{t} -> t
		l = re.sub(r'\\mathit\{([a-zA-Z])\}', r'\1', l)  # \mathit{t} -> t
		
		# Fix \mathrm{COS}, \mathrm{SIN}, etc. -> \cos, \sin (trig functions)
		# Handle uppercase trig functions in \mathrm{}
		trig_in_mathrm = {
			r'\\mathrm\{COS\}': r'\\cos',
			r'\\mathrm\{SIN\}': r'\\sin',
			r'\\mathrm\{TAN\}': r'\\tan',
			r'\\mathrm\{SEC\}': r'\\sec',
			r'\\mathrm\{CSC\}': r'\\csc',
			r'\\mathrm\{COT\}': r'\\cot',
			r'\\mathrm\{LN\}': r'\\ln',
			r'\\mathrm\{LOG\}': r'\\log',
			r'\\mathrm\{EXP\}': r'\\exp',
		}
		for pattern, replacement in trig_in_mathrm.items():
			l = re.sub(pattern, replacement, l)
		
		# Fix \mathrm{cos}, \mathrm{sin}, etc. -> \cos, \sin (lowercase trig functions)
		l = re.sub(r'\\mathrm\{cos\}', r'\\cos', l)
		l = re.sub(r'\\mathrm\{sin\}', r'\\sin', l)
		l = re.sub(r'\\mathrm\{tan\}', r'\\tan', l)
		l = re.sub(r'\\mathrm\{sec\}', r'\\sec', l)
		l = re.sub(r'\\mathrm\{csc\}', r'\\csc', l)
		l = re.sub(r'\\mathrm\{cot\}', r'\\cot', l)
		l = re.sub(r'\\mathrm\{ln\}', r'\\ln', l)
		l = re.sub(r'\\mathrm\{log\}', r'\\log', l)
		l = re.sub(r'\\mathrm\{exp\}', r'\\exp', l)
		
		# Fix single letter variables in \mathrm{} (like \mathrm{t} -> t)
		l = re.sub(r'\\mathrm\{([a-zA-Z])\}', r'\1', l)  # \mathrm{t} -> t
		
		# Direct fixes for common OCR errors without braces
		l = re.sub(r'\\mathbft\b', 't', l)  # \mathbft -> t
		l = re.sub(r'\\mathbfx\b', 'x', l)  # \mathbfx -> x
		l = re.sub(r'\\mathbfy\b', 'y', l)  # \mathbfy -> y
		l = re.sub(r'\\mathbfs\b', 's', l)  # \mathbfs -> s
		
		# Fix OCR errors: /line{{3}} -> 3 (misread number)
		# This pattern seems to be pix2tex misreading numbers
		l = re.sub(r'/line\{\{(\d+)\}\}', r'\1', l)  # /line{{3}} -> 3
		l = re.sub(r'/line\{(\d+)\}', r'\1', l)  # /line{3} -> 3
		l = re.sub(r'/line(\d+)', r'\1', l)  # /line3 -> 3
		
		# Fix \bigl( and \bigr) -> regular parentheses
		l = l.replace('\\bigl(', '(').replace('\\bigr)', ')')
		l = l.replace('\\big(', '(').replace('\\big)', ')')
		l = l.replace('\\Bigl(', '(').replace('\\Bigr)', ')')
		l = l.replace('\\Big(', '(').replace('\\Big)', ')')
		l = l.replace('\\biggl(', '(').replace('\\biggr)', ')')
		l = l.replace('\\Biggl(', '(').replace('\\Biggr)', ')')
		
		# Fix operatorname without backslash (for plain text OCR)
		l = re.sub(r'\boperatornamesir\b', 'sin', l, flags=re.IGNORECASE)
		l = re.sub(r'\boperatornamesin\b', 'sin', l, flags=re.IGNORECASE)
		l = re.sub(r'\boperatornamecos\b', 'cos', l, flags=re.IGNORECASE)
		l = re.sub(r'\boperatornametan\b', 'tan', l, flags=re.IGNORECASE)
		
		return l

	def _sanitize_latex_for_sympy(self, latex: str) -> str:
		"""Prepare OCR LaTeX for SymPy parsing.
		- Keep right-hand side if an '=' is present (drop labels like f(x)=, F(s)=)
		- Remove $ delimiters
		- Drop \left/\right which sometimes confuse simple parsers
		- Normalize \cdot to '*'
		- Collapse excessive braces and spaces
		"""
		l = latex.strip()
		
		# First fix OCR errors
		l = self._fix_latex_ocr_errors(l)
		
		# Keep the rightmost side after '=' to discard labels
		if '=' in l:
			l = l.split('=')[-1]
		# Remove math delimiters
		if l.startswith('$$') and l.endswith('$$'):
			l = l[2:-2]
		elif l.startswith('$') and l.endswith('$'):
			l = l[1:-1]
		# Remove control spacing and sizing commands
		for token in ["\\left", "\\right", "\\,", "\\;", "\\:" ]:
			l = l.replace(token, '')
		# Remove big parentheses sizing commands (already fixed in _fix_latex_ocr_errors, but ensure cleanup)
		l = l.replace('\\bigl(', '(').replace('\\bigr)', ')')
		l = l.replace('\\big(', '(').replace('\\big)', ')')
		l = l.replace('\\Bigl(', '(').replace('\\Bigr)', ')')
		l = l.replace('\\Big(', '(').replace('\\Big)', ')')
		# Normalize multiplication symbol
		l = l.replace("\\cdot", "*")
		# Collapse duplicated braces around sqrt/frac patterns introduced by OCR
		l = l.replace("{\\sqrt", "\\sqrt")
		l = l.replace("{\\frac", "\\frac")
		# Remove stray braces around single tokens
		l = l.replace("{(", "(").replace(")}", ")")
		l = l.replace("{{", "{").replace("}}", "}")
		# Fix /line{{number}} patterns (OCR error)
		l = re.sub(r'/line\{\{(\d+)\}\}', r'\1', l)
		l = re.sub(r'/line\{(\d+)\}', r'\1', l)
		# Trim spaces
		l = ' '.join(l.split())
		return l

	def _latex_plaintext_fallback(self, latex: str) -> str:
		"""Best-effort conversion of LaTeX to human-readable plain text without SymPy.
		Handles common patterns: \frac, \sqrt, \cdot, \times, \div, exponents, and removes wrappers.
		"""
		if not latex:
			return ""
		l = latex
		
		# First fix OCR errors
		l = self._fix_latex_ocr_errors(l)
		
		# Basic cleanup
		l = l.replace("\\left", "").replace("\\right", "")
		l = l.replace("\\,", " ").replace("\\;", " ").replace("\\:", " ")
		l = l.replace("$", "").replace("\\(", "").replace("\\)", "")
		l = l.replace("\\cdot", "*").replace("\\times", "*").replace("\\div", "/")
		l = l.replace("\\over", "/")
		# Fix big parentheses
		l = l.replace('\\bigl(', '(').replace('\\bigr)', ')')
		l = l.replace('\\big(', '(').replace('\\big)', ')')
		l = l.replace('\\Bigl(', '(').replace('\\Bigr)', ')')
		l = l.replace('\\Big(', '(').replace('\\Big)', ')')
		# Fix /line{{number}} OCR errors
		l = re.sub(r'/line\{\{(\d+)\}\}', r'\1', l)
		l = re.sub(r'/line\{(\d+)\}', r'\1', l)
		# Common OCR artifacts
		l = l.replace("`", "'")
		
		# Fix trig functions
		l = l.replace("\\sin", "sin").replace("\\cos", "cos").replace("\\tan", "tan")
		l = l.replace("\\sec", "sec").replace("\\csc", "csc").replace("\\cot", "cot")
		l = l.replace("\\ln", "ln").replace("\\log", "log").replace("\\exp", "exp")

		def extract_braced(s: str, start: int) -> tuple[str, int]:
			"""Extract content inside balanced braces starting at s[start] == '{'. Returns (content, next_index)."""
			assert s[start] == '{'
			depth = 0
			buf: list[str] = []
			i = start
			while i < len(s):
				ch = s[i]
				if ch == '{':
					depth += 1
					if depth > 1:
						buf.append(ch)
				elif ch == '}':
					depth -= 1
					if depth == 0:
						return ("".join(buf), i + 1)
					buf.append(ch)
				else:
					buf.append(ch)
				i += 1
			return ("", i)

		# Replace \frac{a}{b} recursively
		while "\\frac{" in l:
			idx = l.find("\\frac{")
			# locate numerator
			num_start = idx + len("\\frac")
			if num_start >= len(l) or l[num_start] != '{':
				break
			num, after_num = extract_braced(l, num_start)
			if after_num >= len(l) or l[after_num] != '{':
				break
			den, after_den = extract_braced(l, after_num)
			repl = f"({num})/({den})"
			l = l[:idx] + repl + l[after_den:]

		# Replace \sqrt{a} with sqrt(a)
		while "\\sqrt{" in l:
			idx = l.find("\\sqrt{")
			arg, nxt = extract_braced(l, idx + len("\\sqrt"))
			repl = f"sqrt({arg})"
			l = l[:idx] + repl + l[nxt:]

		# Superscripts: x^{2} -> x^2
		l = re.sub(r"\^\{([^{}]+)\}", r"^\1", l)
		# Remove extraneous braces around tokens
		l = re.sub(r"\{\s*([A-Za-z0-9\\()+\-*/^]+)\s*\}", r"\1", l)
		# Normalize spaces
		l = " ".join(l.split())
		return l
