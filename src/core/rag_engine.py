"""
RAG (検索拡張生成) エンジンモジュール
ドキュメントの処理、ベクトル化、検索、生成を統合管理する
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import sqlite3
from datetime import datetime

import chromadb
from chromadb.config import Settings
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.chains import RetrievalQA
from langchain.vectorstores import Chroma
from langchain.prompts import PromptTemplate

class RAGEngine:
    """RAG (検索拡張生成) エンジン"""
    
    def __init__(
        self, 
        vector_db_path: Path,
        projects_db_path: Path,
        llm: Ollama,
        embeddings: OllamaEmbeddings
    ):
        """
        RAGエンジンの初期化
        
        Args:
            vector_db_path: ベクトルデータベースの保存パス
            projects_db_path: プロジェクトデータベースのパス
            llm: Ollama LLMインスタンス
            embeddings: Ollama Embeddingsインスタンス
        """
        self.vector_db_path = vector_db_path
        self.projects_db_path = projects_db_path
        self.llm = llm
        self.embeddings = embeddings
        self.logger = logging.getLogger(__name__)
        
        # ChromaDBクライアントの初期化
        self.chroma_client = chromadb.PersistentClient(
            path=str(vector_db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # テキスト分割器の初期化
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # RAGプロンプトテンプレート
        self.rag_prompt = PromptTemplate(
            template="""あなたは親切で知識豊富なAIアシスタントです。
提供されたコンテキスト情報を基に、ユーザーの質問に正確で有用な回答を提供してください。

コンテキスト情報:
{context}

質問: {question}

回答を提供する際は、以下の点に注意してください：
1. コンテキスト情報に基づいて回答してください
2. コンテキストに含まれていない情報については「提供された文書には記載されていません」と明記してください
3. 回答は日本語で提供してください
4. 可能であれば、情報の出典（文書名など）を含めてください

回答:""",
            input_variables=["context", "question"]
        )
    
    def get_project_collection_name(self, project_id: int) -> str:
        """プロジェクトIDからコレクション名を生成"""
        return f"project_{project_id}"
    
    async def process_document(self, file_path: Path, project_id: int, filename: str) -> bool:
        """
        ドキュメントを処理してベクトルデータベースに保存
        
        Args:
            file_path: ファイルパス
            project_id: プロジェクトID
            filename: ファイル名
            
        Returns:
            処理成功の場合True
        """
        try:
            self.logger.info(f"ドキュメント処理開始: {filename} (プロジェクト: {project_id})")
            
            # ドキュメントを読み込み
            documents = await self._load_document(file_path)
            
            if not documents:
                self.logger.warning(f"ドキュメントが読み込めませんでした: {filename}")
                return False
            
            # テキストを分割
            chunks = self.text_splitter.split_documents(documents)
            
            if not chunks:
                self.logger.warning(f"有効なテキストチャンクが作成できませんでした: {filename}")
                return False
            
            # メタデータを追加
            for chunk in chunks:
                chunk.metadata.update({
                    "project_id": project_id,
                    "filename": filename,
                    "processed_at": datetime.now().isoformat()
                })
            
            # ベクトルデータベースに保存
            await self._store_chunks(chunks, project_id)
            
            # ドキュメント情報をSQLiteに記録
            await self._record_document(project_id, filename, file_path, len(chunks))
            
            self.logger.info(f"ドキュメント処理完了: {filename} ({len(chunks)}チャンク)")
            return True
            
        except Exception as e:
            self.logger.error(f"ドキュメント処理エラー ({filename}): {e}")
            return False
    
    async def _load_document(self, file_path: Path) -> List[Document]:
        """ファイルタイプに応じてドキュメントを読み込み"""
        suffix = file_path.suffix.lower()
        
        try:
            if suffix == '.pdf':
                loader = PyPDFLoader(str(file_path))
            elif suffix in ['.txt', '.md']:
                loader = TextLoader(str(file_path), encoding='utf-8')
            else:
                raise ValueError(f"サポートされていないファイルタイプ: {suffix}")
            
            # 非同期でドキュメントを読み込み
            documents = await asyncio.get_event_loop().run_in_executor(
                None, loader.load
            )
            
            return documents
            
        except Exception as e:
            self.logger.error(f"ドキュメント読み込みエラー ({file_path}): {e}")
            return []
    
    async def _store_chunks(self, chunks: List[Document], project_id: int):
        """チャンクをベクトルデータベースに保存"""
        collection_name = self.get_project_collection_name(project_id)
        
        try:
            # コレクションを取得または作成
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"project_id": project_id}
            )
            
            # テキストとメタデータを準備
            texts = [chunk.page_content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            ids = [f"{project_id}_{i}_{datetime.now().timestamp()}" 
                  for i in range(len(chunks))]
            
            # ベクトル化して保存
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"ベクトルDB保存完了: {len(chunks)}チャンク (コレクション: {collection_name})")
            
        except Exception as e:
            self.logger.error(f"ベクトルDB保存エラー: {e}")
            raise
    
    async def _record_document(self, project_id: int, filename: str, file_path: Path, chunk_count: int):
        """ドキュメント情報をSQLiteに記録"""
        try:
            with sqlite3.connect(self.projects_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO documents (project_id, filename, file_path, file_size, uploaded_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    project_id,
                    filename,
                    str(file_path),
                    file_path.stat().st_size if file_path.exists() else 0,
                    datetime.now()
                ))
                
                conn.commit()
                self.logger.info(f"ドキュメント記録完了: {filename}")
                
        except Exception as e:
            self.logger.error(f"ドキュメント記録エラー: {e}")
            raise
    
    async def search_and_generate(self, query: str, project_id: int, top_k: int = 5) -> Dict[str, Any]:
        """
        クエリに基づいてドキュメントを検索し、RAG回答を生成
        
        Args:
            query: 検索クエリ
            project_id: プロジェクトID
            top_k: 取得する関連文書数
            
        Returns:
            回答と関連情報を含む辞書
        """
        try:
            # 関連文書を検索
            relevant_docs = await self._search_documents(query, project_id, top_k)
            
            if not relevant_docs:
                return {
                    "answer": "申し訳ありません。関連する情報が見つかりませんでした。ドキュメントをアップロードしてから質問してください。",
                    "sources": [],
                    "context_used": False
                }
            
            # コンテキストを構築
            context = self._build_context(relevant_docs)
            
            # RAG回答を生成
            answer = await self._generate_answer(query, context)
            
            # ソース情報を抽出
            sources = self._extract_sources(relevant_docs)
            
            return {
                "answer": answer,
                "sources": sources,
                "context_used": True,
                "num_sources": len(sources)
            }
            
        except Exception as e:
            self.logger.error(f"RAG処理エラー: {e}")
            return {
                "answer": f"申し訳ありません。処理中にエラーが発生しました: {str(e)}",
                "sources": [],
                "context_used": False
            }
    
    async def _search_documents(self, query: str, project_id: int, top_k: int) -> List[Dict]:
        """プロジェクトのドキュメントから関連文書を検索"""
        collection_name = self.get_project_collection_name(project_id)
        
        try:
            # コレクションを取得
            collection = self.chroma_client.get_collection(name=collection_name)
            
            # 検索実行
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # 結果を整形
            documents = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    documents.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'score': 1 - results['distances'][0][i] if results['distances'] else 0
                    })
            
            self.logger.info(f"文書検索完了: {len(documents)}件")
            return documents
            
        except Exception as e:
            self.logger.error(f"文書検索エラー: {e}")
            return []
    
    def _build_context(self, relevant_docs: List[Dict]) -> str:
        """関連文書からコンテキストを構築"""
        context_parts = []
        
        for i, doc in enumerate(relevant_docs, 1):
            filename = doc['metadata'].get('filename', 'Unknown')
            content = doc['content']
            score = doc['score']
            
            context_parts.append(f"[文書{i}: {filename} (関連度: {score:.2f})]\n{content}")
        
        return "\n\n".join(context_parts)
    
    async def _generate_answer(self, query: str, context: str) -> str:
        """RAGプロンプトを使用して回答を生成"""
        try:
            prompt = self.rag_prompt.format(context=context, question=query)
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.llm.invoke, prompt
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"回答生成エラー: {e}")
            return f"回答の生成中にエラーが発生しました: {str(e)}"
    
    def _extract_sources(self, relevant_docs: List[Dict]) -> List[Dict]:
        """関連文書からソース情報を抽出"""
        sources = []
        seen_files = set()
        
        for doc in relevant_docs:
            filename = doc['metadata'].get('filename', 'Unknown')
            
            if filename not in seen_files:
                sources.append({
                    'filename': filename,
                    'score': doc['score']
                })
                seen_files.add(filename)
        
        return sources
    
    async def get_project_documents(self, project_id: int) -> List[Dict]:
        """プロジェクトのドキュメント一覧を取得"""
        try:
            with sqlite3.connect(self.projects_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, filename, file_size, uploaded_at
                    FROM documents
                    WHERE project_id = ?
                    ORDER BY uploaded_at DESC
                """, (project_id,))
                
                documents = []
                for row in cursor.fetchall():
                    documents.append({
                        'id': row[0],
                        'filename': row[1],
                        'file_size': row[2],
                        'uploaded_at': row[3]
                    })
                
                return documents
                
        except Exception as e:
            self.logger.error(f"ドキュメント一覧取得エラー: {e}")
            return []
    
    async def delete_document(self, project_id: int, document_id: int) -> bool:
        """ドキュメントを削除"""
        try:
            # SQLiteから削除
            with sqlite3.connect(self.projects_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM documents
                    WHERE id = ? AND project_id = ?
                """, (document_id, project_id))
                
                deleted = cursor.rowcount > 0
                conn.commit()
            
            # TODO: ChromaDBからも関連チャンクを削除
            # 現在のChromaDBの制限により、個別チャンクの削除は複雑
            # 将来的には、メタデータでフィルタして削除を実装
            
            if deleted:
                self.logger.info(f"ドキュメント削除完了: ID={document_id}")
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"ドキュメント削除エラー: {e}")
            return False