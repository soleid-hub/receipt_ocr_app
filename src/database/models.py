from sqlalchemy import Column, Integer, String, Date, JSON, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Receipt(Base):
    """
    receiptsテーブルのスキーマ定義
    """

    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_name = Column(String, nullable=True)
    purchase_date = Column(Date, nullable=True)
    total_amount = Column(Integer, nullable=True)
    category = Column(String, nullable=True)
    items = Column(JSON, nullable=True)
    image_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Receipt(id={self.id}, store={self.store_name}, amount={self.total_amount})>"
