"""SQLite persistence of the best score (coins + level) per player.

Provides a ``ScoreStore`` that keeps a single best-score record per player
name and queries the Top N leaderboard ordered by coins descending. It uses
only the Python standard library ``sqlite3``; the database file ``scores.db``
lives in the repository root and is created on first use.
"""

import os
import sqlite3
from typing import List, Optional, Tuple

DB_FILE = "scores.db"

# (position, name, coins, level)
ScoreRow = Tuple[int, str, int, int]


def _repo_root() -> str:
    """Return the absolute path to the repository root.

    ``src/core/score_store.py`` sits two levels below the repository root.
    """
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )


class ScoreStore:
    """Persist the best score (coins + level) per player in a local SQLite DB."""

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path if db_path is not None else os.path.join(
            _repo_root(), DB_FILE
        )
        self._conn = sqlite3.connect(self._db_path)
        self._create_table()

    def _create_table(self) -> None:
        """Create the players table on first use (idempotent)."""
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                name TEXT PRIMARY KEY,
                coins INTEGER NOT NULL,
                level INTEGER NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self._conn.commit()

    def upsert_best(self, name: str, coins: int, level: int) -> None:
        """Insert a player record, or update it only when coins exceed the best.

        If the player already has a record and ``coins`` is greater than the
        stored value, the record is updated (coins, level, timestamp). If
        ``coins`` is lower or equal, the existing record is kept untouched.
        """
        name = name.strip()
        if not name:
            return
        with self._conn:
            existing = self._conn.execute(
                "SELECT coins FROM players WHERE name = ?", (name,)
            ).fetchone()
            if existing is None:
                self._conn.execute(
                    "INSERT INTO players (name, coins, level) VALUES (?, ?, ?)",
                    (name, coins, level),
                )
            elif coins > existing[0]:
                self._conn.execute(
                    "UPDATE players SET coins = ?, level = ?, "
                    "updated_at = CURRENT_TIMESTAMP WHERE name = ?",
                    (coins, level, name),
                )

    def top_scores(self, limit: int = 5) -> List[ScoreRow]:
        """Return up to ``limit`` records ordered by coins descending.

        Each row is ``(position, name, coins, level)`` with position starting
        at 1. Ties are broken by the earlier ``updated_at``.
        """
        rows = self._conn.execute(
            "SELECT name, coins, level FROM players "
            "ORDER BY coins DESC, updated_at ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            (i + 1, name, coins, level)
            for i, (name, coins, level) in enumerate(rows)
        ]

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self._conn.close()