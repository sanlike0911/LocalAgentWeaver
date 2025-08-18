#!/usr/bin/env python3
"""
LocalAgentWeaver - 開発環境セットアップスクリプト
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command: str, description: str = None):
    """コマンドを実行し、結果を表示"""
    if description:
        print(f"\n🔧 {description}")
    
    print(f"実行中: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 成功")
        if result.stdout:
            print(result.stdout)
    else:
        print("❌ エラー")
        if result.stderr:
            print(result.stderr)
        return False
    return True

def setup_development_environment():
    """開発環境をセットアップ"""
    print("🚀 LocalAgentWeaver 開発環境セットアップを開始します...")
    
    # 1. Pythonバージョンチェック
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 10):
        print("❌ Python 3.10以上が必要です")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} が使用されます")
    
    # 2. 仮想環境の作成
    if not os.path.exists("venv"):
        if not run_command("python -m venv venv", "仮想環境を作成中..."):
            return False
    else:
        print("✅ 仮想環境は既に存在します")
    
    # 3. 必要なディレクトリを作成
    directories = ["src", "tests", "modules", "data", "logs", "vector_db"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ 必要なディレクトリを作成しました")
    
    # 4. .gitkeep ファイルを作成（空のディレクトリをGitで追跡するため）
    gitkeep_dirs = ["data", "logs"]
    for directory in gitkeep_dirs:
        gitkeep_path = Path(directory) / ".gitkeep"
        gitkeep_path.touch()
    
    # 5. 依存関係のインストール指示
    print("\n📦 次のステップ:")
    if os.name == 'nt':  # Windows
        print("1. 仮想環境をアクティベート: venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("1. 仮想環境をアクティベート: source venv/bin/activate")
    
    print("2. 依存関係をインストール: pip install -r requirements.txt")
    print("3. Ollamaをインストール: https://ollama.ai/")
    print("4. Ollamaモデルをプル: ollama pull llama3")
    
    print("\n🎉 開発環境の準備が完了しました！")
    return True

if __name__ == "__main__":
    setup_development_environment()