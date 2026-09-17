"""
Модуль для логирования взаимодействий с ассистентом в SQLite.

Фрагмент для ДЗ по логированию (из проекта new_assist_bot):
DatabaseLogger, метрики get_stats(), экспорт CSV.
"""

from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class DatabaseLogger:
    """
    Логирует вопросы пользователей и ответы ассистента.

    Хранит:
    - query / response
    - метаданные (время, source, user_id для Telegram)
    - from_cache, response_time_ms
    """

    def __init__(self, db_path: str = "logs/interactions.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                username TEXT,
                source TEXT NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                from_cache INTEGER DEFAULT 0,
                response_time_ms INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON logs(source)")
        conn.commit()
        conn.close()

    def log_interaction(
        self,
        query: str,
        response: str,
        source: str = "console",
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        from_cache: bool = False,
        response_time_ms: Optional[int] = None,
    ) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO logs (
                timestamp, user_id, username, source, query, response,
                from_cache, response_time_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                user_id,
                username,
                source,
                query,
                response,
                1 if from_cache else 0,
                response_time_ms,
            ),
        )
        conn.commit()
        conn.close()

    def get_logs(
        self,
        limit: Optional[int] = None,
        user_id: Optional[str] = None,
        source: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM logs WHERE 1=1"
        params: list = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if source:
            query += " AND source = ?"
            params.append(source)
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        query += " ORDER BY timestamp DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs

    def export_to_csv(
        self,
        output_path: Optional[str] = None,
        user_id: Optional[str] = None,
        source: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        logs = self.get_logs(
            user_id=user_id,
            source=source,
            start_date=start_date,
            end_date=end_date,
        )
        if not logs:
            return ""

        fieldnames = [
            "id",
            "timestamp",
            "user_id",
            "username",
            "source",
            "query",
            "response",
            "from_cache",
            "response_time_ms",
            "created_at",
        ]

        if output_path:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(logs)
            return output_path

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(logs)
        return output.getvalue()

    def get_stats(self) -> dict:
        """Метрики для команды /stats и отчётов."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM logs")
        total_requests = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM logs WHERE from_cache = 1")
        cached_requests = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(DISTINCT user_id) FROM logs WHERE user_id IS NOT NULL"
        )
        unique_users = cursor.fetchone()[0]

        cursor.execute("SELECT source, COUNT(*) FROM logs GROUP BY source")
        by_source = dict(cursor.fetchall())

        cursor.execute(
            "SELECT AVG(response_time_ms) FROM logs WHERE response_time_ms IS NOT NULL"
        )
        avg_response_time = cursor.fetchone()[0]

        conn.close()

        return {
            "total_requests": total_requests,
            "cached_requests": cached_requests,
            "unique_users": unique_users,
            "by_source": by_source,
            "avg_response_time_ms": avg_response_time if avg_response_time else 0,
        }
