import streamlit as st
import pandas as pd
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# OpenAI クライアントの設定
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

# ページ設定
st.set_page_config(
    page_title="EGAO-AI デモ",
    page_icon="👥",
    layout="wide"
)

# セッション状態の初期化
if 'generated_care_plan' not in st.session_state:
    st.session_state.generated_care_plan = None

def get_adl_status_color(status):
    """ADL状態に応じたカラーコードを返す"""
    colors = {
        "要全介助": "#ff6b6b",
        "一部介助": "#ffd93d",
        "見守り": "#a3dc2e",
        "自立": "#4CAF50"
    }
    return colors.get(status, "#ffffff")

def get_adl_description(item, status):
    """ADL項目と状態に応じた説明文を返す"""
    descriptions = {
        "食事": {
            "要全介助": "食事の全過程で介助が必要",
            "一部介助": "食事の一部で介助が必要",
            "見守り": "声かけ・見守りが必要",
            "自立": "自力で食事が可能"
        },
        "排泄": {
            "要全介助": "排泄の全過程で介助が必要",
            "一部介助": "排泄の一部で介助が必要",
            "見守り": "声かけ・見守りが必要",
            "自立": "自力で排泄が可能"
        },
        "入浴": {
            "要全介助": "入浴の全過程で介助が必要",
            "一部介助": "入浴の一部で介助が必要",
            "見守り": "声かけ・見守りが必要",
            "自立": "自力で入浴が可能"
        }
    }
    default_descriptions = {
        "要全介助": "常時介助が必要",
        "一部介助": "部分的な介助が必要",
        "見守り": "声かけ・見守りが必要",
        "自立": "自力で可能"
    }
    return descriptions.get(item, default_descriptions).get(status, "")

def generate_care_plan(user_info, adl_data, client_needs):
    """OpenAI APIを使用してケアプラン生成"""
    try:
        prompt = f"""
以下の情報を元に、介護施設でのケアプランを作成してください。

【利用者情報】
名前: {user_info.get('name')}
年齢: {user_info.get('age')}
性別: {user_info.get('gender')}
要介護度: {user_info.get('care_level')}
家族構成: {user_info.get('family_structure')}
キーパーソン: {user_info.get('key_person')}

【ADLデータ】
{pd.DataFrame([adl_data]).T.to_string()}

【利用者の要望】
{client_needs}

以下の形式でケアプランを作成してください：

1. 課題分析（アセスメント）
2. 長期目標（3-6ヶ月）
3. 短期目標（1-3ヶ月）
4. サービス内容
5. 具体的な支援計画
6. モニタリング計画
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは介護施設のケアプランを作成する専門家です。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        return None

def render_adl_input_section(items, category_name):
    """ADL入力セクションのレンダリング"""
    st.markdown(f"#### {category_name}")
    adl_data = {}
    
    for item in items:
        st.markdown(f"##### {item}")
        selected = st.radio(
            f"{item}の状態",
            ["要全介助", "一部介助", "見守り", "自立"],
            key=f"adl_{item}",
            horizontal=True,
            label_visibility="collapsed"
        )
        
        description = get_adl_description(item, selected)
        color = get_adl_status_color(selected)
        
        st.markdown(
            f"""
            <div style="
                padding: 10px;
                border-radius: 5px;
                background-color: {color};
                color: {'white' if selected == '要全介助' else 'black'};
                margin-bottom: 10px;
            ">
                <strong>{selected}</strong>: {description}
            </div>
            """,
            unsafe_allow_html=True
        )
        
        adl_data[item] = selected
    
    return adl_data

def main():
    st.title("EGAO-AI ケアプラン作成支援システム")
    
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
        
        if st.button("基本情報を保存", type="primary"):
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
        
        adl_categories = {
            "基本動作": ["食事", "排泄", "入浴", "移動", "着替え", "整容"],
            "認知・コミュニケーション": ["コミュニケーション", "認知機能", "睡眠"],
            "社会生活": ["服薬管理", "金銭管理", "買い物"]
        }
        
        tabs = st.tabs(list(adl_categories.keys()))
        all_adl_data = {}
        
        for tab, (category, items) in zip(tabs, adl_categories.items()):
            with tab:
                category_data = render_adl_input_section(items, category)
                all_adl_data.update(category_data)
        
        if st.button("ADLデータを保存", type="primary"):
            st.session_state.adl_data = all_adl_data
            st.success("ADLデータが保存されました")
            st.write(pd.DataFrame([all_adl_data]).T)

    elif page == "ケアプラン生成":
        st.header("ケアプラン生成")
        
        if 'user_info' not in st.session_state or 'adl_data' not in st.session_state:
            st.warning("基本情報とADLデータを先に入力してください")
            return
        
        st.subheader("利用者の要望")
        client_needs = st.text_area(
            "具体的な要望を入力してください",
            height=100,
            placeholder="例：母親の結婚式に参加したい"
        )
        
        if st.button("ケアプランを生成", type="primary"):
            if not client_needs:
                st.warning("利用者の要望を入力してください")
                return
                
            with st.spinner("ケアプランを生成中..."):
                care_plan = generate_care_plan(
                    st.session_state.user_info,
                    st.session_state.adl_data,
                    client_needs
                )
                
                if care_plan:
                    st.session_state.generated_care_plan = care_plan
                    st.success("ケアプランが生成されました")
                    
                    st.subheader("生成されたケアプラン")
                    st.markdown(care_plan)
                    
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