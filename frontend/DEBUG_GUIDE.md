# フロントエンドデバッグガイド

## 🚀 セットアップ

### 1. VS Code拡張機能のインストール
以下の拡張機能をインストールしてください：
- **JavaScript Debugger (Nightly)** - Microsoft公式
- **ES6 Code Snippets**
- **Auto Rename Tag**

## 🛠️ デバッグ方法

### A. VS Codeを使ったデバッグ（推奨）

#### 方法1: ワンクリックデバッグ
1. VS Codeでプロジェクトを開く
2. `F5` を押すか、デバッグパネル（Ctrl+Shift+D）を開く
3. `Next.js: debug full stack` を選択して実行
4. 自動的にChromeが起動し、デバッガがアタッチされます

#### 方法2: 段階的デバッグ
1. **サーバー側デバッグ**
   - デバッグパネルで `Next.js: debug server-side` を選択
   - サーバー側のコードにブレークポイントを設定可能

2. **クライアント側デバッグ**
   - 別途 `npm run dev` でサーバーを起動
   - デバッグパネルで `Next.js: debug client-side` を選択
   - ブラウザ側のコードをデバッグ

### B. コマンドラインを使ったデバッグ

#### 基本デバッグモード
```bash
npm run dev:debug
```
- デバッガポート: 9229
- ブラウザで `chrome://inspect` を開いてアタッチ

#### ブレークポイントで停止
```bash
npm run dev:debug-brk
```
- 起動時に即座にデバッガで停止

### C. ブラウザデベロッパーツール

#### 基本的な使い方
1. ブラウザで `F12` を押す
2. **Sources** タブを開く
3. `webpack://` → `.` → `src` からファイルを探す
4. 行番号をクリックしてブレークポイント設定

#### ネットワーク通信のデバッグ
1. **Network** タブを開く
2. `Fetch/XHR` フィルターを有効化
3. APIリクエストを監視

## 🎯 ブレークポイントの設定方法

### VS Code
```javascript
// 1. 行番号の左をクリック
// 2. または以下のコードを追加
debugger; // この行で必ず停止

// 3. 条件付きブレークポイント
// 右クリック → "Add Conditional Breakpoint"
// 例: user.email === 'test@example.com'
```

### 認証API関連のデバッグポイント例
```javascript
// src/features/auth/api.ts
export class AuthAPI {
  static async register(data: RegisterData): Promise<User> {
    debugger; // ここで停止
    const url = `${API_BASE_URL}/api/auth/register`
    console.log('Registration URL:', url)
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    
    debugger; // レスポンス受信後に停止
    if (!response.ok) {
      debugger; // エラー時に停止
      const error = await response.json().catch(() => ({ detail: 'Registration failed' }))
      throw new Error(error.detail || 'Registration failed')
    }

    return response.json()
  }
}
```

### フォーム送信時のデバッグ
```javascript
// src/features/auth/components/AuthForm.tsx
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault()
  debugger; // フォーム送信開始時
  
  if (!validateForm()) {
    debugger; // バリデーションエラー時
    return
  }

  setLoading(true)

  try {
    if (mode === 'register') {
      debugger; // 登録処理開始時
      const user = await AuthAPI.register(formData as RegisterData)
      debugger; // 登録成功時
    }
  } catch (err) {
    debugger; // エラー発生時
    setError(err instanceof Error ? err.message : '予期しないエラーが発生しました')
  }
}
```

## 🔧 トラブルシューティング

### ソースマップが見つからない場合
```bash
# .next フォルダを削除して再ビルド
rm -rf .next
npm run dev:debug
```

### ブレークポイントが効かない場合
1. `next.config.js` でソースマップを有効化:
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    forceSwcTransforms: true,
  },
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      config.devtool = 'eval-source-map'
    }
    return config
  }
}

module.exports = nextConfig
```

### VS CodeでChromeが起動しない場合
1. Chromeのパスを確認:
```json
// .vscode/launch.json
{
  "type": "chrome",
  "runtimeExecutable": "/path/to/chrome", // 手動でパスを指定
  "userDataDir": "${workspaceFolder}/.chrome-debug"
}
```

## 📊 デバッグのベストプラクティス

### 1. 段階的デバッグ
```javascript
console.log('🔍 Debug Point 1: Function called')
console.log('📝 Data:', data)
debugger;

// 処理...

console.log('✅ Debug Point 2: Process completed')
console.log('📋 Result:', result)
```

### 2. 条件付きログ
```javascript
const DEBUG = process.env.NODE_ENV === 'development'

if (DEBUG) {
  console.log('🐛 Debug Info:', { user, token, url })
}
```

### 3. エラーハンドリング
```javascript
try {
  // API call
} catch (error) {
  console.error('❌ API Error:', {
    message: error.message,
    stack: error.stack,
    url: window.location.href,
    timestamp: new Date().toISOString()
  })
  debugger; // エラー時に必ず停止
}
```

## 🚨 現在の問題のデバッグ

### 404 Not Foundエラーの調査
1. `src/features/auth/api.ts` の37-38行目にブレークポイントを設定
2. 新規登録フォームを送信
3. 以下の値を確認:
   - `API_BASE_URL` の値
   - `process.env.NEXT_PUBLIC_API_BASE_URL` の値
   - 実際のfetch URL

### 環境変数の確認
1. ブラウザのコンソールで確認:
```javascript
console.log('Environment:', {
  NODE_ENV: process.env.NODE_ENV,
  API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL
})
```

## 🎉 デバッグが完了したら

デバッグ用のコードを削除:
```bash
# debugger文を検索
grep -r "debugger" src/

# console.logを検索
grep -r "console.log" src/
```