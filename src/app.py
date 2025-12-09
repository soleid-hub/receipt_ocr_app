import streamlit as st
import os
import sys
import pandas as pd
import altair as alt
from datetime import  date

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ocr import OCRProcessor
from llm import ReceiptAnalyzer
from database.db import DatabaseManager
from database.models import Receipt

#設定
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="レシート自動仕訳システム", layout="wide")

def main():
    st.title("レシート仕訳システム")

    db_manager = DatabaseManager()

    # データ取得と集計処理
    session = db_manager.get_session()
    df = pd.DataFrame()
    try:
        all_records = session.query(Receipt).all()
        if all_records:
            data_list = [
                {
                    "date" : r.purchase_date,
                    "amount" : r.total_amount,
                    "category" : r.category,
                    "store" : r.store_name
                }
                for r in all_records if r.purchase_date is not None
            ]
            df = pd.DataFrame(data_list)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
    finally:
        session.close()

    # タブ切り替え
    tab1, tab2 = st.tabs(["レシート入力・編集", "分析・レポート"])

    # レシート入力・編集
    with tab1:
        st.markdown("画像をアップロードすると、自動で内容を読み取り、仕訳を行います")

    # サイドバーに履歴表示
        with st.sidebar:
            st.header("保存済みレシート（最新10件）")
            session = db_manager.get_session()
            try:
                # 最新10件を取得
                records = session.query(Receipt).order_by(Receipt.id.desc()).limit(10).all()

                if records:
                    for r in records:
                        date_str = r.purchase_date.strftime("%Y-%m-%d") if r.purchase_date else "日付不明"
                        st.text(f"ID:{r.id} | {date_str}")
                        st.caption(f"￥{r.total_amount:,} ({r.store_name})")
                        st.divider()
                else:
                    st.info("データはまだありません")
            finally:
                session.close()

        # メイン画面
        uploaded_file = st.file_uploader("レシート画像をアップロードしてください", type=["jpg","png","webp","jpeg"])

        if uploaded_file is not None:
            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            col1, col2 = st.columns([1,1.5])

            with col1:
                st.image(file_path, caption="アップロード画像", use_container_width=True)

            # 解析処理、編集、保存
            with col2:
                st.subheader("解析結果")

                if "current_image" not in st.session_state or st.session_state["current_image"] != uploaded_file.name:
                    st.session_state["analyzed_data"] = None
                    st.session_state["current_image"] = uploaded_file.name

                if st.session_state.get("analyzed_data") is None:
                    if st.button("AIで解析を開始する", type="primary"):
                        with st.spinner("OCRで文字を読み取り中"):
                            # OCR実行
                            ocr = OCRProcessor()
                            raw_text = ocr.extract_text(file_path)

                        if raw_text:
                            with st.spinner("構造化データに変換中"):
                                # LLM解析
                                analyzer = ReceiptAnalyzer()
                                result = analyzer.parse_receipt(raw_text)

                                if not result:
                                    st.error("AI解析に失敗しました")
                                else:
                                    st.session_state["analyzed_data"] = result
                                    st.rerun()
                        else:
                            st.error("文字を読み取れませんでした")

                data = st.session_state.get("analyzed_data")

                if data:
                    with st.form("edit_form"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            # 日付と店名の編集
                            edited_date = st.text_input("日付（YYYY-MM-DD）", value=data.get("date"))
                            edited_store = st.text_input("店舗名", value=data.get("store_name"))
                        with col_b:
                            # 金額とカテゴリの編集
                            init_amount = data.get("total_amount")
                            if init_amount is None: 
                                init_amount = 0
                            edited_amount = st.number_input("合計金額", value=int(init_amount))

                            categories = ["食費", "日用品","交通費","交際費","その他"]
                            current_cat = data.get("category","その他")

                            cat_index = categories.index(current_cat) if current_cat in categories else 4
                            edited_category = st.selectbox("カテゴリ", categories, index=cat_index)

                        st.markdown("---")
                        st.caption("明細データ（自動抽出）")
                        items_df =pd.DataFrame(data.get("items",[]))
                        if not items_df.empty:
                            st.dataframe(items_df, hide_index=True, use_container_width=True)
                        else:
                            st.info("明細は検出されませんでした")

                        st.markdown("---")
                        submitted = st.form_submit_button("この内容でデータベースに保存", type="primary")

                        if submitted:
                            final_data = {
                                "store_name": edited_store,
                                "date": edited_date,
                                "total_amount" : edited_amount,
                                "category" : edited_category,
                                "items" : data.get("items",[])
                            }  
                            try:
                                # DB保存
                                saved_record = db_manager.save_receipt(final_data, file_path)
                                st.success(f"保存しました(ID:{saved_record.id})")

                                st.session_state["analyzed_data"] = None
                            except Exception as e:
                                st.error(f"保存エラー:{e}")

                elif st.session_state.get("analyzed_data") is not None:
                    st.warning("解析結果が空でした")
                    if st.button("リセット"):
                        st.session_state["analyzed_data"] = None
                        st.rerun()

    # 分析・レポート
    with tab2:
        if df.empty:
            st.info("データがまだありません。")
        else:
            # 合計金額・前月比表示
            st.subheader("支出サマリー")

            # 日付計算
            today = date.today()
            this_month_start = pd.to_datetime(date(today.year, today.month,1))
            last_month_start = this_month_start - pd.DateOffset(months=1)
            next_month_start = this_month_start + pd.DateOffset(months=1)

            # 全期間合計
            total_expense = df["amount"].sum()

            # 今月の支出
            this_month_df = df[(df["date"] >= this_month_start) & (df["date"] < next_month_start)]
            this_month_total = this_month_df["amount"].sum()

            # 先月の支出
            last_month_df = df[(df["date"] >= last_month_start) & (df["date"] < this_month_start)]
            last_month_total = last_month_df["amount"].sum() 

            # 前月比計算
            diff = this_month_total - last_month_total

            # 数値表示   
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("全期間の支出合計", f"￥{total_expense:,.0f}")
            kpi2.metric("今月の支出", f"￥{this_month_total:,.0f}")
            kpi3.metric("前月比", f"￥{diff:,.0f}", delta=f"{diff:,.0f}円", delta_color="inverse")

            st.divider()

            # グラフ表示
            chart_col1, chart_col2 = st.columns(2)

            # カテゴリ別円グラフ
            with chart_col1:
                st.subheader("カテゴリ別割合")
                category_sum = df.groupby("category", as_index=False)["amount"].sum()

                pie_chart = alt.Chart(category_sum).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="amount", type="quantitative"),
                    color=alt.Color(field="category", type="nominal"),
                    tooltip=["category","amount"],
                    order=alt.Order("amount",sort="descending")
                ).properties(title="カテゴリ別支出構成")

                st.altair_chart(pie_chart, use_container_width=True)

            # 月別支出推移
            with chart_col2:
                st.subheader("月別支出推移")
                monthly_trend = df.set_index("date").resample("ME")["amount"].sum()

                st.line_chart(monthly_trend)

            with st.expander("全データリストを見る"):
                st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)
                

if __name__ == "__main__":
    main()