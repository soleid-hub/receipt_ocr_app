import logging
import os
import cv2
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

# ログ設定
logging.getLogger("ppocr").setLevel(logging.WARNING)


class OCRProcessor:
    def __init__(self, lang: str = "japan"):
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang)

    def extract_text(self, image_path: str) -> str:
        print(f"Loading image from: {image_path}")

        if not os.path.exists(image_path):
            print(f"Error: File not found at {image_path}")
            return ""

        try:
            # 画像読み込み、BGR変換
            pil_img = Image.open(image_path)
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")
            img_rgb = np.array(pil_img)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

        except Exception as e:
            print(f"Error loading image: {e}")
            return ""

        # OCR実行
        result = self.ocr.ocr(img_bgr)

        if result is None:
            return ""

        extracted_texts = []

        try:
            # 解析ロジックの分岐
            if isinstance(result, list) and len(result) > 0:
                first_item = result[0]

                # 辞書型で返ってくる場合
                if isinstance(first_item, dict) and "rec_texts" in first_item:
                    print("Debug: Detected Dictionary format output.")
                    rec_texts = first_item["rec_texts"]
                    return "\n".join(rec_texts)

                # リストのリストで返ってくる場合
                elif isinstance(first_item, list):
                    print("Debug: Detected List format output.")
                    for line in first_item:
                        if len(line) >= 2 and isinstance(line[1], (list, tuple)):
                            text = line[1][0]
                            score = line[1][1]
                            if score > 0.6:
                                extracted_texts.append(text)

                else:
                    print(
                        f"Debug: Unknown result format inside list: {type(first_item)}"
                    )
            else:
                print("Debug: Result list is empty.")

        except Exception as e:
            print(f"Debug Error parsing result: {e}")
            return ""

        return "\n".join(extracted_texts)
