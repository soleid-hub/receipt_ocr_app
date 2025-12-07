import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ocr import OCRProcessor
from llm import ReceiptAnalyzer

def main():
    # 画像パス
    image_path = "data/receipt_sample.jpg"

    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        return
    
    # OCR実行
    print(f"Processing image: {image_path}")
    ocr_engine = OCRProcessor()
    raw_text = ocr_engine.extract_text(image_path)

    # OCR結果の表示
    print("-" * 30)
    print("Raw OCR Output:")
    print(raw_text[:200] + "..." if len(raw_text) > 200 else raw_text)
    print("-" * 30)

    # LLM解析
    print("Analyzing")
    analyzer = ReceiptAnalyzer()
    structured_data = analyzer.parse_receipt(raw_text)

    # 結果の表示
    print("Structured JSON Output:")
    print(json.dumps(structured_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()