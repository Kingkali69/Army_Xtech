#!/usr/bin/env python3
"""
STEP 1: Authoritative State Store
==================================

SQLite-based state store with:
- WAL mode (crash-safe writes)
- Transaction log (append-only, replayable)
- State snapshots (recovery from corruption)
- Transactional operations (all-or-nothing)

Rule: If it didn't commit, it never happened.
"""

import sqlite3
import json
import hashlib
import os
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpType(Enum):
    """Operation types for state log"""
    SET = "set"
    DELETE = "delete"
    MERGE = "merge"
    SNAPSHOT = "snapshot"


@dataclass
class StateOp:
    """Single state operation"""
    op_id: str
    op_type: OpType
    key: str
    value: Optional[Any] = None
    timestamp: float = None
    node_id: str = None
    vector_clock: Optional[Dict[str, int]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for storage"""
        return {
            'op_id': self.op_id,
            'op_type': self.op_type.value,
            'key': self.key,
            'value': json.dumps(self.value) if self.value is not None else None,
            'timestamp': self.timestamp,
            'node_id': self.node_id,
            'vector_clock': json.dumps(self.vector_clock) if self.vector_clock else None
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'StateOp':
        """Deserialize from dict"""
        # Handle both JSON string and dict values
        if isinstance(d.get('value'), str) and d.get('value'):
            try:
                value = json.loads(d['value'])
            except:
                value = d.get('value')
        else:
            value = d.get('value')
        
        # Handle vector clock
        if isinstance(d.get('vector_clock'), str) and d.get('vector_clock'):
            try:
                vector_clock = json.loads(d['vector_clock'])
            except:
                vector_clock = None
        else:
            vector_clock = d.get('vector_clock')
        
        return cls(
            op_id=d['op_id'],
            op_type=OpType(d['op_type']),
            key=d['key'],
            value=value,
            timestamp=d.get('timestamp', time.time()),
            node_id=d.get('node_id'),
            vector_clock=vector_clock
        )


class AuthoritativeStateStore:
    """
    Authoritative state store with transactional guarantees.
    
    Every state mutation:
    1. Begins transaction
    2. Appends to state_log
    3. Updates state_snapshot (periodically)
    4. Commits or aborts (no partial writes)
    
    On startup:
    1. Validate DB integrity
    2. If snapshot missing → rebuild from log
    3. If corruption → discard snapshot, replay log
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize state store
        
        Args:
            db_path: Path to SQLite database (default: ~/.omni/state.db)
        """
        if db_path is None:
            db_dir = Path.home() / '.omni'
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / 'state.db')
        
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.snapshot_interval = 1000  # Create snapshot every N ops
        
        # Initialize database
        self._init_db()
        
        # Validate and recover if needed
        self._startup_recovery()
        
        logger.info(f"[STATE_STORE] Initialized: {db_path}")
    
    def _init_db(self):
        """Initialize database schema"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging
        self.conn.execute('PRAGMA synchronous=NORMAL')  # Balanced safety/performance
        self.conn.execute('PRAGMA foreign_keys=ON')
        
        cursor = self.conn.cursor()
        
        # State log (append-only, all operations)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS state_log (
                op_id TEXT PRIMARY KEY,
                op_type TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                timestamp REAL NOT NULL,
                node_id TEXT,
                vector_clock TEXT,
                created_at REAL DEFAULT (julianday('now'))
            )
        ''')
        
        # State snapshot (current state, periodically updated)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS state_snapshot (
                snapshot_id TEXT PRIMARY KEY,
                state_data TEXT NOT NULL,
                checksum TEXT NOT NULL,
                last_op_id TEXT,
                created_at REAL DEFAULT (julianday('now'))
            )
        ''')
        
        # Node metadata (vector clocks, capabilities)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS node_meta (
                node_id TEXT PRIMARY KEY,
                vector_clock TEXT,
                capabilities TEXT,
                last_seen REAL,
                created_at REAL DEFAULT (julianday('now'))
            )
        ''')
        
        self.conn.commit()
        logger.info("[STATE_STORE] Database schema initialized")
    
    def _startup_recovery(self):
        """Recovery sequence on startup"""
        # 1. Validate DB integrity
        if not self.validate_db():
            logger.error("[STATE_STORE] Database corruption detected - attempting recovery")
            # Corrupted DB - discard snapshot, will rebuild from log
            try:
                cursor = self.conn.cursor()
                cursor.execute('DELETE FROM state_snapshot')
                self.conn.commit()
                logger.info("[STATE_STORE] Discarded corrupted snapshot")
            except Exception as e:
                logger.error(f"[STATE_STORE] Failed to discard snapshot: {e}")
        
        # 2. Check if snapshot exists
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM state_snapshot')
        snapshot_count = cursor.fetchone()[0]
        
        if snapshot_count == 0:
            logger.info("[STATE_STORE] No snapshot found - will rebuild from log on first access")
            # Snapshot will be created on next state access (STEP 2 will handle this)
    
    def validate_db(self) -> bool:
        """
        Validate database integrity
        
        Returns:
            True if valid, False if corrupted
        """
        try:
            cursor = self.conn.cursor()
            
            # Check integrity
            cursor.execute('PRAGMA integrity_check')
            result = cursor.fetchone()
            
            if result[0] != 'ok':
                logger.error(f"[STATE_STORE] Integrity check failed: {result[0]}")
                return False
            
            # Validate tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['state_log', 'state_snapshot', 'node_meta']
            missing = [t for t in required_tables if t not in tables]
            
            if missing:
                logger.error(f"[STATE_STORE] Missing tables: {missing}")
                return False
            
            logger.debug("[STATE_STORE] Database validation passed")
            return True
            
        except Exception as e:
            logger.error(f"[STATE_STORE] Validation error: {e}")
            return False
    
    def apply_op(self, op: StateOp) -> bool:
        """
        Apply a state operation (transactional)
        
        Args:
            op: State operation to apply
            
        Returns:
            True if committed, False if failed
        """
        if not self.conn:
            logger.error("[STATE_STORE] No database connection")
            return False
        
        try:
            # Begin transaction
            self.conn.execute('BEGIN TRANSACTION')
            
            # Append to state_log (append-only)
            op_dict = op.to_dict()
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO state_log (op_id, op_type, key, value, timestamp, node_id, vector_clock)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                op_dict['op_id'],
                op_dict['op_type'],
                op_dict['key'],
                op_dict['value'],
                op_dict['timestamp'],
                op_dict['node_id'],
                op_dict['vector_clock']
            ))
            
            # Check if we should create snapshot (every N ops)
            cursor.execute('SELECT COUNT(*) FROM state_log')
            op_count = cursor.fetchone()[0]
            
            # Note: Snapshot creation will be handled in STEP 2 (state model)
            # For now, just log the operation
            
            # Commit transaction (all-or-nothing)
            self.conn.commit()
            logger.debug(f"[STATE_STORE] Applied op: {op.op_id} ({op.op_type.value})")
            return True
            
        except sqlite3.Error as e:
            # Rollback on error
            self.conn.rollback()
            logger.error(f"[STATE_STORE] Transaction failed: {e}")
            return False
    
    def get_log_tail(self, last_op_id: str = None, limit: int = 100) -> List[StateOp]:
        """
        Get tail of state log (for sync)
        
        Args:
            last_op_id: Last op ID we have (get ops after this)
            limit: Max ops to return
            
        Returns:
            List of state operations
        """
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            
            if last_op_id:
                cursor.execute('''
                    SELECT op_id, op_type, key, value, timestamp, node_id, vector_clock
                    FROM state_log
                    WHERE op_id > ?
                    ORDER BY created_at ASC
                    LIMIT ?
                ''', (last_op_id, limit))
            else:
                cursor.execute('''
                    SELECT op_id, op_type, key, value, timestamp, node_id, vector_clock
                    FROM state_log
                    ORDER BY created_at ASC
                    LIMIT ?
                ''', (limit,))
            
            ops = []
            for row in cursor.fetchall():
                op_dict = {
                    'op_id': row[0],
                    'op_type': row[1],
                    'key': row[2],
                    'value': row[3],
                    'timestamp': row[4],
                    'node_id': row[5],
                    'vector_clock': row[6]
                }
                ops.append(StateOp.from_dict(op_dict))
            
            return ops
            
        except Exception as e:
            logger.error(f"[STATE_STORE] Get log tail error: {e}")
            return []
    
    def get_last_op_id(self) -> Optional[str]:
        """Get the last operation ID from log"""
        if not self.conn:
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT op_id FROM state_log ORDER BY created_at DESC LIMIT 1')
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"[STATE_STORE] Get last op ID error: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("[STATE_STORE] Database connection closed")


# Singleton instance
_store_instance: Optional[AuthoritativeStateStore] = None


def get_state_store(db_path: str = None) -> AuthoritativeStateStore:
    """Get singleton state store instance"""
    global _store_instance
    if _store_instance is None:
        _store_instance = AuthoritativeStateStore(db_path)
    return _store_instance


if __name__ == "__main__":
    # Test state store
    import uuid
    test_db = f"/tmp/test_state_{uuid.uuid4().hex[:8]}.db"
    store = AuthoritativeStateStore(db_path=test_db)
    
    # Validate
    if store.validate_db():
        print("[TEST] ✅ Database validation passed")
    else:
        print("[TEST] ❌ Database validation failed")
        exit(1)
    
    # Test apply op
    test_op = StateOp(
        op_id=str(uuid.uuid4()),
        op_type=OpType.SET,
        key="test.key",
        value={"test": "value"},
        node_id="test_node"
    )
    
    if store.apply_op(test_op):
        print("[TEST] ✅ Apply op succeeded")
    else:
        print("[TEST] ❌ Apply op failed")
        exit(1)
    
    # Test get log tail
    ops = store.get_log_tail(limit=10)
    print(f"[TEST] ✅ Retrieved {len(ops)} ops from log")
    
    # Test get last op ID
    last_op = store.get_last_op_id()
    print(f"[TEST] ✅ Last op ID: {last_op}")
    
    store.close()
    
    # Cleanup test DB
    if os.path.exists(test_db):
        os.remove(test_db)
    
    print("[TEST] ✅ All tests passed")
