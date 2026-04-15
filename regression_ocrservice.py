# regression_ocr_service.py

from __future__ import annotations
import io
import re
from typing import Any
import numpy as np
from PIL import Image

try:
    from paddleocr import PaddleOCR
    OCR_AVAILABLE = True
except Exception:
    PaddleOCR = None
    OCR_AVAILABLE = False


class RegressionOCRService:
    def __init__(self) -> None:
        self.ocr = None
        self._init_model()
        print("OCR AVAILABLE:", OCR_AVAILABLE)
        print("OCR OBJECT:", self.ocr)

    def _init_model(self):
        if OCR_AVAILABLE:
            try:
                self.ocr = PaddleOCR(use_angle_cls=True, lang="en")
                print("[Regression OCR] PaddleOCR loaded")
            except Exception as e:
                print("[Regression OCR] Failed:", e)
                self.ocr = None

    async def process_image_bytes(self, image_bytes: bytes) -> dict[str, Any]:
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            return {"success": False, "error": str(e)}

        text = self._run_ocr(image)
        print("RAW OCR OUTPUT:", text)

        # Extract numbers from OCR text
        x_values, y_values = self._extract_xy_values(text)

        return {
            "success": True,
            "original_text": text,
            "x_values": x_values,
            "y_values": y_values
        }

    def _run_ocr(self, image: Image.Image) -> str:
        if self.ocr is None:
            return ""

        img_np = np.array(image)
        result = self.ocr.ocr(img_np, cls=True)

        lines = []
        for page in result or []:
            for detection in page:
                try:
                    text = detection[1][0]
                    if text.strip():
                        lines.append(text.strip())
                except:
                    continue

        return "\n".join(lines)

    def _extract_xy_values(self, text: str):
        """
        Extract numbers and split into X and Y.
        Assumes:
        - First half numbers = X
        - Second half numbers = Y
        """

        # Extract all numbers (integer + decimal)
        numbers = re.findall(r'-?\d+\.?\d*', text)

        if len(numbers) < 2:
            return "", ""

        half = len(numbers) // 2

        x_vals = numbers[:half]
        y_vals = numbers[half:]

        return ",".join(x_vals), ",".join(y_vals)