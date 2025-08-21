# 🛠️ LocalAgentWeaver デバッグガイド

## 🚀 クイックスタート

### VS Codeでプロジェクトを開く
```bash
# ワークスペースファイルで開く（推奨）
code LocalAgentWeaver.code-workspace

# または通常のフォルダとして開く
code .
```

## 🎯 404 Not Found エラーのデバッグ

### 1. フロントエンドのデバッグ
```bash
# 1. フロントエンドディレクトリに移動
cd frontend

# 2. デバッグモードで起動
npm run dev:debug
```

### 2. VS Codeでのデバッグ手順
1. `F5` を押すか、デバッグパネルを開く（`Ctrl+Shift+D`）
2. `🐛 Debug Frontend (Auth API)` を選択
3. デバッグ実行開始

### 3. ブレークポイントの設定場所
- **`frontend/src/features/auth/api.ts:42`** - API URL生成部分
- **`frontend/src/features/auth/components/AuthForm.tsx:65`** - フォーム送信処理

## 🔍 現在の問題の調査手順

### Step 1: 環境変数の確認
1. ブラウザで `F12` → `Console`
2. 以下をコンソールに入力して確認:
```javascript
console.log({
  'NEXT_PUBLIC_API_BASE_URL': process.env.NEXT_PUBLIC_API_BASE_URL,
  'NODE_ENV': process.env.NODE_ENV
});
```

### Step 2: API URL の確認
`frontend/src/features/auth/api.ts` の42行目にブレークポイントを設定し、以下を確認:
- `API_BASE_URL` の値
- 実際のfetch URL
- リクエストボディの内容

### Step 3: ネットワークタブでの確認
1. `F12` → `Network` タブ
2. `Fetch/XHR` フィルターを有効化
3. 新規登録フォームを送信
4. 失敗したリクエストの詳細を確認

## 🛠️ 利用可能なデバッグ設定

### フロントエンド専用
- **Next.js: debug client-side** - ブラウザ側のコードをデバッグ
- **Next.js: debug server-side** - Next.jsサーバー側をデバッグ
- **Next.js: debug full stack** - フルスタックデバッグ

### バックエンド専用  
- **FastAPI: debug backend** - FastAPIサーバーをデバッグ

### フルスタック
- **Full Stack: Frontend + Backend** - 両方同時にデバッグ

## 🔧 トラブルシューティング

### ソースマップが見つからない場合
```bash
cd frontend
rm -rf .next
npm run dev:debug
```

### 環境変数が読み込まれない場合
```bash
# フロントエンドサーバーを完全停止
# Ctrl+C で停止後、再起動
npm run dev
```

### Chrome起動エラーの場合
1. `.vscode/launch.json` の Chrome設定を確認
2. 必要に応じて `runtimeExecutable` パスを手動設定

## 📊 現在の環境設定

### 環境変数ファイル
- `frontend/.env.local` - フロントエンド環境変数
- `.env` - 全体設定（存在する場合）

### 設定ファイル
- `frontend/next.config.js` - Next.js設定（APIプロキシ含む）
- `.vscode/launch.json` - VS Codeデバッグ設定
- `LocalAgentWeaver.code-workspace` - ワークスペース設定

## 🚨 緊急時のデバッグコマンド

### 現在の状況を素早く確認
```bash
# サーバー起動確認
curl http://localhost:3000
curl http://localhost:8000/health

# 環境変数確認
cat frontend/.env.local

# Next.js設定確認
cat frontend/next.config.js
```

### ログを詳細に確認
```bash
# フロントエンド（デバッグモード）
cd frontend && npm run dev:debug

# バックエンド（詳細ログ）
cd backend && uvicorn app.main:app --log-level debug --reload
```

---

## 🎉 成功パターン

正常に動作している場合、以下のような出力が確認できます：

### ブラウザコンソール
```
API_BASE_URL: http://localhost:8000
Registration URL: http://localhost:8000/api/auth/register
```

### ネットワークタブ
```
POST http://localhost:8000/api/auth/register
Status: 201 Created
Response: {"id": 1, "email": "...", ...}
```