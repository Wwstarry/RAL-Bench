"""
Database module for TinyDB.
"""
import json
import os
from typing import Dict, List, Optional, Any, Union
from .table import Table
from .storages import Storage, JSONStorage


class TinyDB:
    """Main database class for TinyDB."""
    
    def __init__(self, path: str, storage: Storage = None):
        """
        Initialize a TinyDB instance.
        
        Args:
            path: Path to the JSON file
            storage: Storage class to use (defaults to JSONStorage)
        """
        self.path = path
        self.storage = storage or JSONStorage(path)
        self._tables: Dict[str, Table] = {}
        self._load_tables()
    
    def _load_tables(self) -> None:
        """Load existing tables from storage."""
        data = self.storage.read()
        if data:
            for table_name, table_data in data.items():
                self._tables[table_name] = Table(table_name, self.storage, table_data)
    
    def table(self, name: str) -> Table:
        """
        Get or create a table.
        
        Args:
            name: Name of the table
            
        Returns:
            Table instance
        """
        if name not in self._tables:
            self._tables[name] = Table(name, self.storage)
        return self._tables[name]
    
    def tables(self) -> List[str]:
        """
        Get list of all table names.
        
        Returns:
            List of table names
        """
        return list(self._tables.keys())
    
    def drop_table(self, name: str) -> None:
        """
        Drop a table.
        
        Args:
            name: Name of the table to drop
        """
        if name in self._tables:
            del self._tables[name]
            self._sync()
    
    def close(self) -> None:
        """Close the database and write all changes to disk."""
        self._sync()
    
    def _sync(self) -> None:
        """Sync all tables to storage."""
        data = {}
        for table_name, table in self._tables.items():
            data[table_name] = table._get_all()
        self.storage.write(data)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class TaskManager:
    """High-level task manager built on TinyDB."""
    
    def __init__(self, db_path: str = "tasks.json"):
        """
        Initialize task manager.
        
        Args:
            db_path: Path to the database file
        """
        self.db = TinyDB(db_path)
        self.tasks = self.db.table("tasks")
        self.projects = self.db.table("projects")
    
    def create_task(self, title: str, project: str = "default", 
                   description: str = "", estimate: int = 0) -> int:
        """
        Create a new task.
        
        Args:
            title: Task title
            project: Project name
            description: Task description
            estimate: Estimated time in minutes
            
        Returns:
            Task ID
        """
        task = {
            "title": title,
            "project": project,
            "description": description,
            "status": "todo",
            "estimate": estimate,
            "created_at": self._current_timestamp(),
            "updated_at": self._current_timestamp()
        }
        return self.tasks.insert(task)
    
    def create_project(self, name: str, description: str = "") -> int:
        """
        Create a new project.
        
        Args:
            name: Project name
            description: Project description
            
        Returns:
            Project ID
        """
        project = {
            "name": name,
            "description": description,
            "created_at": self._current_timestamp()
        }
        return self.projects.insert(project)
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        """
        Update task fields.
        
        Args:
            task_id: ID of task to update
            **kwargs: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if "updated_at" not in kwargs:
            kwargs["updated_at"] = self._current_timestamp()
        
        return self.tasks.update(kwargs, doc_ids=[task_id])
    
    def delete_task(self, task_id: int) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: ID of task to delete
            
        Returns:
            True if successful, False otherwise
        """
        return self.tasks.remove(doc_ids=[task_id])
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task document or None
        """
        tasks = self.tasks.get(doc_id=task_id)
        return tasks
    
    def get_tasks(self, project: str = None, status: str = None) -> List[Dict]:
        """
        Get tasks with optional filters.
        
        Args:
            project: Filter by project name
            status: Filter by status
            
        Returns:
            List of task documents
        """
        query = self.tasks._query_builder()
        
        if project:
            query = query & (self.tasks._query_builder().project == project)
        
        if status:
            query = query & (self.tasks._query_builder().status == status)
        
        return self.tasks.search(query)
    
    def get_unfinished_tasks_per_project(self) -> Dict[str, int]:
        """
        Get count of unfinished tasks per project.
        
        Returns:
            Dictionary mapping project names to unfinished task counts
        """
        unfinished = self.get_tasks(status="todo")
        result = {}
        
        for task in unfinished:
            project = task["project"]
            result[project] = result.get(project, 0) + 1
        
        return result
    
    def get_total_estimate(self, project: str = None) -> int:
        """
        Get total estimate for tasks.
        
        Args:
            project: Optional project filter
            
        Returns:
            Total estimate in minutes
        """
        tasks = self.get_tasks(project=project)
        return sum(task.get("estimate", 0) for task in tasks)
    
    def change_task_status(self, task_id: int, status: str) -> bool:
        """
        Change task status.
        
        Args:
            task_id: Task ID
            status: New status
            
        Returns:
            True if successful
        """
        return self.update_task(task_id, status=status)
    
    def _current_timestamp(self) -> str:
        """Get current timestamp as ISO format string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def close(self):
        """Close the database."""
        self.db.close()