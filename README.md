# AIマルチモデルチャットボット(VOLTMIND-chat)

## 概要
このプロジェクトは、複数のAIモデルを利用できるチャットボットアプリケーションです。Flask製のWebアプリケーションとして実装されており、様々なAIモデルとの対話、画像認識、Web検索などの機能を提供します。
また、このプロジェクトはマルチプラットフォームに対応しており、Windwos,macOS,iOS,iPadOSにて動作確認をしています。 

<img width="1512" alt="スクリーンショット 2024-11-25 17 51 14" src="https://github.com/user-attachments/assets/d93e846b-4b18-4751-beb0-a943ba806773">
<img width="1512" alt="スクリーンショット 2024-11-25 17 51 24" src="https://github.com/user-attachments/assets/e46fc762-1568-48cd-a1f8-47a3d782a0ba">

## 主な機能

- 複数のAIモデルとの対話機能（GPT、Claude、Gemini、Groq等）
- 画像認識機能
- Web検索機能（@webコマンド）
- URL解析機能（@urlコマンド）
- ユーザー認証システム
- チャット履歴の保存機能
- 管理者機能

## インストール方法

### 1. 必要な環境

- Python 3.8以上
- pip（Pythonパッケージマネージャー）
- SQLite3

### 2. プロジェクトのセットアップ

1. リポジトリをクローンまたはダウンロードします

2. 仮想環境を作成し、有効化します
```bash
python -m venv venv
source venv/bin/activate  # Linuxの場合
venv\Scripts\activate     # Windowsの場合
```

3. 必要なパッケージをインストールします
```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`functions/.env`ファイルを作成し、以下の形式でAPIキーを設定します:

```
OPENAI_API_KEY = "your-openai-api-key"
GROQ_API_KEY = "your-groq-api-key"
PPLX_API_KEY = "your-pplx-api-key"
XAI_API_KEY = "your-xai-api-key"
ANTHROPIC_API_KEY = "your-anthropic-api-key"
GEMINI_API_KEY = "your-gemini-api-key"
GOOGLE_API_KEY = "your-google-api-key"
GOOGLE_SERCH_ENGINE_ID = "your-google-search-engine-id"
```

## 使用方法

### アプリケーションの起動

1. プロジェクトディレクトリで以下のコマンドを実行します:
```bash
python app.py
```

2. ブラウザで `http://localhost:5000` にアクセスします

### 初期設定

- 初回起動時に自動的に管理者アカウントが作成されます
  - ユーザー名: ****
  - パスワード: *****_***

### 基本的な使い方

1. アカウントの作成
   - 「新規登録」からアカウントを作成
   - ユーザー名とパスワード（8文字以上）が必要

2. ログイン
   - 作成したアカウントでログイン

3. チャット機能
   - 通常のチャット:テキストを入力して送信
   - 画像認識:画像をアップロードして分析
   - Web検索:`@web [検索キーワード]`の形式で入力
   - URL解析:`@url [URL]`の形式で入力

4. モデルの切り替え
   - インターフェース上のドロップダウンメニューから使用するAIモデルを選択可能

### 管理者機能

(/adminにアクセスしたら使えます。)


<img width="1512" alt="スクリーンショット 2024-11-25 17 51 37" src="https://github.com/user-attachments/assets/fe9e9c9c-e857-49a1-9df0-b35ca4f8f61d">

- ユーザー管理
- チャット履歴の管理
- システム設定の管理

## セキュリティ注意事項
- APIキーは必ず`.env`ファイルで管理し、公開リポジトリにアップロードしないでください
- 初期の管理者パスワードは必ず変更してください
- 本番環境では`debug=True`の設定を無効化してください

## ディレクトリ構造

```
.
├── app.py              # メインアプリケーションファイル
├── functions/          # 機能モジュール
│   ├── agent.py       # エージェント関連の機能
│   ├── funs.py        # 基本機能
│   ├── search_funs.py # 検索関連機能
│   └── web_search_rag.py # Web検索RAG機能
├── static/            # 静的ファイル
│   ├── css/          # スタイルシート
│   └── js/           # JavaScriptファイル
├── templates/         # HTMLテンプレート
├── instance/         # データベース
└── uploads/          # アップロードファイル一時保存
```

## エラー対処

1. データベースエラー
   - `instance/users.db`を削除して再起動することで初期化できます

2. APIキーエラー
   - `.env`ファイルの設定を確認してください
   - 各サービスでAPIキーが有効であることを確認してください

3. 接続エラー
   - ファイアウォールの設定を確認してください
   - ポート5000が使用可能であることを確認してください
