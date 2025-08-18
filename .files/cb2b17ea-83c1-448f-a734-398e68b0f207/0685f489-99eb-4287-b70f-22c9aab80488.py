#!/usr/bin/env python3
"""
LocalAgentWeaver - メインアプリケーション
ローカル環境で動作するナレッジベース拡張型AIチャットアプリ
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Optional, List

# パスの設定を追加
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir))

import chainlit as cl
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import HumanMessage, AIMessage

# 絶対インポートに変更
try:
    from src.localagentweaver.core.project_manager import ProjectManager, Project
    from src.localagentweaver.core.rag_engine import RAGEngine
    from src.localagentweaver.config.settings import (
        PROJECT_ROOT, DATA_DIR, LOGS_DIR, VECTOR_DB_DIR,
        OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TEMPERATURE,
        DATABASE_PATH, SUPPORTED_FILE_EXTENSIONS,
        LOG_LEVEL, LOG_FORMAT
    )
except ImportError:
    # フォールバック: 相対インポート
    from .core.project_manager import ProjectManager, Project
    from .core.rag_engine import RAGEngine
    from .config.settings import (
        PROJECT_ROOT, DATA_DIR, LOGS_DIR, VECTOR_DB_DIR,
        OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TEMPERATURE,
        DATABASE_PATH, SUPPORTED_FILE_EXTENSIONS,
        LOG_LEVEL, LOG_FORMAT
    )


class LocalAgentWeaver:
    """LocalAgentWeaverのメインクラス"""
    
    def __init__(self):
        """初期化"""
        self.llm = None
        self.embeddings = None
        self.rag_engine = None
        self.project_manager = ProjectManager(DATABASE_PATH)
        self.setup_logging()
        self.setup_llm()
    
    def setup_logging(self):
        """ロギング設定"""
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
            format=LOG_FORMAT,
            handlers=[
                logging.FileHandler(LOGS_DIR / 'localagentweaver.log'),
                logging.StreamHandler()
            ]
        )
    
    def setup_llm(self):
        """Ollama LLMのセットアップ"""
        try:
            # Ollamaの接続テスト
            self.llm = Ollama(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=OLLAMA_TEMPERATURE
            )
            
            self.embeddings = OllamaEmbeddings(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_BASE_URL
            )
            
            # RAGエンジンの初期化
            self.rag_engine = RAGEngine(
                vector_db_path=VECTOR_DB_DIR,
                projects_db_path=DATABASE_PATH,
                llm=self.llm,
                embeddings=self.embeddings
            )
            
            print("✅ Ollama接続成功")
        except Exception as e:
            print(f"❌ Ollama接続エラー: {e}")
            self.llm = None
            self.embeddings = None
            self.rag_engine = None
    
    async def generate_response(self, message: str, project_id: int = None, conversation_history: list = None) -> str:
        """AIからのレスポンスを生成"""
        if not self.llm:
            return "申し訳ありません。現在AIが利用できません。Ollamaが起動しているか確認してください。"
        
        try:
            # RAGエンジンが利用可能でプロジェクトIDがある場合はRAG検索を使用
            if self.rag_engine and project_id:
                rag_result = await self.rag_engine.search_and_generate(message, project_id)
                
                if rag_result["context_used"]:
                    # ソース情報を含めた回答を作成
                    answer = rag_result["answer"]
                    sources = rag_result["sources"]
                    
                    if sources:
                        source_info = "\n\n**📚 参考文書:**\n"
                        for source in sources:
                            source_info += f"- {source['filename']} (関連度: {source['score']:.2f})\n"
                        answer += source_info
                    
                    return answer
            
            # 会話履歴を含むプロンプト作成
            context_text = ""
            if conversation_history:
                context_text = "\n\nConversation history:\n"
                for entry in conversation_history[-5:]:  # 最新5件の履歴を使用
                    context_text += f"User: {entry['user']}\nAssistant: {entry['assistant']}\n\n"
            
            enhanced_prompt = f"""Please respond in the same language as the user's question. If the user asks in Japanese, respond in Japanese. If the user asks in English, respond in English.
{context_text}
Current user question: {message}

Response:"""
            
            # 通常のLLM応答
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.llm.invoke, enhanced_prompt
            )
            return response
        except Exception as e:
            return f"エラーが発生しました: {str(e)}"
    
    async def process_uploaded_file(self, file_path: Path, filename: str, project_id: int) -> bool:
        """アップロードされたファイルを処理"""
        if not self.rag_engine:
            return False
        
        return await self.rag_engine.process_document(file_path, project_id, filename)


# グローバルインスタンス
weaver = LocalAgentWeaver()


@cl.on_chat_start
async def on_chat_start():
    """チャット開始時の処理"""
    
    # ウェルカムメッセージ
    welcome_message = """
🎉 **LocalAgentWeaverへようこそ！**

ローカル環境で動作するAIチャットアプリです。

何でもお気軽に質問してください！
"""
    
    await cl.Message(content=welcome_message).send()
    
    # Ollama接続状態をチェック
    if not weaver.llm:
        error_message = """
⚠️ **Ollama接続エラー**

Ollamaが起動していない可能性があります。以下をご確認ください：

1. Ollamaがインストールされているか
2. `ollama serve` でOllamaが起動しているか
3. `ollama pull llama3` でモデルがダウンロード済みか

詳細: https://ollama.ai/
"""
        await cl.Message(content=error_message).send()


async def show_project_selection():
    """プロジェクト選択UIを表示"""
    try:
        # 既存のプロジェクトを取得
        projects = weaver.project_manager.get_all_projects()
        
        actions = []
        
        # 既存プロジェクトのボタンを作成
        for project in projects:
            actions.append(cl.Action(
                name=f"select_project_{project.id}",
                value=str(project.id),
                payload={"project_id": project.id},
                label=f"📁 {project.name}",
                description=f"作成日: {project.created_at.strftime('%Y-%m-%d')}"
            ))
        
        # 新規プロジェクト作成ボタン
        actions.append(cl.Action(
            name="create_new_project",
            value="new",
            payload={"action": "create"},
            label="➕ 新規プロジェクトを作成",
            description="新しいプロジェクトを作成します"
        ))
        
        if projects:
            message_content = f"**既存のプロジェクト ({len(projects)}個):**\n\nプロジェクトを選択するか、新規作成してください。"
        else:
            message_content = "**プロジェクトがありません**\n\n最初のプロジェクトを作成しましょう！"
        
        await cl.Message(
            content=message_content,
            actions=actions
        ).send()
        
        # Ollama接続状態をチェック
        if not weaver.llm:
            error_message = """
⚠️ **Ollama接続エラー**

Ollamaが起動していない可能性があります。以下をご確認ください：

1. Ollamaがインストールされているか
2. `ollama serve` でOllamaが起動しているか
3. `ollama pull llama3` でモデルがダウンロード済みか

詳細: https://ollama.ai/
"""
            await cl.Message(content=error_message).send()
            
    except Exception as e:
        await cl.Message(content=f"エラー: プロジェクト情報の取得に失敗しました: {str(e)}").send()


@cl.action_callback("create_new_project")
async def create_new_project(action):
    """新規プロジェクト作成のハンドラ"""
    
    try:
        # プロジェクト名を入力してもらう
        project_name = await cl.AskUserMessage(
            content="新規プロジェクトの名前を入力してください:",
            timeout=30
        ).send()
        
        if project_name and project_name.get("output"):
            name = project_name["output"].strip()
            
            if name:
                try:
                    # プロジェクトを作成
                    project_id = weaver.project_manager.create_project(name)
                    
                    # セッションにプロジェクトIDを保存
                    cl.user_session.set("current_project_id", project_id)
                    cl.user_session.set("current_project_name", name)
                    
                    success_message = f"""
✅ **プロジェクト『{name}』を作成しました！**

これで次の機能が利用可能です：
- 📚 ドキュメントファイルのアップロード
- 🤖 ナレッジベースを活用したAIチャット
- 💾 会話履歴の保存

ファイルをアップロードするか、質問を入力してください！
"""
                    
                    await cl.Message(content=success_message).send()
                    
                    # アクションボタンを表示
                    await add_action_buttons()
                    
                except ValueError as e:
                    await cl.Message(content=f"❌ エラー: {str(e)}").send()
                    await show_project_selection()
                except Exception as e:
                    await cl.Message(content=f"❌ プロジェクト作成に失敗しました: {str(e)}").send()
                    await show_project_selection()
            else:
                await cl.Message(content="❌ プロジェクト名を入力してください").send()
                await show_project_selection()
        else:
            await cl.Message(content="❌ プロジェクト名の入力がキャンセルされました").send()
            await show_project_selection()
            
    except Exception as e:
        await cl.Message(content=f"❌ プロジェクト作成処理でエラーが発生しました: {str(e)}").send()
        await show_project_selection()


@cl.action_callback
async def select_existing_project(action):
    """既存プロジェクト選択のハンドラ"""
    
    # プロジェクト選択アクションかチェック
    if not action.name.startswith("select_project_"):
        return
    
    project_id = int(action.value)
    
    try:
        project = weaver.project_manager.get_project_by_id(project_id)
        
        if project:
            # セッションにプロジェクト情報を保存
            cl.user_session.set("current_project_id", project.id)
            cl.user_session.set("current_project_name", project.name)
            
            # プロジェクトの統計情報を取得
            stats = weaver.project_manager.get_project_stats(project_id)
            
            success_message = f"""
✅ **プロジェクト『{project.name}』を開始します**

📊 **プロジェクト情報:**
- 作成日: {project.created_at.strftime('%Y年%m月%d日')}
- ドキュメント数: {stats['document_count']}個

何かご質問がありましたら、お気軽にお尋ねください！
"""
            
            await cl.Message(content=success_message).send()
            
            # アクションボタンを表示
            await add_action_buttons()
            
        else:
            await cl.Message(content="❌ プロジェクトが見つかりません").send()
            await show_project_selection()
            
    except Exception as e:
        await cl.Message(content=f"❌ プロジェクトの読み込みに失敗しました: {str(e)}").send()
        await show_project_selection()


@cl.on_message
async def on_message(message: cl.Message):
    """メッセージ受信時の処理"""
    
    user_message = message.content
    
    # 空メッセージの場合は処理しない
    if not user_message or not user_message.strip():
        await cl.Message(content="💭 メッセージを入力してください。").send()
        return
    
    # 会話履歴を取得
    conversation_history = cl.user_session.get("conversation_history", [])
    
    # 処理中メッセージを表示
    processing_msg = cl.Message(content="🤖 回答を生成しています...")
    await processing_msg.send()
    
    try:
        # AIからの回答を生成（会話履歴付き）
        response = await weaver.generate_response(user_message, conversation_history=conversation_history)
        
        # 会話履歴に追加
        conversation_history.append({
            "user": user_message,
            "assistant": response
        })
        
        # 履歴が長すぎる場合は古いものを削除（最新10件を保持）
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
        
        # セッションに保存
        cl.user_session.set("conversation_history", conversation_history)
        
        # 処理中メッセージを更新
        processing_msg.content = response
        await processing_msg.update()
        
    except Exception as e:
        error_response = f"申し訳ありません。エラーが発生しました: {str(e)}"
        processing_msg.content = error_response
        await processing_msg.update()


async def handle_file_upload(elements, project_id: int, project_name: str):
    """ファイルアップロードの処理"""
    
    uploaded_files = []
    failed_files = []
    
    for element in elements:
        if element.mime and element.path:
            try:
                file_path = Path(element.path)
                filename = element.name or file_path.name
                
                # サポートされているファイルタイプかチェック
                file_extension = file_path.suffix.lower()
                
                print(f"ファイル: {filename}, 拡張子: '{file_extension}', サポート対象: {SUPPORTED_FILE_EXTENSIONS}")
                
                if file_extension not in SUPPORTED_FILE_EXTENSIONS:
                    failed_files.append(f"{filename} (サポートされていないファイル形式: {file_extension})")
                    continue
                
                # 処理開始メッセージ
                processing_msg = cl.Message(content=f"📄 {filename} を処理しています...")
                await processing_msg.send()
                
                # ファイルを処理
                success = await weaver.process_uploaded_file(file_path, filename, project_id)
                
                if success:
                    uploaded_files.append(filename)
                    processing_msg.content = f"✅ {filename} の処理が完了しました！"
                    await processing_msg.update()
                else:
                    failed_files.append(filename)
                    processing_msg.content = f"❌ {filename} の処理に失敗しました"
                    await processing_msg.update()
                    
            except Exception as e:
                failed_files.append(f"{element.name} ({str(e)})")
    
    # 結果サマリーを表示
    if uploaded_files or failed_files:
        summary_parts = []
        
        if uploaded_files:
            summary_parts.append(f"**✅ 成功 ({len(uploaded_files)}件):**\n" + 
                               "\n".join(f"- {name}" for name in uploaded_files))
        
        if failed_files:
            summary_parts.append(f"**❌ 失敗 ({len(failed_files)}件):**\n" + 
                               "\n".join(f"- {name}" for name in failed_files))
        
        summary = f"**📁 プロジェクト『{project_name}』ファイルアップロード結果**\n\n" + \
                 "\n\n".join(summary_parts)
        
        if uploaded_files:
            summary += "\n\n💡 アップロードされた文書について質問できるようになりました！"
        
        await cl.Message(content=summary).send()


# プロジェクト切り替えとナレッジ管理のアクション
@cl.action_callback("switch_project")
async def switch_project_action(action):
    """プロジェクト切り替えアクション"""
    await cl.Message(content="📁 プロジェクトを切り替えます...").send()
    await show_project_selection()


@cl.action_callback("manage_knowledge")
async def manage_knowledge_action(action):
    """ナレッジ管理アクション"""
    current_project_id = cl.user_session.get("current_project_id")
    current_project_name = cl.user_session.get("current_project_name")
    
    if not current_project_id:
        await cl.Message(content="⚠️ プロジェクトが選択されていません。").send()
        return
    
    try:
        if weaver.rag_engine:
            documents = await weaver.rag_engine.get_project_documents(current_project_id)
            
            if documents:
                doc_list = f"**📚 プロジェクト『{current_project_name}』のナレッジベース**\n\n"
                
                for doc in documents:
                    upload_date = doc['uploaded_at'][:10] if doc['uploaded_at'] else 'Unknown'
                    file_size = f"{doc['file_size'] / 1024:.1f}KB" if doc['file_size'] else 'Unknown'
                    doc_list += f"📄 **{doc['filename']}**\n"
                    doc_list += f"   - アップロード日: {upload_date}\n"
                    doc_list += f"   - ファイルサイズ: {file_size}\n\n"
                
                doc_list += "💡 新しい文書をアップロードするには、ファイルをドラッグ&ドロップしてください。"
                
            else:
                doc_list = f"**📚 プロジェクト『{current_project_name}』のナレッジベース**\n\n"
                doc_list += "📄 アップロードされた文書はありません。\n\n"
                doc_list += "💡 PDF、TXT、MDファイルをドラッグ&ドロップしてアップロードしてください。"
            
            await cl.Message(content=doc_list).send()
        else:
            await cl.Message(content="❌ ナレッジベース機能が利用できません").send()
            
    except Exception as e:
        await cl.Message(content=f"❌ ナレッジベース情報の取得に失敗しました: {str(e)}").send()


# メッセージにアクションボタンを常時表示するヘルパー関数
async def add_action_buttons():
    """アクションボタンを表示"""
    current_project_id = cl.user_session.get("current_project_id")
    
    if current_project_id:
        actions = [
            cl.Action(
                name="manage_knowledge",
                value="manage",
                payload={"action": "manage_knowledge"},
                label="📚 ナレッジ管理",
                description="現在のプロジェクトの文書を管理"
            ),
            cl.Action(
                name="switch_project",
                value="switch",
                payload={"action": "switch_project"},
                label="🔄 プロジェクト切替",
                description="別のプロジェクトに切り替え"
            )
        ]
        
        await cl.Message(
            content="**🛠️ 利用可能な操作:**",
            actions=actions
        ).send()


@cl.on_stop
async def on_stop():
    """チャット終了時の処理"""
    print("LocalAgentWeaver セッションが終了しました")


if __name__ == "__main__":
    print("🚀 LocalAgentWeaver を起動中...")
    print("Chainlit UI: http://localhost:8000")
    
    # Chainlitアプリを起動
    # 注意: このスクリプトは `chainlit run src/localagentweaver/main.py` で起動してください