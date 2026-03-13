#!/usr/bin/env python3
"""
STEP 5: Files as Payloads
=========================

Chunked transfer for large files.
Hash verification for integrity.
Resume support (don't restart).

Files are transferred as ops payloads.
"""

import sys
import os
import hashlib
import logging
import threading
import socket
import json
import uuid
import time
from typing import Dict, List, Optional, Tuple, BinaryIO, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransferStatus(Enum):
    """File transfer status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class FileChunk:
    """File chunk metadata"""
    chunk_id: int
    file_id: str
    offset: int
    size: int
    hash: str  # SHA256 of chunk data
    data: Optional[bytes] = None


@dataclass
class FileTransfer:
    """File transfer state"""
    file_id: str
    file_path: str
    file_size: int
    file_hash: str  # SHA256 of entire file
    total_chunks: int
    chunk_size: int
    chunks_received: Set[int] = field(default_factory=set)
    chunks_sent: Set[int] = field(default_factory=set)
    status: TransferStatus = TransferStatus.PENDING
    start_time: float = field(default_factory=time.time)
    bytes_transferred: int = 0


class FileTransferEngine:
    """
    File transfer engine.
    
    Features:
    - Chunked transfer (large files)
    - Hash verification (integrity)
    - Resume support (don't restart)
    - Progress tracking
    """
    
    CHUNK_SIZE = 64 * 1024  # 64KB chunks
    
    def __init__(self, data_dir: str = None):
        """
        Initialize file transfer engine.
        
        Args:
            data_dir: Directory for temporary file storage
        """
        if data_dir is None:
            data_dir = os.path.expanduser('~/.omni/files')
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Active transfers
        self.transfers: Dict[str, FileTransfer] = {}
        self.lock = threading.Lock()
        
        logger.info(f"[FILE_TRANSFER] Initialized - data dir: {self.data_dir}")
    
    def compute_file_hash(self, file_path: str) -> str:
        """
        Compute SHA256 hash of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash (hex)
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def compute_chunk_hash(self, data: bytes) -> str:
        """Compute SHA256 hash of chunk data"""
        return hashlib.sha256(data).hexdigest()
    
    def prepare_file_for_transfer(self, file_path: str) -> Dict[str, any]:
        """
        Prepare file for transfer.
        
        Creates file metadata and computes hash.
        
        Args:
            file_path: Path to file
            
        Returns:
            File metadata dict
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = file_path_obj.stat().st_size
        file_hash = self.compute_file_hash(file_path)
        total_chunks = (file_size + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE
        
        file_id = str(uuid.uuid4())
        
        metadata = {
            'file_id': file_id,
            'file_name': file_path_obj.name,
            'file_path': str(file_path),
            'file_size': file_size,
            'file_hash': file_hash,
            'total_chunks': total_chunks,
            'chunk_size': self.CHUNK_SIZE,
            'created_at': time.time()
        }
        
        # Create transfer state
        transfer = FileTransfer(
            file_id=file_id,
            file_path=str(file_path),
            file_size=file_size,
            file_hash=file_hash,
            total_chunks=total_chunks,
            chunk_size=self.CHUNK_SIZE,
            status=TransferStatus.PENDING
        )
        
        with self.lock:
            self.transfers[file_id] = transfer
        
        logger.info(f"[FILE_TRANSFER] Prepared file: {file_path_obj.name} ({file_size} bytes, {total_chunks} chunks)")
        return metadata
    
    def read_chunk(self, file_path: str, chunk_id: int, chunk_size: int = None) -> FileChunk:
        """
        Read a chunk from file.
        
        Args:
            file_path: Path to file
            chunk_id: Chunk ID (0-based)
            chunk_size: Chunk size (default: self.CHUNK_SIZE)
            
        Returns:
            FileChunk object
        """
        if chunk_size is None:
            chunk_size = self.CHUNK_SIZE
        
        file_id = str(uuid.uuid4())  # Temporary, would be tracked per file
        offset = chunk_id * chunk_size
        
        with open(file_path, 'rb') as f:
            f.seek(offset)
            data = f.read(chunk_size)
        
        chunk_hash = self.compute_chunk_hash(data)
        
        return FileChunk(
            chunk_id=chunk_id,
            file_id=file_id,
            offset=offset,
            size=len(data),
            hash=chunk_hash,
            data=data
        )
    
    def write_chunk(self, file_id: str, chunk: FileChunk, target_path: str = None) -> bool:
        """
        Write chunk to file.
        
        Args:
            file_id: File ID
            chunk: FileChunk object
            target_path: Target file path (default: data_dir/file_id)
            
        Returns:
            True if written successfully
        """
        if target_path is None:
            target_path = self.data_dir / file_id
        
        # Verify chunk hash
        if chunk.data:
            computed_hash = self.compute_chunk_hash(chunk.data)
            if computed_hash != chunk.hash:
                logger.error(f"[FILE_TRANSFER] Chunk hash mismatch: {chunk.chunk_id}")
                return False
        
        # Write chunk
        try:
            with open(target_path, 'r+b') as f:
                f.seek(chunk.offset)
                f.write(chunk.data)
            
            # Update transfer state
            with self.lock:
                if file_id in self.transfers:
                    transfer = self.transfers[file_id]
                    transfer.chunks_received.add(chunk.chunk_id)
                    transfer.bytes_transferred += chunk.size
                    
                    # Check if complete
                    if len(transfer.chunks_received) == transfer.total_chunks:
                        # Verify file hash
                        file_hash = self.compute_file_hash(str(target_path))
                        if file_hash == transfer.file_hash:
                            transfer.status = TransferStatus.COMPLETE
                            logger.info(f"[FILE_TRANSFER] File transfer complete: {file_id}")
                        else:
                            transfer.status = TransferStatus.FAILED
                            logger.error(f"[FILE_TRANSFER] File hash mismatch: {file_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"[FILE_TRANSFER] Failed to write chunk: {e}")
            return False
    
    def get_transfer_progress(self, file_id: str) -> Dict[str, any]:
        """
        Get transfer progress.
        
        Args:
            file_id: File ID
            
        Returns:
            Progress dict
        """
        with self.lock:
            transfer = self.transfers.get(file_id)
            if not transfer:
                return {'error': 'Transfer not found'}
            
            progress_percent = 0.0
            if transfer.total_chunks > 0:
                progress_percent = (len(transfer.chunks_received) / transfer.total_chunks) * 100
            
            return {
                'file_id': file_id,
                'status': transfer.status.value,
                'progress_percent': progress_percent,
                'chunks_received': len(transfer.chunks_received),
                'total_chunks': transfer.total_chunks,
                'bytes_transferred': transfer.bytes_transferred,
                'file_size': transfer.file_size,
                'elapsed_time': time.time() - transfer.start_time
            }
    
    def resume_transfer(self, file_id: str) -> List[int]:
        """
        Get list of chunks that need to be transferred (resume).
        
        Args:
            file_id: File ID
            
        Returns:
            List of chunk IDs that need transfer
        """
        with self.lock:
            transfer = self.transfers.get(file_id)
            if not transfer:
                return []
            
            all_chunks = set(range(transfer.total_chunks))
            missing_chunks = all_chunks - transfer.chunks_received
            return sorted(list(missing_chunks))


def test_file_transfer():
    """Test file transfer"""
    import tempfile
    
    # Create test file
    test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
    test_data = b'Test file content ' * 1000  # ~18KB
    test_file.write(test_data)
    test_file.close()
    
    engine = FileTransferEngine()
    
    # Prepare file
    metadata = engine.prepare_file_for_transfer(test_file.name)
    print(f"✓ Prepared file: {metadata['file_name']}")
    print(f"  File ID: {metadata['file_id']}")
    print(f"  Size: {metadata['file_size']} bytes")
    print(f"  Chunks: {metadata['total_chunks']}")
    print(f"  Hash: {metadata['file_hash'][:16]}...")
    
    # Read chunks
    chunk = engine.read_chunk(test_file.name, 0)
    print(f"✓ Read chunk 0: {chunk.size} bytes, hash: {chunk.hash[:16]}...")
    
    # Cleanup
    os.unlink(test_file.name)
    print("✓ File transfer tests passed")


if __name__ == "__main__":
    test_file_transfer()
