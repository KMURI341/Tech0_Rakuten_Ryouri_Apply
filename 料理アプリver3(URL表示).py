import streamlit as st
import requests

# 入力フォーム
st.title("楽天レシピ提案アプリ")
cuisine_type = st.selectbox(
    "料理のジャンルを選択してください",
    ["日本料理", "中華料理", "フレンチ料理", "イタリア料理", "韓国料理", "その他"]
)

season = st.selectbox(
    "季節を選択してください",
    ["春", "夏", "秋", "冬"]
)

dish_type = st.selectbox(
    "料理の種類を選択してください",
    ["前菜", "主菜", "副菜", "サラダ", "汁物", "デザート", "その他"]
)

# APIリクエストを送信する関数
def get_recipes(cuisine_type, dish_type):
    # カテゴリに応じたAPIのカテゴリIDなどを設定（仮のIDを使用）
    category_id = {
        "日本料理": "48",
        "中華料理": "41",
        "フレンチ料理": "44",
        "イタリア料理": "43",
        "韓国料理": "42",
        "その他": "46"
    }[cuisine_type]

    url = 'https://app.rakuten.co.jp/services/api/Recipe/CategoryRanking/20170426'
    rakuten_api_key = "1042255002923493931"
    params = {
        'format': 'json',
        'applicationId': rakuten_api_key,
    }
    response = requests.get(url, params)
    return response.json()

from bs4 import BeautifulSoup
from openai import OpenAI

import os 
api_key = os.getenv("OPENAI_API_KEY")

# OpenAIクライアントの初期化
client = OpenAI(api_key=api_key)

def get_page_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

def extract_recipe_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # 'recipe_material' クラスを持つ要素を探す
    ingredients_section = soup.find(class_='recipe_material__list')
    if ingredients_section:
        # 各材料をリストとして抽出
        ingredients = [item.get_text(strip=True) for item in ingredients_section.find_all('li')]
        return ingredients
    else:
        return None

def estimate_calories(ingredients):
    prompt = f"以下の材料からカロリーを推定してください:\n\n{', '.join(ingredients)}"
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "あなたは栄養士です。"},
            {"role": "user", "content": prompt}
        ]
    )
    
    # 修正部分: messageオブジェクトに直接アクセスする
    estimated_calories = response.choices[0].message.content
    return estimated_calories

# コード1: レシピ提案ボタンの処理
if st.button("レシピを提案する"):
    data = get_recipes(cuisine_type, dish_type)
    
    # レシピのフィルタリング（仮の条件でフィルタリング）
    if data:
        recipes = data['result'][:3]  # 最初の3つのレシピを取得
        
        # データの表示
        for recipe in recipes:
            st.subheader(recipe['recipeTitle'])
            st.image(recipe['foodImageUrl'])
            st.write(f"作る時間: {recipe['recipeIndication']}")
            
            #レシピのURL先を表示(markdown構文)
            recipe_url = recipe.get('recipeUrl')  
            # st.markdownでリンクを表示する際に、リンクが外部リンク（ウェブページ）であることを明示する必要があります。これを行うためには、リンクを含むst.markdownにunsafe_allow_html=Trueを追加して、HTML形式でリンクを表示する方法があります。
            st.markdown(f'<a href="{recipe_url}" target="_blank">レシピの詳細はこちら</a>', unsafe_allow_html=True)

            # コード2: 取得したURLを使ってカロリー推定を実行
            html_content = get_page_content(recipe_url)
            
            if html_content:
                ingredients = extract_recipe_info(html_content)
                if ingredients:
                    estimated_calories = estimate_calories(ingredients)
                    st.write(f"推定カロリー: {estimated_calories}")
                else:
                    st.write("材料を抽出できませんでした。")
            else:
                st.write("ページの内容を取得できませんでした。")
    else:
        st.write("データが見つかりませんでした。")


