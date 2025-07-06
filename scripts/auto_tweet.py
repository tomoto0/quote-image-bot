#!/usr/bin/env python3
"""
自動名言ツイートスクリプト
GitHub Actionsで定期実行され、Gemini APIで名言を生成し、
背景画像と合成してTwitterに投稿します。
"""

import os
import sys
import json
import random
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import tempfile
import tweepy
import google.generativeai as genai

def setup_apis():
    """APIクライアントをセットアップ"""
    # Gemini API
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    
    # Twitter API
    # tweepy.Clientを使用するように変更
    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
    )
    
    # v1.1 API for media upload
    auth_v1_1 = tweepy.OAuthHandler(
        os.environ["TWITTER_API_KEY"],
        os.environ["TWITTER_API_SECRET"]
    )
    auth_v1_1.set_access_token(
        os.environ["TWITTER_ACCESS_TOKEN"],
        os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
    )
    api_v1_1 = tweepy.API(auth_v1_1)
    
    return model, client, api_v1_1

def get_english_quote():
    """ZenQuotes APIから英語の名言を取得"""
    try:
        response = requests.get("https://zenquotes.io/api/random")
        response.raise_for_status() # HTTPエラーがあれば例外を発生させる
        data = response.json()
        if data and len(data) > 0:
            quote = data[0]["q"]
            author = data[0]["a"]
            return quote, author
    except Exception as e:
        print(f"Error fetching English quote from ZenQuotes: {e}")
    return None, None

def translate_quote(model, text):
    """Gemini APIを使用してテキストを日本語に翻訳"""
    try:
        prompt = f"以下の英語の名言を日本語に翻訳してください。\n\n{text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error translating quote: {e}")
    return ""

def generate_quote(model):
    """英語の名言を取得し、日本語に翻訳して返す"""
    english_quote, english_author = get_english_quote()
    if english_quote and english_author:
        japanese_translation = translate_quote(model, english_quote)
        return english_quote, english_author, japanese_translation
    
    # フォールバック名言
    fallback_quotes = [
        ("Life is what happens when you\\\\'re busy making other plans.", "John Lennon", "人生とは、他の計画を立てるのに忙しいときに起こるものだ。"),
        ("The only way to do great work is to love what you do.", "Steve Jobs", "素晴らしい仕事をする唯一の方法は、自分のやっていることを愛することだ。"),
        ("In three words I can sum up everything I\\\\'ve learned about life: it goes on.", "Robert Frost", "人生について学んだすべてを3つの言葉で要約できる。それは続くということだ。")
    ]
    return random.choice(fallback_quotes)

def get_background_image():
    """背景画像を取得"""
    background_types = [
        "nature landscape mountains",
        "ocean sunset beautiful",
        "forest peaceful serene",
        "sky clouds dramatic",
        "abstract geometric minimal",
        "vintage texture paper"
    ]
    
    try:
        if "UNSPLASH_ACCESS_KEY" in os.environ:
            # Unsplash APIを使用
            query = random.choice(background_types)
            url = f"https://api.unsplash.com/photos/random"
            params = {
                "query": query,
                "orientation": "landscape",
                "w": 800,
                "h": 600
            }
            headers = {
                "Authorization": f"Client-ID {os.environ['UNSPLASH_ACCESS_KEY']}"
            }
            
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                image_url = data["urls"]["regular"]
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    return Image.open(BytesIO(image_response.content))
    except Exception as e:
        print(f"Error fetching background image: {e}")
    
    # フォールバック: グラデーション背景を生成
    img = Image.new("RGB", (800, 600), color="#667eea")
    draw = ImageDraw.Draw(img)
    
    # 簡単なグラデーション効果
    for y in range(600):
        r = int(102 + (118 - 102) * y / 600)
        g = int(126 + (75 - 126) * y / 600)
        b = int(234 + (162 - 234) * y / 600)
        draw.line([(0, y), (800, y)], fill=(r, g, b))
    
    return img

def create_quote_image(quote, author, japanese_translation, background_img):
    """名言画像を生成"""
    # 背景画像をリサイズ
    background_img = background_img.resize((800, 600), Image.Resampling.LANCZOS)
    
    # オーバーレイを追加
    overlay = Image.new("RGBA", (800, 600), (0, 0, 0, 100))
    background_img = Image.alpha_composite(background_img.convert("RGBA"), overlay)
    
    draw = ImageDraw.Draw(background_img)
    
    try:
        # フォントを設定（システムフォントを使用）
        quote_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        author_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        japanese_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20) # 日本語訳用フォント
    except:
        # フォントが見つからない場合はデフォルトフォント
        quote_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
        japanese_font = ImageFont.load_default()
    
    # テキストを描画
    text_color = (255, 255, 255)
    
    # 名言を複数行に分割
    max_width = 700
    words = list(quote)
    lines = []
    current_line = ""
    
    for char in words:
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=quote_font)
        if bbox[2] - bbox[0] > max_width and current_line:
            lines.append(current_line)
            current_line = char
        else:
            current_line = test_line
    
    if current_line:
        lines.append(current_line)
    
    # 名言を描画
    total_height = len(lines) * 50
    start_y = 250 - total_height // 2
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=quote_font)
        text_width = bbox[2] - bbox[0]
        x = (800 - text_width) // 2
        y = start_y + i * 50
        draw.text((x, y), line, fill=text_color, font=quote_font)
    
    # 作者名を描画
    author_text = f"- {author}"
    bbox = draw.textbbox((0, 0), author_text, font=author_font)
    author_width = bbox[2] - bbox[0]
    author_x = (800 - author_width) // 2
    author_y = start_y + len(lines) * 50 + 30
    draw.text((author_x, author_y), author_text, fill=text_color, font=author_font)

    # 日本語訳を描画
    if japanese_translation:
        japanese_text = f"({japanese_translation})"
        bbox = draw.textbbox((0, 0), japanese_text, font=japanese_font)
        japanese_width = bbox[2] - bbox[0]
        japanese_x = (800 - japanese_width) // 2
        japanese_y = author_y + 30
        draw.text((japanese_x, japanese_y), japanese_text, fill=text_color, font=japanese_font)
    
    return background_img.convert("RGB")

def post_to_twitter(client, api_v1_1, quote, author, japanese_translation, image):
    """Twitterに投稿"""
    try:
        # 画像を一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            image.save(tmp_file.name, "PNG")
            
            # ツイート文を作成
            tweet_text = f"\"{quote}\" - {author}\n({japanese_translation})\n\n#名言 #格言 #inspiration #quote"
            
            # 文字数制限をチェック
            if len(tweet_text) > 280:
                # 長すぎる場合は短縮
                # 日本語訳を含めた長さを考慮
                base_len = len(f" - {author}\n()\n\n#名言 #格言 #inspiration #quote")
                max_english_quote_len = 280 - base_len - len(japanese_translation) - 5 # 5は余裕
                if len(quote) > max_english_quote_len:
                    quote = quote[:max_english_quote_len-3] + "..."
                tweet_text = f"\"{quote}\" - {author}\n({japanese_translation})\n\n#名言 #格言 #inspiration #quote"
            
            # 画像をv1.1 APIでアップロード
            media = api_v1_1.media_upload(tmp_file.name)
            
            # ツイートをv2 APIで投稿
            response = client.create_tweet(text=tweet_text, media_ids=[media.media_id])
            
            print(f"Successfully tweeted: {tweet_text}")
            print(f"Tweet ID: {response.data['id']}")
            
            # 一時ファイルを削除
            os.unlink(tmp_file.name)
            
    except Exception as e:
        print(f"Error posting to Twitter: {e}")
        raise

def main():
    """メイン処理"""
    try:
        print("Setting up APIs...")
        model, client, api_v1_1 = setup_apis()
        
        print("Generating quote...")
        english_quote, english_author, japanese_translation = generate_quote(model)
        print(f"Generated quote: \'{english_quote}\' - {english_author} ({japanese_translation})")
        
        print("Getting background image...")
        background_img = get_background_image()
        
        print("Creating quote image...")
        quote_image = create_quote_image(english_quote, english_author, japanese_translation, background_img)
        
        print("Posting to Twitter...")
        post_to_twitter(client, api_v1_1, english_quote, english_author, japanese_translation, quote_image)
        
        print("Successfully completed auto tweet!")
        
    except Exception as e:
        print(f"Error in main process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()



