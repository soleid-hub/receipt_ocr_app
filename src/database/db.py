from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from .models import Base, Receipt

DATABASE_URL ="sqlite:///./receipts.db"

class DatabaseManager:
    def __init__(self, url: str = DATABASE_URL):
        self.engine = create_engine(url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        #テーブル作成
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """新しいセッションを作成して返す"""
        return self.SessionLocal()
    
    def save_receipt(self, data: dict, image_path: str) -> Receipt:
        """
        解析済みデータと画像パスを受け取りDBに保存する
        """
        session = self.get_session()

        try:
            # 日付文字列の変換
            date_obj = None
            if data.get("date"):
                try:
                    date_obj = datetime.strptime(data["date"], "%Y-%m-%d").date()
                except ValueError:
                    print(f"Warning: Could not parse date format: {data["date"]}")

            #　モデルインスタンスの作成
            new_receipt = Receipt(
                store_name=data.get("store_name"),
                purchase_date=date_obj,
                total_amount=data.get("total_amount"),
                category=data.get("category"),
                items=data.get("items",[]),
                image_path=image_path
            )

            # 保存実行
            session.add(new_receipt)
            session.commit()
            session.refresh(new_receipt)

            return new_receipt
        
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
