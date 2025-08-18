"""
プロジェクトマネージャーのテスト
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime

from modules.project_manager import ProjectManager, Project


class TestProjectManager:
    """ProjectManagerのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される準備処理"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_projects.db"
        self.pm = ProjectManager(self.db_path)
    
    def test_init_database(self):
        """データベース初期化のテスト"""
        # テーブルが作成されているか確認
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # projectsテーブルの存在確認
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='projects'
            """)
            assert cursor.fetchone() is not None
            
            # documentsテーブルの存在確認
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='documents'
            """)
            assert cursor.fetchone() is not None
    
    def test_create_project(self):
        """プロジェクト作成のテスト"""
        project_id = self.pm.create_project("テストプロジェクト", "テスト用のプロジェクトです")
        
        assert project_id is not None
        assert isinstance(project_id, int)
        
        # データベースに保存されているか確認
        project = self.pm.get_project_by_id(project_id)
        assert project is not None
        assert project.name == "テストプロジェクト"
        assert project.description == "テスト用のプロジェクトです"
    
    def test_create_duplicate_project(self):
        """重複プロジェクト名のテスト"""
        self.pm.create_project("重複テスト")
        
        # 同じ名前で作成を試行
        with pytest.raises(ValueError):
            self.pm.create_project("重複テスト")
    
    def test_get_all_projects(self):
        """全プロジェクト取得のテスト"""
        # 初期状態では空
        projects = self.pm.get_all_projects()
        assert len(projects) == 0
        
        # プロジェクトを追加
        self.pm.create_project("プロジェクト1")
        self.pm.create_project("プロジェクト2")
        
        projects = self.pm.get_all_projects()
        assert len(projects) == 2
        assert all(isinstance(p, Project) for p in projects)
    
    def test_get_project_by_id(self):
        """ID指定プロジェクト取得のテスト"""
        project_id = self.pm.create_project("IDテスト")
        
        project = self.pm.get_project_by_id(project_id)
        assert project is not None
        assert project.id == project_id
        assert project.name == "IDテスト"
        
        # 存在しないIDの場合
        non_existent = self.pm.get_project_by_id(99999)
        assert non_existent is None
    
    def test_delete_project(self):
        """プロジェクト削除のテスト"""
        project_id = self.pm.create_project("削除テスト")
        
        # 削除実行
        result = self.pm.delete_project(project_id)
        assert result is True
        
        # 削除されているか確認
        project = self.pm.get_project_by_id(project_id)
        assert project is None
        
        # 存在しないプロジェクトの削除
        result = self.pm.delete_project(99999)
        assert result is False
    
    def test_get_project_stats(self):
        """プロジェクト統計のテスト"""
        project_id = self.pm.create_project("統計テスト")
        
        stats = self.pm.get_project_stats(project_id)
        assert isinstance(stats, dict)
        assert "document_count" in stats
        assert stats["document_count"] == 0  # 初期状態では0