"""
Создаёт обезличенные samples из локальной БД new_assist_bot:
- interactions_redacted.db
- logs_redacted.csv
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

SRC_DB = Path(r"C:\Users\Dominique\.cursor\new_assist_bot\logs\interactions.db")
OUT_DIR = Path(__file__).resolve().parent.parent / "samples"
OUT_DB = OUT_DIR / "interactions_redacted.db"
OUT_CSV = OUT_DIR / "logs_redacted.csv"


def redact_user_id(raw: str | None, mapping: dict[str, str]) -> str | None:
    """Один фиксированный демо-id, как просил куратор: 123456789."""
    if raw is None or raw == "":
        return raw
    key = str(raw)
    if key not in mapping:
        mapping[key] = "123456789"
    return mapping[key]


def redact_username(raw: str | None) -> str | None:
    if raw is None or raw == "":
        return raw
    return "user_***"


def main() -> None:
    if not SRC_DB.exists():
        raise SystemExit(f"Исходная БД не найдена: {SRC_DB}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if OUT_DB.exists():
        OUT_DB.unlink()

    src = sqlite3.connect(SRC_DB)
    src.row_factory = sqlite3.Row
    rows = src.execute("SELECT * FROM logs ORDER BY id").fetchall()
    src.close()

    dst = sqlite3.connect(OUT_DB)
    dst.execute(
        """
        CREATE TABLE logs (
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

    id_map: dict[str, str] = {}
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
    csv_rows = []

    for row in rows:
        d = dict(row)
        d["user_id"] = redact_user_id(d.get("user_id"), id_map)
        d["username"] = redact_username(d.get("username"))
        # На всякий случай не тащим длинные ответы целиком в публичный семпл — обрезаем
        resp = d.get("response") or ""
        if len(resp) > 500:
            d["response"] = resp[:500] + "…"
        q = d.get("query") or ""
        if len(q) > 300:
            d["query"] = q[:300] + "…"

        dst.execute(
            """
            INSERT INTO logs (
                id, timestamp, user_id, username, source, query, response,
                from_cache, response_time_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                d.get("id"),
                d.get("timestamp"),
                d.get("user_id"),
                d.get("username"),
                d.get("source"),
                d.get("query"),
                d.get("response"),
                d.get("from_cache") or 0,
                d.get("response_time_ms"),
                d.get("created_at"),
            ),
        )
        csv_rows.append({k: d.get(k) for k in fieldnames})

    dst.commit()
    dst.close()

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"OK: {len(csv_rows)} rows")
    print(f"  {OUT_DB}")
    print(f"  {OUT_CSV}")
    print(f"  redacted user_ids: {id_map}")


if __name__ == "__main__":
    main()
