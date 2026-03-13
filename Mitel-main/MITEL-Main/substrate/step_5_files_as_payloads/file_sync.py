#!/usr/bin/env python3
"""
STEP 5: File Sync Integration
============================

Integrates file transfer with sync engine.
Files are transferred as ops payloads.
"""

import sys
import os
import logging
import json
import uuid
from typing import Dict, List, Optional

# Add paths
base_dir = os.path.dirname(__file__)
substrate_dir = os.path.join(base_dir, '..')
sys.path.insert(0, os.path.join(substrate_dir, 'step_1_state_store'))
sys.path.insert(0, os.path.join(substrate_dir, 'step_4_sync_engine'))

from file_transfer import FileTransferEngine, FileChunk, TransferStatus

# Import StateOp with fallback
try:
    from step_1_state_store.state_store import StateOp, OpType
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "state_store",
        os.path.join(substrate_dir, 'step_1_state_store', 'state_store.py')
    )
    state_store_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(state_store_mod)
    StateOp = state_store_mod.StateOp
    OpType = state_store_mod.OpType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileSync:
    """
    File sync integration.
    
    Files are synced as ops with file metadata and chunks as payloads.
    """
    
    def __init__(self, file_transfer_engine: FileTransferEngine, state_model=None):
        """
        Initialize file sync.
        
        Args:
            file_transfer_engine: File transfer engine instance
            state_model: State model instance (for applying ops)
        """
        self.transfer_engine = file_transfer_engine
        self.state_model = state_model
        
        logger.info("[FILE_SYNC] Initialized")
    
    def create_file_op(self, file_path: str, target_key: str = None) -> StateOp:
        """
        Create file transfer op.
        
        Args:
            file_path: Path to file
            target_key: State key for file metadata (default: files.{file_id})
            
        Returns:
            StateOp with file metadata
        """
        # Prepare file
        metadata = self.transfer_engine.prepare_file_for_transfer(file_path)
        
        if target_key is None:
            target_key = f"files.{metadata['file_id']}"
        
        # Create op with file metadata
        op = StateOp(
            op_id=str(uuid.uuid4()),
            op_type=OpType.SET,
            key=target_key,
            value=metadata,
            node_id=self.transfer_engine.transfers[metadata['file_id']].file_id  # Would use actual node_id
        )
        
        logger.info(f"[FILE_SYNC] Created file op: {metadata['file_name']} ({metadata['file_size']} bytes)")
        return op
    
    def create_chunk_op(self, file_id: str, chunk_id: int, file_path: str) -> StateOp:
        """
        Create chunk transfer op.
        
        Args:
            file_id: File ID
            chunk_id: Chunk ID
            file_path: Path to source file
            
        Returns:
            StateOp with chunk data
        """
        # Read chunk
        chunk = self.transfer_engine.read_chunk(file_path, chunk_id)
        
        # Create op with chunk data
        chunk_data = {
            'chunk_id': chunk.chunk_id,
            'file_id': chunk.file_id,
            'offset': chunk.offset,
            'size': chunk.size,
            'hash': chunk.hash,
            'data': chunk.data.hex() if chunk.data else None  # Hex encode for JSON
        }
        
        op = StateOp(
            op_id=str(uuid.uuid4()),
            op_type=OpType.SET,
            key=f"files.{file_id}.chunks.{chunk_id}",
            value=chunk_data,
            node_id=self.transfer_engine.transfers[file_id].file_id  # Would use actual node_id
        )
        
        return op
    
    def apply_file_op(self, op: StateOp) -> bool:
        """
        Apply file metadata op.
        
        Args:
            op: StateOp with file metadata
            
        Returns:
            True if applied
        """
        if self.state_model:
            return self.state_model.apply_op(op)
        return False
    
    def apply_chunk_op(self, op: StateOp) -> bool:
        """
        Apply chunk op and write to file.
        
        Args:
            op: StateOp with chunk data
            
        Returns:
            True if applied
        """
        try:
            chunk_data = op.value
            
            # Decode hex data
            if chunk_data.get('data'):
                chunk_data['data'] = bytes.fromhex(chunk_data['data'])
            
            # Create chunk object
            chunk = FileChunk(
                chunk_id=chunk_data['chunk_id'],
                file_id=chunk_data['file_id'],
                offset=chunk_data['offset'],
                size=chunk_data['size'],
                hash=chunk_data['hash'],
                data=chunk_data.get('data')
            )
            
            # Write chunk
            file_id = chunk_data['file_id']
            success = self.transfer_engine.write_chunk(file_id, chunk)
            
            if success and self.state_model:
                # Apply op to state
                self.state_model.apply_op(op)
            
            return success
            
        except Exception as e:
            logger.error(f"[FILE_SYNC] Failed to apply chunk op: {e}")
            return False
    
    def transfer_file(self, file_path: str, target_key: str = None) -> str:
        """
        Transfer file (create ops for all chunks).
        
        Args:
            file_path: Path to file
            target_key: State key for file metadata
            
        Returns:
            File ID
        """
        # Create file metadata op
        file_op = self.create_file_op(file_path, target_key)
        file_id = file_op.value['file_id']
        
        # Apply file op
        self.apply_file_op(file_op)
        
        # Create chunk ops
        metadata = file_op.value
        total_chunks = metadata['total_chunks']
        
        for chunk_id in range(total_chunks):
            chunk_op = self.create_chunk_op(file_id, chunk_id, file_path)
            self.apply_file_op(chunk_op)  # Store chunk op in state
        
        logger.info(f"[FILE_SYNC] File transfer initiated: {file_id} ({total_chunks} chunks)")
        return file_id


def test_file_sync():
    """Test file sync"""
    import tempfile
    
    # Create test file
    test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
    test_data = b'Test file content ' * 100
    test_file.write(test_data)
    test_file.close()
    
    engine = FileTransferEngine()
    sync = FileSync(engine)
    
    # Transfer file
    file_id = sync.transfer_file(test_file.name)
    print(f"✓ File sync test passed: {file_id}")
    
    # Cleanup
    os.unlink(test_file.name)
    print("✓ File sync tests passed")


if __name__ == "__main__":
    test_file_sync()
