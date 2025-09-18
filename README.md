# 名言・格言画像Bot

AIが生成する心に響く名言を美しい画像と組み合わせ、Xに自動投稿するWebアプリケーション。

## 機能

- **AI名言生成**: Gemini-2.5-flashを使用して心に響く名言・格言を自動生成、Xに自動投稿（毎日一回）
- **美しい画像合成**: 背景画像と名言を組み合わせた画像を生成
- **多様な背景**: 自然、抽象、ミニマル、ヴィンテージ、宇宙、都市など様々な背景タイプ
- **カスタマイズ可能**: 生成された名言や作者名を手動で編集可能
- **画像ダウンロード**: 生成された画像をPNG形式でダウンロード

## セットアップ

### 1. 依存関係のインストール

```bash
cd quote-image-bot
pnpm install
```

### 2. 環境変数の設定

`.env.example`を`.env`にコピーして、必要なAPIキーを設定してください：

```bash
cp .env.example .env
```

`.env`ファイルを編集して以下のAPIキーを設定：

- `VITE_GEMINI_API_KEY`: Google Gemini APIキー
- `VITE_UNSPLASH_ACCESS_KEY`: Unsplash APIキー（オプション）

### 3. 開発サーバーの起動

```bash
pnpm run dev
```

### 4. ビルド

```bash
pnpm run build
```

## 使用方法

1. **APIキーの入力**: Gemini APIキーを入力フィールドに設定
2. **背景タイプの選択**: お好みの背景タイプを選択
3. **名言の生成**: 「名言を生成」ボタンをクリック
4. **画像の生成**: 「画像を生成」ボタンをクリック
5. **ダウンロード**: 生成された画像をダウンロード

## GitHub Actionsでの自動化

このプロジェクトには、定期的に名言画像を生成してX (旧Twitter) に投稿するGitHub Actionsワークフローが含まれています。

### 必要なシークレット

GitHubリポジトリの設定で以下のシークレットを設定してください：

- `GEMINI_API_KEY`: Google Gemini APIキー
- `TWITTER_API_KEY`: X (旧Twitter) APIキー
- `TWITTER_API_SECRET`: X (旧Twitter) APIシークレット
- `TWITTER_ACCESS_TOKEN`: X (旧Twitter) アクセストークン
- `TWITTER_ACCESS_TOKEN_SECRET`: X (旧Twitter) アクセストークンシークレット
- `UNSPLASH_ACCESS_KEY`: Unsplash APIキー（オプション）

**注意**: X (旧Twitter) APIの仕様変更により、メディアのアップロードにはv1.1 APIを、ツイートの投稿にはv2 APIを使用しています。

## 技術スタック

- **Frontend**: React + Vite
- **UI**: Tailwind CSS + shadcn/ui
- **AI**: Google Gemini-2.5-flash
- **画像API**: Unsplash API
- **デプロイ**: GitHub Pages
- **自動化**: GitHub Actions

## ライセンス

MIT License



