import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ocr import OCRProcessor
from llm import ReceiptAnalyzer
from database.db import DatabaseManager


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
    if not raw_text:
        print("Failed to extract text")
        return

    # LLM解析
    print("Analyzing")
    analyzer = ReceiptAnalyzer()
    structured_data = analyzer.parse_receipt(raw_text)

    # Databse保存
    print("-" * 30)
    print("Saving to Database")

    db_manager = DatabaseManager()
    try:
        # DBへ保存
        saved_record = db_manager.save_receipt(structured_data, image_path)

        print("\n[SUCCESS] Data saved successfully")
        print(f"ID: {saved_record.id}")
        print(f"Store: {saved_record.store_name}")
        print(f"Date: {saved_record.purchase_date}")
        print(f"Amount: ￥{saved_record.total_amount}")
        print(f"Category: {saved_record.category}")

    except Exception as e:
        print(f"[ERROR] Failed to save to database: {e}")


if __name__ == "__main__":
    main()
