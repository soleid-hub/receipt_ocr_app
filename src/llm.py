import os 
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class ReceiptAnalyzer:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-lite",
            generation_config={"response_mime_type": "application/json"}
        )

    def parse_receipt(self, raw_text: str) -> dict:
        """
        OCRテキストを受け取り、構造化されたJSONデータを返す
        """
        print("Analyzing text with Gemini...")

        prompt = f"""
        あなたはレシート処理の専門家です。
        以下のOCRで読み取ったテキストから、重要な情報を抽出し、JSON形式で出力してください。

        # 要件
        - date: 日付 (YYYY-MM-DD形式)。不明な場合は null。
        - store_name: 店舗名。
        - items: 購入品目のリスト [{{"name": "商品名", "price": 金額}}, ...]
        - total_amount: 合計金額 (数値)。
        - category: 一般的な支出カテゴリ (例: 食費, 交通費, 日用品, 交際費, その他)。推測してください。

        # OCRテキスト
        {raw_text}
        """

        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error in LLM processing: {e}")
            return {}