# Playlist Downloader

YouTube Music と SoundCloud のプレイリストを監視し、新しい曲を自動でMP3ダウンロードするWebアプリケーション。

## 機能

- **プレイリスト管理**: YouTube Music / SoundCloud のプレイリストURLを登録
- **自動監視**: 設定した間隔（1時間〜1週間）でプレイリストの更新をチェック
- **自動ダウンロード**: 新しく追加された曲を自動でMP3形式でダウンロード
- **ダウンロード履歴**: ダウンロードした曲の履歴を日時・ステータス付きで確認
- **手動チェック**: 任意のタイミングで更新チェックを実行可能

## 技術スタック

### バックエンド
- **FastAPI** - Python Web フレームワーク
- **SQLAlchemy** - ORM
- **SQLite** - データベース
- **APScheduler** - スケジューラー
- **yt-dlp** - ダウンロードエンジン

### フロントエンド
- **React** - UIライブラリ
- **Vite** - ビルドツール
- **TailwindCSS** - スタイリング
- **React Router** - ルーティング

## セットアップ

### Docker を使う場合（推奨）

```bash
# リポジトリをクローン
git clone <repository-url>
cd playlist-downloader

# 環境変数ファイルを作成
cp .env.example .env

# Docker Compose で起動
docker-compose up --build
```

起動後:
- フロントエンド: http://localhost:5173
- バックエンドAPI: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs

### ローカル開発環境

#### バックエンド

```bash
cd backend

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# サーバーを起動
uvicorn main:app --reload
```

#### フロントエンド

```bash
cd frontend

# 依存関係をインストール
npm install

# 開発サーバーを起動
npm run dev
```

## 使い方

### 1. プレイリストを追加

1. サイドバーから「Playlists」を選択
2. 「Add Playlist」をクリック
3. プレイリストURLを入力（YouTube Music または SoundCloud）
4. 監視間隔を設定
5. 「Add Playlist」で保存

### 2. 監視と自動ダウンロード

- 登録されたプレイリストは設定した間隔で自動チェック
- 新しい曲が見つかると自動でMP3をダウンロード
- 手動チェックも可能（更新アイコンをクリック）

### 3. ダウンロード履歴を確認

- サイドバーから「History」を選択
- ステータス・プレイリストでフィルタリング可能
- 完了した曲はダウンロードアイコンからMP3を取得
- 失敗した曲は再試行ボタンで再ダウンロード

## API エンドポイント

### プレイリスト管理
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/playlists` | プレイリスト一覧取得 |
| POST | `/api/playlists` | プレイリスト追加 |
| GET | `/api/playlists/{id}` | プレイリスト詳細取得 |
| PUT | `/api/playlists/{id}` | プレイリスト更新 |
| DELETE | `/api/playlists/{id}` | プレイリスト削除 |
| POST | `/api/playlists/{id}/check` | 手動更新チェック |

### ダウンロード・履歴
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/downloads` | ダウンロード履歴一覧 |
| GET | `/api/downloads/stats` | ダウンロード統計 |
| POST | `/api/downloads/track/{track_id}` | 手動ダウンロード |
| POST | `/api/downloads/{id}/retry` | 失敗したダウンロードを再試行 |
| GET | `/api/downloads/files/{filename}` | ファイルダウンロード |

### スケジューラー
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scheduler/status` | スケジューラー状態取得 |
| POST | `/api/scheduler/pause` | 一時停止 |
| POST | `/api/scheduler/resume` | 再開 |

## ディレクトリ構成

```
playlist-downloader/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── backend/
│   ├── main.py              # FastAPIエントリポイント
│   ├── config.py            # 設定管理
│   ├── api/
│   │   ├── routes/          # APIルート
│   │   └── schemas/         # Pydanticスキーマ
│   ├── services/            # ビジネスロジック
│   ├── scheduler/           # 定期実行ジョブ
│   └── db/                  # データベースモデル
└── frontend/
    ├── src/
    │   ├── api/             # APIクライアント
    │   ├── pages/           # ページコンポーネント
    │   └── App.tsx          # メインアプリ
    └── package.json
```

## 注意事項

- **ffmpeg** が必要（Docker イメージには含まれています）
- YouTube Music の一部コンテンツはログインが必要な場合があります（cookies.txt を設定）
- ダウンロードした音楽は個人利用の範囲でお使いください

## ライセンス

MIT License
