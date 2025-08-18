#!/usr/bin/env python3
"""
LocalAgentWeaver 起動スクリプト
"""

import subprocess
import sys
import os
from pathlib import Path

def check_ollama():
    """Ollamaの起動状態をチェック"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """メイン関数"""
    print("🚀 LocalAgentWeaver を起動しています...")
    
    # Ollamaの起動確認
    if not check_ollama():
        print("⚠️  Ollama が起動していません。")
        print("以下のコマンドでOllamaを起動してください:")
        print("  ollama serve")
        print("\nまたは、以下でモデルをダウンロードしてください:")
        print("  ollama pull llama3")
        
        response = input("\n続行しますか？ (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        print("✅ Ollama接続確認")
    
    # Chainlitアプリを起動
    try:
        print("🌐 Webアプリを起動中...")
        print("ブラウザで http://localhost:8000 にアクセスしてください")
        print("終了するには Ctrl+C を押してください")
        
        subprocess.run([
            "chainlit", "run", "src/main.py",
            "--host", "localhost",
            "--port", "8000"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 LocalAgentWeaver を終了しました")
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()