#!/usr/bin/env python3
"""
NEXUS File Executor - Bank Teller Model
========================================

NEXUS executes file transfers autonomously through the substrate.
3-lane bank teller model with tube system for file passing.

Execution-first layer (not chat).
AI as first-class citizen doing actual work.
"""

import sys
import os
import logging
import time
import uuid
import json
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Add paths
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_5_files_as_payloads'))

try:
    from ai_command_executor import AICommandExecutor, AICommand, CommandStatus
    from file_transfer import FileTransferEngine, TransferStatus
    from nexus_file_transfer import NexusFileTransfer
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    logging.warning(f"[NEXUS_FILE_EXECUTOR] Components not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransferLane(Enum):
    """Bank teller lanes"""
    LANE_1 = "lane_1"  # Direct (walk-up)
    LANE_2 = "lane_2"  # Tube system (fast)
    LANE_3 = "lane_3"  # Tube system (priority)


@dataclass
class FileTransferRequest:
    """File transfer request"""
    request_id: str
    operation: str  # "push", "pull", "copy", "move"
    source_path: str
    target_node: Optional[str]
    target_path: Optional[str]
    lane: TransferLane
    priority: int  # 1-10, 10 = highest
    timestamp: float


class NexusFileExecutor:
    """
    NEXUS File Executor - Bank Teller Model
    
    3 lanes:
    - Lane 1: Direct transfer (walk-up window)
    - Lane 2: Tube system (fast, chunked)
    - Lane 3: Tube system (priority, critical files)
    
    NEXUS decides which lane to use based on:
    - File size
    - Urgency
    - Network conditions
    - Target node availability
    """
    
    def __init__(self, node_id: str, data_dir: str = None):
        """
        Initialize NEXUS file executor.
        
        Args:
            node_id: Node identifier
            data_dir: Directory for file operations
        """
        self.node_id = node_id
        
        if data_dir is None:
            data_dir = os.path.expanduser('~/.omni/files')
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        if COMPONENTS_AVAILABLE:
            self.command_executor = AICommandExecutor(node_id=node_id)
            self.file_transfer_engine = FileTransferEngine(data_dir=str(self.data_dir))
            self.nexus_ft = NexusFileTransfer(node_id=node_id)
        else:
            self.command_executor = None
            self.file_transfer_engine = None
            self.nexus_ft = None
        
        # Active transfers
        self.active_transfers: Dict[str, FileTransferRequest] = {}
        
        logger.info(f"[NEXUS_FILE_EXECUTOR] Initialized for node {node_id[:12]}...")
        logger.info("[NEXUS_FILE_EXECUTOR] Bank teller model active - 3 lanes ready")
    
    def push_file(self, source_path: str, target_node: str, target_path: str = None,
                  priority: int = 5) -> Optional[str]:
        """
        Push file to target node (EXECUTION).
        
        Args:
            source_path: Local file path
            target_node: Target node ID
            target_path: Target path on remote node (None = same path)
            priority: Transfer priority (1-10)
            
        Returns:
            Transfer request ID if successful
        """
        if not os.path.exists(source_path):
            logger.error(f"[NEXUS_FILE_EXECUTOR] File not found: {source_path}")
            return None
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Determine lane based on file size and priority
        file_size = os.path.getsize(source_path)
        lane = self._select_lane(file_size, priority)
        
        # Create transfer request
        request = FileTransferRequest(
            request_id=request_id,
            operation="push",
            source_path=source_path,
            target_node=target_node,
            target_path=target_path or source_path,
            lane=lane,
            priority=priority,
            timestamp=time.time()
        )
        
        # Store request
        self.active_transfers[request_id] = request
        
        # Execute transfer based on lane
        if lane == TransferLane.LANE_1:
            # Direct transfer (small files)
            success = self._execute_direct_transfer(request)
        else:
            # Tube system (chunked transfer)
            success = self._execute_tube_transfer(request)
        
        if success:
            logger.info(f"[NEXUS_FILE_EXECUTOR] File push initiated: {source_path} -> {target_node} (lane: {lane.value})")
            return request_id
        else:
            logger.error(f"[NEXUS_FILE_EXECUTOR] File push failed: {source_path}")
            del self.active_transfers[request_id]
            return None
    
    def pull_file(self, source_node: str, source_path: str, target_path: str = None,
                  priority: int = 5) -> Optional[str]:
        """
        Pull file from source node (EXECUTION).
        
        Args:
            source_node: Source node ID
            source_path: Remote file path
            target_path: Local target path (None = same path)
            priority: Transfer priority (1-10)
            
        Returns:
            Transfer request ID if successful
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Determine lane (assume medium file for now)
        lane = TransferLane.LANE_2
        
        # Create transfer request
        request = FileTransferRequest(
            request_id=request_id,
            operation="pull",
            source_path=source_path,
            target_node=source_node,
            target_path=target_path or source_path,
            lane=lane,
            priority=priority,
            timestamp=time.time()
        )
        
        # Store request
        self.active_transfers[request_id] = request
        
        # Execute pull via command executor
        if self.command_executor:
            command = AICommand(
                command_id=request_id,
                command_type='file_pull',
                target_node=source_node,
                parameters={
                    'source_path': source_path,
                    'target_path': target_path or source_path
                }
            )
            
            success = self.command_executor.execute_command(command)
            
            if success:
                logger.info(f"[NEXUS_FILE_EXECUTOR] File pull initiated: {source_node}:{source_path} (lane: {lane.value})")
                return request_id
            else:
                logger.error(f"[NEXUS_FILE_EXECUTOR] File pull failed")
                del self.active_transfers[request_id]
                return None
        else:
            logger.error("[NEXUS_FILE_EXECUTOR] Command executor not available")
            return None
    
    def copy_file(self, source_path: str, target_path: str) -> bool:
        """
        Copy file locally (EXECUTION).
        
        Args:
            source_path: Source file path
            target_path: Target file path
            
        Returns:
            True if successful
        """
        try:
            if not os.path.exists(source_path):
                logger.error(f"[NEXUS_FILE_EXECUTOR] Source file not found: {source_path}")
                return False
            
            # Create target directory if needed
            target_dir = os.path.dirname(target_path)
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, target_path)
            
            logger.info(f"[NEXUS_FILE_EXECUTOR] File copied: {source_path} -> {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"[NEXUS_FILE_EXECUTOR] Copy failed: {e}")
            return False
    
    def move_file(self, source_path: str, target_path: str) -> bool:
        """
        Move file locally (EXECUTION).
        
        Args:
            source_path: Source file path
            target_path: Target file path
            
        Returns:
            True if successful
        """
        try:
            if not os.path.exists(source_path):
                logger.error(f"[NEXUS_FILE_EXECUTOR] Source file not found: {source_path}")
                return False
            
            # Create target directory if needed
            target_dir = os.path.dirname(target_path)
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)
            
            # Move file
            shutil.move(source_path, target_path)
            
            logger.info(f"[NEXUS_FILE_EXECUTOR] File moved: {source_path} -> {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"[NEXUS_FILE_EXECUTOR] Move failed: {e}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file (EXECUTION).
        
        Args:
            file_path: File path to delete
            
        Returns:
            True if successful
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"[NEXUS_FILE_EXECUTOR] File not found: {file_path}")
                return False
            
            os.remove(file_path)
            
            logger.info(f"[NEXUS_FILE_EXECUTOR] File deleted: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"[NEXUS_FILE_EXECUTOR] Delete failed: {e}")
            return False
    
    def list_files(self, directory: str = None) -> List[str]:
        """
        List files in directory (EXECUTION).
        
        Args:
            directory: Directory path (None = data dir)
            
        Returns:
            List of file paths
        """
        try:
            if directory is None:
                directory = str(self.data_dir)
            
            if not os.path.exists(directory):
                logger.error(f"[NEXUS_FILE_EXECUTOR] Directory not found: {directory}")
                return []
            
            files = []
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
            
            logger.info(f"[NEXUS_FILE_EXECUTOR] Listed {len(files)} files in {directory}")
            return files
            
        except Exception as e:
            logger.error(f"[NEXUS_FILE_EXECUTOR] List failed: {e}")
            return []
    
    def get_transfer_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get transfer status"""
        request = self.active_transfers.get(request_id)
        if not request:
            return None
        
        return {
            'request_id': request_id,
            'operation': request.operation,
            'source_path': request.source_path,
            'target_node': request.target_node,
            'lane': request.lane.value,
            'priority': request.priority,
            'timestamp': request.timestamp
        }
    
    def _select_lane(self, file_size: int, priority: int) -> TransferLane:
        """Select transfer lane based on file size and priority"""
        # Priority lane for critical files
        if priority >= 8:
            return TransferLane.LANE_3
        
        # Direct lane for small files (< 1MB)
        if file_size < 1024 * 1024:
            return TransferLane.LANE_1
        
        # Tube system for larger files
        return TransferLane.LANE_2
    
    def _execute_direct_transfer(self, request: FileTransferRequest) -> bool:
        """Execute direct transfer (Lane 1)"""
        try:
            # Read file
            with open(request.source_path, 'rb') as f:
                file_data = f.read()
            
            # Send via command executor
            if self.command_executor:
                command = AICommand(
                    command_id=request.request_id,
                    command_type='file_push',
                    target_node=request.target_node,
                    parameters={
                        'target_path': request.target_path,
                        'file_data': file_data.hex(),  # Hex encode for JSON
                        'transfer_mode': 'direct'
                    }
                )
                
                return self.command_executor.execute_command(command)
            else:
                logger.error("[NEXUS_FILE_EXECUTOR] Command executor not available")
                return False
                
        except Exception as e:
            logger.error(f"[NEXUS_FILE_EXECUTOR] Direct transfer failed: {e}")
            return False
    
    def _execute_tube_transfer(self, request: FileTransferRequest) -> bool:
        """Execute tube transfer (Lane 2/3 - chunked)"""
        try:
            if not self.file_transfer_engine:
                logger.error("[NEXUS_FILE_EXECUTOR] File transfer engine not available")
                return False
            
            # Initiate chunked transfer
            file_id = self.file_transfer_engine.initiate_transfer(
                request.source_path,
                [request.target_node]
            )
            
            if file_id:
                logger.info(f"[NEXUS_FILE_EXECUTOR] Tube transfer initiated: {file_id}")
                return True
            else:
                logger.error("[NEXUS_FILE_EXECUTOR] Tube transfer failed to initiate")
                return False
                
        except Exception as e:
            logger.error(f"[NEXUS_FILE_EXECUTOR] Tube transfer failed: {e}")
            return False
