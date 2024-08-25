import streamlit as st
from openai import OpenAI
import requests
import random
import time
import os 
from difflib import get_close_matches
from bs4 import BeautifulSoup
from dotenv import load_dotenv  # dotenvをインポート

# .envファイルの内容を読み込む
load_dotenv()

# OpenAI APIキーを設定
api_key = api_key = os.getenv("OPENAI_API_KEY")

# OpenAIクライアントの初期化
client = OpenAI()

# 楽天APIのアプリケーションIDを設定
rakuten_api_key = os.getenv("RAKUTEN_API_KEY")

# 名詞リスト
NOUN_LIST = [
    "牛肉", "豚肉", "鶏肉", "ひき肉", "ベーコン", "ソーセージ", "ウインナー", "ハム",
    "サーモン", "鮭", "いわし", "さば", "あじ", "ぶり", "さんま", "鯛", "マグロ",
    "たら", "エビ", "いか", "たこ", "かに", "牡蠣", "貝類", "明太子", "魚卵",
    "なす", "かぼちゃ", "大根", "きゅうり", "じゃがいも", "さつまいも", "キャベツ",
    "白菜", "トマト", "もやし", "小松菜", "ほうれん草", "ごぼう", "アボカド", "玉ねぎ",
    "ブロッコリー", "にんじん", "春野菜", "夏野菜", "秋野菜", "冬野菜", "きのこ", "ハーブ",
    "練物", "加工食品", "チーズ", "ヨーグルト", "こんにゃく", "しらたき", "海藻", "乾物",
    "漬物", "もち米", "もち麦", "マカロニ", "ペンネ", "ホットケーキミックス", "粉類",
    "オムライス", "チャーハン", "パエリア", "タコライス", "チキンライス", "ハヤシライス",
    "ロコモコ", "ピラフ", "ハッシュドビーフ", "寿司", "丼物", "炊き込みご飯", "おかゆ",
    "雑炊", "おにぎり", "アレンジごはん", "カルボナーラ", "ミートソース", "ナポリタン",
    "ペペロンチーノ", "ジェノベーゼ", "ペスカトーレ", "たらこパスタ", "明太子パスタ",
    "ボンゴレ", "アラビアータ", "トマトクリームパスタ", "納豆パスタ", "クリーム系パスタ",
    "オイル", "塩系パスタ", "チーズ系パスタ", "バジルソース系パスタ", "和風パスタ",
    "きのこパスタ", "ツナパスタ", "冷製パスタ", "スープスパ", "スープパスタ", "パスタソース",
    "ニョッキ", "ラザニア", "ラビオリ", "うどん", "蕎麦", "そうめん", "焼きそば",
    "ラーメン", "冷やし中華", "つけ麺", "お好み焼き", "たこ焼き", "粉物料理", "味噌汁",
    "豚汁", "けんちん汁", "お吸い物", "かぼちゃスープ", "野菜スープ", "チャウダー",
    "クラムチャウダー", "コーンスープ", "ポタージュ", "トマトスープ", "コンソメスープ",
    "クリームスープ", "中華スープ", "和風スープ", "韓国風スープ", "ポトフ",
    "ポテトサラダ", "タラモサラダ", "マカロニサラダ", "スパゲティサラダ", "シーザーサラダ",
    "大根サラダ", "春雨サラダ", "コールスロー", "キャロットラペ", "かぼちゃサラダ",
    "ごぼうサラダ", "コブサラダ", "ホットサラダ", "温野菜", "ジャーサラダ", "マヨネーズ",
    "ナンプラー", "ソース", "タレ", "つゆ", "だし", "ドレッシング", "発酵食品",
    "発酵調味料", "スパイス", "柚子胡椒", "オリーブオイル", "ココナッツオイル", "ごま油",
    "エスニック調味料", "中華調味料", "キャラ弁", "おかず", "運動会", "お花見", "遠足",
    "ピクニック", "色別", "作り置き", "冷凍", "すきま", "使い回し", "子供", "大人", "部活",
    "クッキー", "スイートポテト", "チーズケーキ", "シフォンケーキ", "パウンドケーキ",
    "ケーキ", "ホットケーキ", "パンケーキ", "タルト", "パイ", "チョコレート", "スコーン",
    "マフィン", "焼き菓子", "プリン", "ドーナツ", "シュークリーム", "エクレア", "ゼリー",
    "寒天", "ムース", "アイス", "シャーベット", "和菓子", "クリーム", "ジャム", "サンドイッチ",
    "フレンチトースト", "食パン", "蒸しパン", "ホットサンド", "惣菜パン", "菓子パン"
]

# カテゴリ一覧を取得する
def get_category_list(application_id):
    url = f'https://app.rakuten.co.jp/services/api/Recipe/CategoryList/20170426?applicationId={application_id}'
    res = requests.get(url)
    json_data = res.json()
    if 'result' in json_data:
        return json_data['result']
    else:
        st.error(f"エラー: 'result'キーが見つかりません。レスポンス内容: {json_data}")
        return None

# カテゴリをキーワードで検索
def search_category_by_keyword(categories, keyword):
    matching_categories = []
    for category_type in ['large', 'medium', 'small']:
        for category in categories.get(category_type, []):
            if keyword in category['categoryName']:
                if category_type == 'large':
                    matching_categories.append({
                        'categoryId': category['categoryId'],
                        'categoryName': category['categoryName']
                    })
                elif category_type == 'medium':
                    matching_categories.append({
                        'categoryId': f"{category['parentCategoryId']}-{category['categoryId']}",
                        'categoryName': category['categoryName']
                    })
                else:  # small category
                    parent_medium_id = category['parentCategoryId']
                    medium_category = next((cat for cat in categories.get('medium', []) if cat['categoryId'] == parent_medium_id), None)
                    if medium_category:
                        large_category_id = medium_category['parentCategoryId']
                        matching_categories.append({
                            'categoryId': f"{large_category_id}-{medium_category['categoryId']}-{category['categoryId']}",
                            'categoryName': category['categoryName']
                        })
    return matching_categories

# レシピを取得する
def get_recipes_by_category(application_id, category_id):
    url = f'https://app.rakuten.co.jp/services/api/Recipe/CategoryRanking/20170426?applicationId={application_id}&categoryId={category_id}'
    res = requests.get(url)
    json_data = res.json()
    if 'result' in json_data:
        return json_data['result']
    else:
        st.error(f"エラー: 'result'キーが見つかりません。レスポンス内容: {json_data}")
        return None

# ページ内容を取得する関数
def get_page_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

# レシピ情報を抽出する関数
def extract_recipe_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    ingredients_section = soup.find(class_='recipe_material__list')
    if ingredients_section:
        ingredients = [item.get_text(strip=True) for item in ingredients_section.find_all('li')]
        return ingredients
    else:
        return None

# カロリーを推定する関数
def estimate_calories(ingredients):
    prompt = f"以下の材料からカロリーを推定し、推定カロリー数値のみ提示してください:\n\n{', '.join(ingredients)}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたは栄養士です。"},
            {"role": "user", "content": prompt}
        ]
    )
    estimated_calories = response.choices[0].message.content
    return estimated_calories

# Streamlitアプリのメイン処理
def main():
    st.title("楽天レシピ提案アプリ")
    st.write("材料を入力して、レシピを検索しましょう。")

    # 入力フォーム
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

    if st.button("レシピを表示"):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Based on the following information, suggest a keyword for a recipe: Cuisine type: {cuisine_type}, Season: {season}, Dish type: {dish_type}."}
                ],
                max_tokens=50
            )

            keyword = response.choices[0].message.content.strip()
            closest_match = get_close_matches(keyword, NOUN_LIST, n=1, cutoff=0.0)
            selected_keyword = closest_match[0] if closest_match else NOUN_LIST[0]

            categories = get_category_list(rakuten_api_key)
            if categories is None:
                st.error("カテゴリ一覧の取得に失敗しました。")
                return

            matching_categories = search_category_by_keyword(categories, selected_keyword)
            if not matching_categories:
                st.write(f"キーワード「{selected_keyword}」に該当するカテゴリが見つかりません。")
                return

            selected_category = random.choice(matching_categories)
            time.sleep(1)

            recipes = get_recipes_by_category(rakuten_api_key, selected_category['categoryId'])
            if recipes is None:
                st.error(f"カテゴリID: {selected_category['categoryId']} のレシピ取得に失敗しました。")
                return

            for recipe in recipes[:3]:  # 最初の3つのレシピを表示
                st.subheader(recipe['recipeTitle'])
                st.image(recipe['foodImageUrl'])
                st.write(f"作る時間: {recipe['recipeIndication']}")
                recipe_url = recipe['recipeUrl']

                # レシピのURLをハイパーリンクとして表示
                st.markdown(f"[レシピの詳細を見る]({recipe_url})")

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
        except Exception as e:
            st.write(f"エラーが発生しました: {e}")
        except OpenAI.APIError as e:
            st.write(f"API Error: {e}.")


if __name__ == "__main__":
    main()
