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
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Twitter API
    auth = tweepy.OAuthHandler(
        os.environ['TWITTER_API_KEY'],
        os.environ['TWITTER_API_SECRET']
    )
    auth.set_access_token(
        os.environ['TWITTER_ACCESS_TOKEN'],
        os.environ['TWITTER_ACCESS_TOKEN_SECRET']
    )
    twitter_api = tweepy.API(auth)
    
    return model, twitter_api

def generate_quote(model):
    """Gemini APIを使用して名言を生成"""
    prompts = [
        "心に響く名言や格言を1つ生成してください。日本語で、作者名も含めて教えてください。形式は「名言内容」- 作者名 でお願いします。",
        "人生について考えさせられる深い名言を生成してください。日本語で、作者名も含めて教えてください。形式は「名言内容」- 作者名 でお願いします。",
        "成功や努力に関する励ましの名言を生成してください。日本語で、作者名も含めて教えてください。形式は「名言内容」- 作者名 でお願いします。",
        "愛や友情について心温まる名言を生成してください。日本語で、作者名も含めて教えてください。形式は「名言内容」- 作者名 でお願いします。"
    ]
    
    try:
        prompt = random.choice(prompts)
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # 名言と作者を分離
        if '」-' in text:
            parts = text.split('」-')
            quote = parts[0].replace('「', '').strip()
            author = parts[1].strip()
        elif '"' in text and '-' in text:
            parts = text.split('-')
            quote = parts[0].strip().replace('"', '').replace('"', '')
            author = parts[1].strip()
        else:
            # フォーマットが異なる場合の処理
            parts = text.split('-')
            if len(parts) >= 2:
                quote = parts[0].strip().replace('「', '').replace('」', '').replace('"', '')
                author = parts[1].strip()
            else:
                quote = text.strip()
                author = "Unknown"
        
        return quote, author
    except Exception as e:
        print(f"Error generating quote: {e}")
        # フォールバック名言
        fallback_quotes = [
            ("人生は一度きり。後悔のないように生きよう。", "Anonymous"),
            ("小さな一歩が大きな変化を生む。", "Anonymous"),
            ("困難は成長の機会である。", "Anonymous")
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
        if 'UNSPLASH_ACCESS_KEY' in os.environ:
            # Unsplash APIを使用
            query = random.choice(background_types)
            url = f"https://api.unsplash.com/photos/random"
            params = {
                'query': query,
                'orientation': 'landscape',
                'w': 800,
                'h': 600
            }
            headers = {
                'Authorization': f"Client-ID {os.environ['UNSPLASH_ACCESS_KEY']}"
            }
            
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                image_url = data['urls']['regular']
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    return Image.open(BytesIO(image_response.content))
    except Exception as e:
        print(f"Error fetching background image: {e}")
    
    # フォールバック: グラデーション背景を生成
    img = Image.new('RGB', (800, 600), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # 簡単なグラデーション効果
    for y in range(600):
        r = int(102 + (118 - 102) * y / 600)
        g = int(126 + (75 - 126) * y / 600)
        b = int(234 + (162 - 234) * y / 600)
        draw.line([(0, y), (800, y)], fill=(r, g, b))
    
    return img

def create_quote_image(quote, author, background_img):
    """名言画像を生成"""
    # 背景画像をリサイズ
    background_img = background_img.resize((800, 600), Image.Resampling.LANCZOS)
    
    # オーバーレイを追加
    overlay = Image.new('RGBA', (800, 600), (0, 0, 0, 100))
    background_img = Image.alpha_composite(background_img.convert('RGBA'), overlay)
    
    draw = ImageDraw.Draw(background_img)
    
    try:
        # フォントを設定（システムフォントを使用）
        quote_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        author_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        # フォントが見つからない場合はデフォルトフォント
        quote_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
    
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
    
    return background_img.convert('RGB')

def post_to_twitter(twitter_api, quote, author, image):
    """Twitterに投稿"""
    try:
        # 画像を一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            image.save(tmp_file.name, 'PNG')
            
            # ツイート文を作成
            tweet_text = f'"{quote}" - {author}\n\n#名言 #格言 #inspiration #quote'
            
            # 文字数制限をチェック
            if len(tweet_text) > 280:
                # 長すぎる場合は短縮
                max_quote_length = 200 - len(f' - {author}\n\n#名言 #格言 #inspiration #quote')
                if len(quote) > max_quote_length:
                    quote = quote[:max_quote_length-3] + '...'
                tweet_text = f'"{quote}" - {author}\n\n#名言 #格言 #inspiration #quote'
            
            # 画像をアップロード
            media = twitter_api.media_upload(tmp_file.name)
            
            # ツイートを投稿
            twitter_api.update_status(status=tweet_text, media_ids=[media.media_id])
            
            print(f"Successfully tweeted: {tweet_text}")
            
            # 一時ファイルを削除
            os.unlink(tmp_file.name)
            
    except Exception as e:
        print(f"Error posting to Twitter: {e}")
        raise

def main():
    """メイン処理"""
    try:
        print("Setting up APIs...")
        model, twitter_api = setup_apis()
        
        print("Generating quote...")
        quote, author = generate_quote(model)
        print(f"Generated quote: '{quote}' - {author}")
        
        print("Getting background image...")
        background_img = get_background_image()
        
        print("Creating quote image...")
        quote_image = create_quote_image(quote, author, background_img)
        
        print("Posting to Twitter...")
        post_to_twitter(twitter_api, quote, author, quote_image)
        
        print("Successfully completed auto tweet!")
        
    except Exception as e:
        print(f"Error in main process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

