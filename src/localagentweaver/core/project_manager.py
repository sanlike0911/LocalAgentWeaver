"""
プロジェクト管理モジュール
SQLiteを使用してプロジェクト情報を管理する
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Project:
    """プロジェクトデータクラス"""
    id: Optional[int]
    name: str
    created_at: datetime
    description: Optional[str] = None

class ProjectManager:
    """プロジェクト管理クラス"""
    
    def __init__(self, db_path: Path):
        """
        プロジェクトマネージャーの初期化
        
        Args:
            db_path: SQLiteデータベースファイルのパス
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """データベースとテーブルの初期化"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # プロジェクトテーブルを作成
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP NOT NULL
                    )
                """)
                
                # ドキュメントテーブルを作成（将来的に使用）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER NOT NULL,
                        filename TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        uploaded_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects (id)
                    )
                """)
                
                conn.commit()
                self.logger.info("データベース初期化完了")
                
        except sqlite3.Error as e:
            self.logger.error(f"データベース初期化エラー: {e}")
            raise
    
    def create_project(self, name: str, description: Optional[str] = None) -> int:
        """
        新しいプロジェクトを作成
        
        Args:
            name: プロジェクト名
            description: プロジェクト説明（オプション）
            
        Returns:
            作成されたプロジェクトのID
            
        Raises:
            ValueError: 重複するプロジェクト名の場合
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO projects (name, description, created_at)
                    VALUES (?, ?, ?)
                """, (name, description, datetime.now()))
                
                project_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"プロジェクト作成: ID={project_id}, Name={name}")
                return project_id
                
        except sqlite3.IntegrityError:
            raise ValueError(f"プロジェクト名 '{name}' は既に存在します")
        except sqlite3.Error as e:
            self.logger.error(f"プロジェクト作成エラー: {e}")
            raise
    
    def get_all_projects(self) -> List[Project]:
        """
        すべてのプロジェクトを取得
        
        Returns:
            プロジェクトのリスト
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, description, created_at
                    FROM projects
                    ORDER BY created_at DESC
                """)
                
                projects = []
                for row in cursor.fetchall():
                    projects.append(Project(
                        id=row[0],
                        name=row[1],
                        description=row[2],
                        created_at=datetime.fromisoformat(row[3])
                    ))
                
                return projects
                
        except sqlite3.Error as e:
            self.logger.error(f"プロジェクト取得エラー: {e}")
            raise
    
    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """
        IDでプロジェクトを取得
        
        Args:
            project_id: プロジェクトID
            
        Returns:
            プロジェクト（存在しない場合はNone）
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, description, created_at
                    FROM projects
                    WHERE id = ?
                """, (project_id,))
                
                row = cursor.fetchone()
                if row:
                    return Project(
                        id=row[0],
                        name=row[1],
                        description=row[2],
                        created_at=datetime.fromisoformat(row[3])
                    )
                
                return None
                
        except sqlite3.Error as e:
            self.logger.error(f"プロジェクト取得エラー (ID={project_id}): {e}")
            raise
    
    def delete_project(self, project_id: int) -> bool:
        """
        プロジェクトを削除
        
        Args:
            project_id: 削除するプロジェクトのID
            
        Returns:
            削除成功の場合True
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 関連するドキュメントも削除
                cursor.execute("DELETE FROM documents WHERE project_id = ?", (project_id,))
                
                # プロジェクトを削除
                cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                
                deleted = cursor.rowcount > 0
                conn.commit()
                
                if deleted:
                    self.logger.info(f"プロジェクト削除: ID={project_id}")
                
                return deleted
                
        except sqlite3.Error as e:
            self.logger.error(f"プロジェクト削除エラー (ID={project_id}): {e}")
            raise
    
    def get_project_stats(self, project_id: int) -> Dict[str, int]:
        """
        プロジェクトの統計情報を取得
        
        Args:
            project_id: プロジェクトID
            
        Returns:
            統計情報（ドキュメント数など）
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(*) FROM documents WHERE project_id = ?
                """, (project_id,))
                
                document_count = cursor.fetchone()[0]
                
                return {
                    "document_count": document_count
                }
                
        except sqlite3.Error as e:
            self.logger.error(f"プロジェクト統計取得エラー (ID={project_id}): {e}")
            raise