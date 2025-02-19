import streamlit as st
import pandas as pd
from datetime import datetime
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# ページ設定
st.set_page_config(
    page_title="EGAO-AI デモ",
    page_icon="👥",
    layout="wide"
)

# セッション状態の初期化
if 'generated_care_plan' not in st.session_state:
    st.session_state.generated_care_plan = None

def mock_generate_care_plan(user_info, adl_data, client_needs):
    """ケアプラン生成のモック関数"""
    return f"""
    # ケアプラン（サンプル）

    ## 利用者情報
    - 名前: {user_info.get('name', '名前未設定')}
    - 年齢: {user_info.get('age', '年齢未設定')}
    - 要介護度: {user_info.get('care_level', '要介護度未設定')}

    ## ADL評価
    {pd.DataFrame([adl_data]).T.to_string()}

    ## 利用者の要望
    {client_needs}

    ## 提案されるケアプラン
    1. 日常生活の支援計画
       - 食事: 必要に応じた介助を提供
       - 入浴: 安全な入浴環境の確保
       - 移動: 適切な補助具の使用

    2. リハビリテーション計画
       - 週3回の機能訓練
       - 日常生活動作の練習

    3. 社会参加支援
       - レクリエーションへの参加促進
       - 家族との交流機会の確保
    """

def main():
    st.title("EGAO-AI ケアプラン作成支援システム")
    
    # サイドバー
    with st.sidebar:
        st.header("メニュー")
        page = st.radio(
            "選択してください",
            ["基本情報入力", "ADLデータ入力", "ケアプラン生成", "履歴管理"]
        )
    
    if page == "基本情報入力":
        st.header("基本情報入力")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("利用者名")
            age = st.number_input("年齢", min_value=0, max_value=150)
            gender = st.selectbox("性別", ["選択してください", "男性", "女性"])
            
        with col2:
            care_level = st.selectbox(
                "要介護度",
                ["選択してください", "要介護1", "要介護2", "要介護3", "要介護4", "要介護5"]
            )
            family_structure = st.text_input("家族構成")
            key_person = st.text_input("キーパーソン")
        
        if st.button("基本情報を保存"):
            if name and age > 0 and gender != "選択してください" and care_level != "選択してください":
                st.session_state.user_info = {
                    "name": name,
                    "age": age,
                    "gender": gender,
                    "care_level": care_level,
                    "family_structure": family_structure,
                    "key_person": key_person
                }
                st.success("基本情報が保存されました")
                st.write(st.session_state.user_info)
            else:
                st.warning("必須項目を入力してください")
    
    elif page == "ADLデータ入力":
        st.header("ADLデータ入力")
        
        # ADL項目の定義
        adl_items = [
            "食事", "排泄", "入浴", "移動", "着替え", "整容",
            "コミュニケーション", "認知機能", "睡眠",
            "服薬管理", "金銭管理", "買い物"
        ]
        
        # ADLデータ入力フォーム
        adl_data = {}
        for item in adl_items:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write(item)
            with col2:
                adl_data[item] = st.select_slider(
                    f"{item}の状態",
                    options=["要全介助", "一部介助", "見守り", "自立"],
                    key=f"adl_{item}",
                    label_visibility="collapsed"
                )
        
        if st.button("ADLデータを保存"):
            st.session_state.adl_data = adl_data
            st.success("ADLデータが保存されました")
            st.write(pd.DataFrame([adl_data]).T)
    
    elif page == "ケアプラン生成":
        st.header("ケアプラン生成")
        
        # 保存された情報の確認
        if 'user_info' not in st.session_state or 'adl_data' not in st.session_state:
            st.warning("基本情報とADLデータを先に入力してください")
            return
        
        # 利用者の要望入力
        st.subheader("利用者の要望")
        client_needs = st.text_area(
            "具体的な要望を入力してください",
            height=100,
            placeholder="例：母親の結婚式に参加したい"
        )
        
        # ケアプラン生成ボタン
        if st.button("ケアプランを生成"):
            if not client_needs:
                st.warning("利用者の要望を入力してください")
                return
                
            with st.spinner("ケアプランを生成中..."):
                care_plan = mock_generate_care_plan(
                    st.session_state.user_info,
                    st.session_state.adl_data,
                    client_needs
                )
                
                if care_plan:
                    st.session_state.generated_care_plan = care_plan
                    st.success("ケアプランが生成されました")
                    
                    # ケアプランの表示
                    st.subheader("生成されたケアプラン")
                    st.markdown(care_plan)
                    
                    # ダウンロードボタン
                    st.download_button(
                        "ケアプランをダウンロード",
                        care_plan,
                        "care_plan.txt",
                        "text/plain"
                    )
    
    elif page == "履歴管理":
        st.header("履歴管理")
        st.info("この機能は開発中です")

if __name__ == "__main__":
    main()