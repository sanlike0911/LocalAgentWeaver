# 🐧 WSL環境でのVS Codeデバッグガイド

## 🚀 前提条件

### 必要な拡張機能（Windows VS Code）
1. **Remote - WSL** (`ms-vscode-remote.remote-wsl`)
2. **JavaScript Debugger** (標準搭載)
3. **Python** (`ms-python.python`) - バックエンド用

### WSL環境の確認
```bash
# WSLのバージョン確認
wsl --version

# Node.jsのバージョン確認
node --version  # v18以上推奨

# Python環境確認
python3 --version  # 3.11以上推奨
```

## 🛠️ セットアップ手順

### Step 1: Windows VS CodeでWSLに接続
```bash
# WSL内でプロジェクトディレクトリに移動
cd "/mnt/c/Users/ID5665/project/Generation AI/LocalAgentWeaver"

# VS CodeをWSLモードで起動
code .
```

### Step 2: 環境の確認
VS Code内でタスクを実行：
1. `Ctrl+Shift+P` → `Tasks: Run Task`
2. `WSL: Check Environment` を選択

### Step 3: 依存関係のインストール
```bash
# フロントエンド依存関係
cd frontend
npm install

# バックエンド依存関係（必要に応じて）
cd ../backend
pip install -r requirements.txt
```

## 🎯 デバッグ方法

### 方法1: フロントエンド専用デバッグ（推奨）

#### 1. サーバーを手動起動
```bash
# ターミナル1: バックエンド
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# ターミナル2: フロントエンド（デバッグモード）
cd frontend  
npm run dev:debug
```

#### 2. VS Codeでデバッグ開始
1. `F5` または デバッグパネル（`Ctrl+Shift+D`）
2. **`WSL: Debug Auth API (Frontend Only)`** を選択
3. 実行開始

### 方法2: VS Code統合デバッグ

#### Node.jsデバッガ使用
1. デバッグ設定: **`WSL: Next.js Debug Frontend`**
2. 自動でNext.jsサーバーが起動
3. Node.jsプロセスに直接アタッチ

#### Chromeデバッガ使用  
1. デバッグ設定: **`WSL: Chrome Debug Client`**
2. Chromeが自動起動してソースにアタッチ

### 方法3: フルスタックデバッグ
1. デバッグ設定: **`WSL: Full Stack Debug`**
2. フロントエンド＋バックエンド同時デバッグ

## 🔍 404エラーの具体的なデバッグ手順

### Step 1: ブレークポイントの設定
VS Codeで以下にブレークポイントを設定：
- `frontend/src/features/auth/api.ts:42` (URL生成部分)
- `frontend/src/features/auth/components/AuthForm.tsx:65` (送信処理)

### Step 2: 環境変数の確認
デバッガ起動後、VS Codeの**デバッグコンソール**で：
```javascript
process.env.NEXT_PUBLIC_API_BASE_URL
```

### Step 3: リクエストURLの確認  
`api.ts`のブレークポイントで停止時、**変数**パネルで確認：
- `API_BASE_URL`の値
- `url`変数の値
- `data`パラメータの内容

### Step 4: ネットワーク通信の確認
Chromeデベロッパーツール：
1. `F12` → `Network`タブ
2. `Fetch/XHR`フィルター有効化  
3. フォーム送信時のリクエストを監視

## 🛠️ WSL特有のトラブルシューティング

### ファイル監視が効かない場合
```bash
# .env.localまたはnext.config.jsに追加
CHOKIDAR_USEPOLLING=true
WATCHPACK_POLLING=true
```

### ポートアクセスの問題
```bash  
# WSL2でのポート転送確認
netstat -an | grep :3000
netstat -an | grep :8000

# Windows側からWSLのポートにアクセス可能か確認
curl http://localhost:3000
curl http://localhost:8000
```

### パフォーマンスの問題
```bash
# WSL1の場合はWSL2にアップグレード推奨
wsl --set-version Ubuntu 2

# または、Windowsファイルシステム側に移動
cp -r "/mnt/c/Users/ID5665/project" ~/project
cd ~/project/LocalAgentWeaver
```

### VS Codeの接続問題
1. **Remote - WSL**拡張機能を再インストール
2. WSLを再起動: `wsl --shutdown`
3. VS Codeを管理者権限で実行

## 🔧 デバッグ設定のカスタマイズ

### Chrome起動オプション
```json
{
  "type": "chrome",
  "userDataDir": "${workspaceFolder}/.chrome-debug-wsl",
  "runtimeArgs": [
    "--remote-debugging-port=9222",
    "--disable-web-security",
    "--disable-features=VizDisplayCompositor"
  ]
}
```

### Node.js検査ポート変更
```json
{
  "env": {
    "NODE_OPTIONS": "--inspect=0.0.0.0:9229"
  }
}
```

## 🚨 緊急デバッグコマンド

### プロセス確認
```bash
# 動作中のプロセス確認
ps aux | grep node
ps aux | grep python

# ポート使用状況
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :8000
```

### ログ確認
```bash
# Next.jsのログ
cd frontend && npm run dev 2>&1 | tee frontend.log

# FastAPIのログ  
cd backend && uvicorn app.main:app --log-level debug 2>&1 | tee backend.log
```

### 環境変数確認
```bash
# 現在の環境変数を全て表示
env | grep -E "(NODE|NEXT|API)"

# .env.localの内容確認
cat frontend/.env.local
```

## 📊 成功時の確認事項

### 正常動作の確認方法
1. **ブラウザコンソール**で環境変数が正しく表示される
2. **Network**タブで正しいURLにリクエストが送信される
3. **VS Codeデバッガ**でソースマップが正しく読み込まれる
4. **ブレークポイント**で変数の値が期待通り

### 期待される出力
```
// ブラウザコンソール
API_BASE_URL: http://localhost:8000
Registration URL: http://localhost:8000/api/auth/register

// Networkタブ  
POST http://localhost:8000/api/auth/register 201 Created
```