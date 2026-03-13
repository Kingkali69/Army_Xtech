"""
GhostAI Database Module
Handles data persistence for engagements, learned patterns, and user history.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class Engagement:
    """Represents a security engagement."""
    engagement_id: str
    contract_data: Dict[str, Any]
    created_at: str
    status: str  # 'pending', 'in_progress', 'completed', 'failed'
    results: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    tools_used: Optional[List[str]] = None
    targets: Optional[List[str]] = None
    findings: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class LearnedPattern:
    """Represents a learned pattern from execution."""
    pattern_id: str
    target_type: str  # 'linux', 'windows', 'network', etc.
    tool_chain: List[str]
    success_rate: float
    avg_execution_time: float
    conditions: Dict[str, Any]
    created_at: str
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class UserHistory:
    """Represents user execution history."""
    history_id: str
    user_id: str
    engagement_id: str
    action: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class GhostAIDatabase:
    """Database manager for GhostAI."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database.

        Args:
            db_path: Path to SQLite database file. Defaults to ~/.ghostops/ghostai.db
        """
        if db_path is None:
            home = Path.home()
            ghostops_dir = home / ".ghostops"
            ghostops_dir.mkdir(exist_ok=True)
            db_path = str(ghostops_dir / "ghostai.db")

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Engagements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS engagements (
                    engagement_id TEXT PRIMARY KEY,
                    contract_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    results TEXT,
                    execution_time REAL,
                    tools_used TEXT,
                    targets TEXT,
                    findings TEXT
                )
            """)

            # Learned patterns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    target_type TEXT NOT NULL,
                    tool_chain TEXT NOT NULL,
                    success_rate REAL NOT NULL,
                    avg_execution_time REAL NOT NULL,
                    conditions TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0
                )
            """)

            # User history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_history (
                    history_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    engagement_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY (engagement_id) REFERENCES engagements(engagement_id)
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_engagements_status
                ON engagements(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_engagements_created
                ON engagements(created_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_target_type
                ON learned_patterns(target_type)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_success_rate
                ON learned_patterns(success_rate)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_user
                ON user_history(user_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_timestamp
                ON user_history(timestamp)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # Engagement operations
    def create_engagement(self, engagement: Engagement) -> bool:
        """Create a new engagement.

        Args:
            engagement: Engagement object to create

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO engagements (
                        engagement_id, contract_data, created_at, status,
                        results, execution_time, tools_used, targets, findings
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    engagement.engagement_id,
                    json.dumps(engagement.contract_data),
                    engagement.created_at,
                    engagement.status,
                    json.dumps(engagement.results) if engagement.results else None,
                    engagement.execution_time,
                    json.dumps(engagement.tools_used) if engagement.tools_used else None,
                    json.dumps(engagement.targets) if engagement.targets else None,
                    json.dumps(engagement.findings) if engagement.findings else None
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating engagement: {e}")
            return False

    def get_engagement(self, engagement_id: str) -> Optional[Engagement]:
        """Get engagement by ID.

        Args:
            engagement_id: Engagement ID

        Returns:
            Engagement object or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM engagements WHERE engagement_id = ?
                """, (engagement_id,))
                row = cursor.fetchone()

                if row:
                    return Engagement(
                        engagement_id=row['engagement_id'],
                        contract_data=json.loads(row['contract_data']),
                        created_at=row['created_at'],
                        status=row['status'],
                        results=json.loads(row['results']) if row['results'] else None,
                        execution_time=row['execution_time'],
                        tools_used=json.loads(row['tools_used']) if row['tools_used'] else None,
                        targets=json.loads(row['targets']) if row['targets'] else None,
                        findings=json.loads(row['findings']) if row['findings'] else None
                    )
                return None
        except Exception as e:
            print(f"Error getting engagement: {e}")
            return None

    def update_engagement(self, engagement_id: str, updates: Dict[str, Any]) -> bool:
        """Update engagement.

        Args:
            engagement_id: Engagement ID
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build update query dynamically
            allowed_fields = ['status', 'results', 'execution_time', 'tools_used', 'targets', 'findings']
            update_fields = []
            values = []

            for field, value in updates.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    if field in ['results', 'tools_used', 'targets', 'findings'] and value is not None:
                        values.append(json.dumps(value))
                    else:
                        values.append(value)

            if not update_fields:
                return False

            values.append(engagement_id)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = f"UPDATE engagements SET {', '.join(update_fields)} WHERE engagement_id = ?"
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating engagement: {e}")
            return False

    def list_engagements(self,
                        status: Optional[str] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        limit: int = 100) -> List[Engagement]:
        """List engagements with optional filters.

        Args:
            status: Filter by status
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            limit: Maximum number of results

        Returns:
            List of Engagement objects
        """
        try:
            query = "SELECT * FROM engagements WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if start_date:
                query += " AND created_at >= ?"
                params.append(start_date)

            if end_date:
                query += " AND created_at <= ?"
                params.append(end_date)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [
                    Engagement(
                        engagement_id=row['engagement_id'],
                        contract_data=json.loads(row['contract_data']),
                        created_at=row['created_at'],
                        status=row['status'],
                        results=json.loads(row['results']) if row['results'] else None,
                        execution_time=row['execution_time'],
                        tools_used=json.loads(row['tools_used']) if row['tools_used'] else None,
                        targets=json.loads(row['targets']) if row['targets'] else None,
                        findings=json.loads(row['findings']) if row['findings'] else None
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"Error listing engagements: {e}")
            return []

    # Learned patterns operations
    def create_pattern(self, pattern: LearnedPattern) -> bool:
        """Create a new learned pattern.

        Args:
            pattern: LearnedPattern object to create

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO learned_patterns (
                        pattern_id, target_type, tool_chain, success_rate,
                        avg_execution_time, conditions, created_at, usage_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern.pattern_id,
                    pattern.target_type,
                    json.dumps(pattern.tool_chain),
                    pattern.success_rate,
                    pattern.avg_execution_time,
                    json.dumps(pattern.conditions),
                    pattern.created_at,
                    pattern.usage_count
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating pattern: {e}")
            return False

    def get_patterns_by_target_type(self, target_type: str, min_success_rate: float = 0.0) -> List[LearnedPattern]:
        """Get learned patterns for a target type.

        Args:
            target_type: Target type (e.g., 'windows', 'linux')
            min_success_rate: Minimum success rate filter

        Returns:
            List of LearnedPattern objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM learned_patterns
                    WHERE target_type = ? AND success_rate >= ?
                    ORDER BY success_rate DESC, usage_count DESC
                """, (target_type, min_success_rate))
                rows = cursor.fetchall()

                return [
                    LearnedPattern(
                        pattern_id=row['pattern_id'],
                        target_type=row['target_type'],
                        tool_chain=json.loads(row['tool_chain']),
                        success_rate=row['success_rate'],
                        avg_execution_time=row['avg_execution_time'],
                        conditions=json.loads(row['conditions']),
                        created_at=row['created_at'],
                        usage_count=row['usage_count']
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting patterns: {e}")
            return []

    def update_pattern_stats(self, pattern_id: str, success_rate: float, avg_execution_time: float) -> bool:
        """Update pattern statistics.

        Args:
            pattern_id: Pattern ID
            success_rate: New success rate
            avg_execution_time: New average execution time

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE learned_patterns
                    SET success_rate = ?, avg_execution_time = ?, usage_count = usage_count + 1
                    WHERE pattern_id = ?
                """, (success_rate, avg_execution_time, pattern_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating pattern stats: {e}")
            return False

    def get_best_patterns(self, limit: int = 10) -> List[LearnedPattern]:
        """Get best performing patterns.

        Args:
            limit: Maximum number of results

        Returns:
            List of LearnedPattern objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM learned_patterns
                    ORDER BY success_rate DESC, usage_count DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()

                return [
                    LearnedPattern(
                        pattern_id=row['pattern_id'],
                        target_type=row['target_type'],
                        tool_chain=json.loads(row['tool_chain']),
                        success_rate=row['success_rate'],
                        avg_execution_time=row['avg_execution_time'],
                        conditions=json.loads(row['conditions']),
                        created_at=row['created_at'],
                        usage_count=row['usage_count']
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting best patterns: {e}")
            return []

    # User history operations
    def add_history(self, history: UserHistory) -> bool:
        """Add user history entry.

        Args:
            history: UserHistory object to add

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_history (
                        history_id, user_id, engagement_id, action, timestamp, details
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    history.history_id,
                    history.user_id,
                    history.engagement_id,
                    history.action,
                    history.timestamp,
                    json.dumps(history.details) if history.details else None
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding history: {e}")
            return False

    def get_user_history(self, user_id: str, limit: int = 100) -> List[UserHistory]:
        """Get user history.

        Args:
            user_id: User ID
            limit: Maximum number of results

        Returns:
            List of UserHistory objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM user_history
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
                rows = cursor.fetchall()

                return [
                    UserHistory(
                        history_id=row['history_id'],
                        user_id=row['user_id'],
                        engagement_id=row['engagement_id'],
                        action=row['action'],
                        timestamp=row['timestamp'],
                        details=json.loads(row['details']) if row['details'] else None
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting user history: {e}")
            return []

    # Analytics queries
    def get_engagement_stats(self, quarter: Optional[str] = None) -> Dict[str, Any]:
        """Get engagement statistics.

        Args:
            quarter: Optional quarter filter (e.g., 'Q4')

        Returns:
            Dictionary with statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Build date filter for quarter
                where_clause = ""
                params = []
                if quarter:
                    # Parse quarter (e.g., Q4 -> Oct-Dec)
                    quarter_months = {
                        'Q1': ('01', '03'),
                        'Q2': ('04', '06'),
                        'Q3': ('07', '09'),
                        'Q4': ('10', '12')
                    }
                    if quarter.upper() in quarter_months:
                        start_month, end_month = quarter_months[quarter.upper()]
                        current_year = datetime.now().year
                        where_clause = " WHERE created_at >= ? AND created_at <= ?"
                        params = [f"{current_year}-{start_month}-01", f"{current_year}-{end_month}-31"]

                # Total engagements
                cursor.execute(f"SELECT COUNT(*) as total FROM engagements{where_clause}", params)
                total = cursor.fetchone()['total']

                # By status
                cursor.execute(f"""
                    SELECT status, COUNT(*) as count
                    FROM engagements{where_clause}
                    GROUP BY status
                """, params)
                by_status = {row['status']: row['count'] for row in cursor.fetchall()}

                # Average execution time
                cursor.execute(f"""
                    SELECT AVG(execution_time) as avg_time
                    FROM engagements
                    WHERE execution_time IS NOT NULL{' AND ' + where_clause[7:] if where_clause else ''}
                """, params)
                avg_time = cursor.fetchone()['avg_time'] or 0.0

                return {
                    'total_engagements': total,
                    'by_status': by_status,
                    'average_execution_time': avg_time
                }
        except Exception as e:
            print(f"Error getting engagement stats: {e}")
            return {}

    def get_tool_performance(self, target_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tool performance statistics.

        Args:
            target_type: Optional target type filter

        Returns:
            List of tool performance data
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                where_clause = ""
                params = []
                if target_type:
                    where_clause = " WHERE target_type = ?"
                    params = [target_type]

                cursor.execute(f"""
                    SELECT
                        target_type,
                        tool_chain,
                        success_rate,
                        avg_execution_time,
                        usage_count
                    FROM learned_patterns{where_clause}
                    ORDER BY success_rate DESC, usage_count DESC
                """, params)

                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting tool performance: {e}")
            return []


# Global database instance
_db_instance: Optional[GhostAIDatabase] = None


def get_database() -> GhostAIDatabase:
    """Get global database instance.

    Returns:
        GhostAIDatabase instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = GhostAIDatabase()
    return _db_instance
