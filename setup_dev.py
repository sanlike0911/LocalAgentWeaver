#!/usr/bin/env python3
"""
LocalAgentWeaver - 開発環境セットアップスクリプト
"""

import subprocess
import sys
import os
import threading
import time
from pathlib import Path

def run_command(command: str, description: str = None, show_progress: bool = False):
    """コマンドを実行し、結果を表示"""
    if description:
        print(f"\n🔧 {description}")
    
    print(f"実行中: {command}")
    
    if show_progress:
        # プログレス表示用のスレッド
        progress_running = threading.Event()
        progress_running.set()
        
        def show_progress_animation():
            animation = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            i = 0
            while progress_running.is_set():
                print(f"\r{animation[i % len(animation)]} 処理中...", end="", flush=True)
                time.sleep(0.1)
                i += 1
            print("\r", end="", flush=True)  # カーソルをクリア
        
        progress_thread = threading.Thread(target=show_progress_animation)
        progress_thread.daemon = True
        progress_thread.start()
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
        finally:
            progress_running.clear()
            progress_thread.join(timeout=1)
            print()  # 改行
    else:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 成功")
        if result.stdout and not show_progress:
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
    if not os.path.exists(".venv"):
        if not run_command("python -m venv .venv", "仮想環境を作成中...", show_progress=True):
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
    
    # 5. 依存関係をインストール
    print("\n📦 依存関係をインストール中...")
    
    # 仮想環境のpipパスを取得
    if os.name == 'nt':  # Windows
        pip_path = ".venv\\Scripts\\pip"
        python_path = ".venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        pip_path = ".venv/bin/pip"
        python_path = ".venv/bin/python"
    
    # pipをアップグレード
    if not run_command(f"{python_path} -m pip install --upgrade pip", "pipをアップグレード中...", show_progress=True):
        print("⚠️  pipのアップグレードに失敗しましたが、続行します")
    
    # requirements.txtから依存関係をインストール
    if os.path.exists("requirements.txt"):
        # requirements.txtの内容を確認してパッケージ数を表示
        with open("requirements.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]
            package_lines = [line for line in lines if line and not line.startswith("#")]
            package_count = len(package_lines)
        
        print(f"📦 {package_count}個のパッケージをインストールします...")
        
        if run_command(f"{pip_path} install -r requirements.txt", f"依存関係をインストール中... ({package_count}個のパッケージ)", show_progress=True):
            print("✅ 依存関係のインストールが完了しました")
        else:
            print("❌ 依存関係のインストールに失敗しました")
            return False
    else:
        print("⚠️  requirements.txtが見つかりません")
    
    # 6. 次のステップの案内
    print("\n📦 次のステップ:")
    print("1. Ollamaをインストール: https://ollama.ai/")
    print("2. Ollamaモデルをプル: ollama pull llama3")
    if os.name == 'nt':  # Windows
        print("3. 仮想環境をアクティベート: .venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("3. 仮想環境をアクティベート: source .venv/bin/activate")
    
    print("4. アプリを起動: python run.py または chainlit run app.py")
    
    print("\n🎉 開発環境の準備が完了しました！")
    return True

if __name__ == "__main__":
    setup_development_environment()