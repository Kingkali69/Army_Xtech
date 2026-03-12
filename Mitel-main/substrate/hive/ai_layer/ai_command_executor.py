#!/usr/bin/env python3
"""
AI Command Executor - First-Class Citizen AI
=============================================

AI executes commands directly through the substrate.
Not a tool - a first-class citizen that can:
- Push commands through the substrate
- Receive responses back
- Execute operations across nodes
- Coordinate file operations

This is the "bank teller" - always available, no matter which OS.
"""

import sys
import os
import logging
import time
import uuid
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

# Add paths
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_1_state_store'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_2_state_model'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_4_sync_engine'))

try:
    from state_store import StateOp, OpType
    from state_model import StateModel
    SUBSTRATE_AVAILABLE = True
except ImportError:
    SUBSTRATE_AVAILABLE = False
    logging.warning("[AI_COMMAND_EXECUTOR] Substrate not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """Command execution status"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETE = "complete"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AICommand:
    """AI command to execute through substrate"""
    command_id: str
    command_type: str  # "file_pull", "file_push", "file_list", "file_delete", etc.
    target_node: Optional[str]  # None = local, or specific node ID
    parameters: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    status: CommandStatus = CommandStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


class AICommandExecutor:
    """
    AI Command Executor - First-Class Citizen
    
    AI executes commands directly through the substrate.
    Commands flow through the substrate and responses come back.
    """
    
    def __init__(self, node_id: str, state_model: StateModel = None):
        """
        Initialize AI command executor.
        
        Args:
            node_id: Node identifier
            state_model: State model for substrate operations
        """
        self.node_id = node_id
        self.state_model = state_model
        
        # Active commands
        self.active_commands: Dict[str, AICommand] = {}
        
        # Command handlers
        self.command_handlers: Dict[str, Callable] = {
            'file_pull': self._handle_file_pull,
            'file_push': self._handle_file_push,
            'file_list': self._handle_file_list,
            'file_delete': self._handle_file_delete,
            'file_exists': self._handle_file_exists,
            'file_info': self._handle_file_info,
        }
        
        # Response callbacks
        self.response_callbacks: Dict[str, Callable] = {}
        
        logger.info(f"[AI_COMMAND_EXECUTOR] Initialized for node {node_id[:12]}...")
        logger.info("[AI_COMMAND_EXECUTOR] AI is a FIRST-CLASS CITIZEN - can execute commands through substrate")
    
    def execute_command(self, command_type: str, target_node: Optional[str] = None,
                      parameters: Dict[str, Any] = None) -> str:
        """
        Execute AI command through substrate.
        
        Args:
            command_type: Type of command
            target_node: Target node (None = local)
            parameters: Command parameters
            
        Returns:
            Command ID
        """
        command_id = str(uuid.uuid4())
        
        command = AICommand(
            command_id=command_id,
            command_type=command_type,
            target_node=target_node,
            parameters=parameters or {}
        )
        
        self.active_commands[command_id] = command
        
        logger.info(f"[AI_COMMAND_EXECUTOR] Executing command: {command_type} (ID: {command_id[:12]}...)")
        
        # Push command through substrate
        if target_node and target_node != self.node_id:
            # Remote command - push through substrate
            self._push_command_through_substrate(command)
        else:
            # Local command - execute directly
            self._execute_local_command(command)
        
        return command_id
    
    def _push_command_through_substrate(self, command: AICommand):
        """
        Push command through substrate to target node.
        
        Args:
            command: Command to push
        """
        command.status = CommandStatus.EXECUTING
        
        # Create state operation for command
        op = StateOp(
            op_id=command.command_id,
            op_type=OpType.SET,
            key=f"ai.command.{command.target_node}.{command.command_id}",
            value=json.dumps({
                'command_type': command.command_type,
                'parameters': command.parameters,
                'source_node': self.node_id,
                'timestamp': command.timestamp
            }),
            timestamp=command.timestamp,
            node_id=self.node_id
        )
        
        # Apply to state model (will sync to target node)
        if self.state_model:
            self.state_model.apply_op(op)
            logger.info(f"[AI_COMMAND_EXECUTOR] Command pushed through substrate to {command.target_node[:12]}...")
        else:
            logger.warning("[AI_COMMAND_EXECUTOR] State model not available, cannot push command")
            command.status = CommandStatus.FAILED
            command.error = "State model not available"
    
    def _execute_local_command(self, command: AICommand):
        """
        Execute command locally.
        
        Args:
            command: Command to execute
        """
        command.status = CommandStatus.EXECUTING
        
        handler = self.command_handlers.get(command.command_type)
        if not handler:
            command.status = CommandStatus.FAILED
            command.error = f"Unknown command type: {command.command_type}"
            logger.error(f"[AI_COMMAND_EXECUTOR] Unknown command: {command.command_type}")
            return
        
        try:
            result = handler(command.parameters)
            command.status = CommandStatus.COMPLETE
            command.result = result
            logger.info(f"[AI_COMMAND_EXECUTOR] Command completed: {command.command_id[:12]}...")
        except Exception as e:
            command.status = CommandStatus.FAILED
            command.error = str(e)
            logger.error(f"[AI_COMMAND_EXECUTOR] Command failed: {e}")
    
    def _handle_file_pull(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file pull command"""
        file_path = params.get('file_path')
        target_path = params.get('target_path')
        
        if not file_path:
            raise ValueError("file_path required")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # If target_path specified, copy file
        if target_path:
            import shutil
            shutil.copy2(file_path, target_path)
            return {'status': 'copied', 'source': file_path, 'target': target_path}
        else:
            # Return file info
            stat = os.stat(file_path)
            return {
                'status': 'found',
                'file_path': file_path,
                'size': stat.st_size,
                'exists': True
            }
    
    def _handle_file_push(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file push command"""
        source_path = params.get('source_path')
        target_path = params.get('target_path')
        
        if not source_path or not target_path:
            raise ValueError("source_path and target_path required")
        
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Ensure target directory exists
        target_dir = os.path.dirname(target_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        
        import shutil
        shutil.copy2(source_path, target_path)
        
        return {'status': 'pushed', 'source': source_path, 'target': target_path}
    
    def _handle_file_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file list command"""
        directory = params.get('directory', '.')
        
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if not os.path.isdir(directory):
            raise ValueError(f"Not a directory: {directory}")
        
        files = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            stat = os.stat(item_path)
            files.append({
                'name': item,
                'path': item_path,
                'is_directory': os.path.isdir(item_path),
                'size': stat.st_size if os.path.isfile(item_path) else 0
            })
        
        return {'files': files, 'directory': directory}
    
    def _handle_file_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file delete command"""
        file_path = params.get('file_path')
        
        if not file_path:
            raise ValueError("file_path required")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if os.path.isdir(file_path):
            import shutil
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
        
        return {'status': 'deleted', 'file_path': file_path}
    
    def _handle_file_exists(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file exists check"""
        file_path = params.get('file_path')
        
        if not file_path:
            raise ValueError("file_path required")
        
        exists = os.path.exists(file_path)
        result = {'exists': exists, 'file_path': file_path}
        
        if exists:
            stat = os.stat(file_path)
            result['is_directory'] = os.path.isdir(file_path)
            result['size'] = stat.st_size if os.path.isfile(file_path) else 0
        
        return result
    
    def _handle_file_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file info command"""
        file_path = params.get('file_path')
        
        if not file_path:
            raise ValueError("file_path required")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = os.stat(file_path)
        return {
            'file_path': file_path,
            'size': stat.st_size,
            'is_directory': os.path.isdir(file_path),
            'modified': stat.st_mtime,
            'created': stat.st_ctime if hasattr(stat, 'st_ctime') else stat.st_mtime
        }
    
    def get_command_status(self, command_id: str) -> Optional[AICommand]:
        """
        Get command status.
        
        Args:
            command_id: Command ID
            
        Returns:
            Command object or None
        """
        return self.active_commands.get(command_id)
    
    def wait_for_command(self, command_id: str, timeout: float = 30.0) -> Optional[AICommand]:
        """
        Wait for command to complete.
        
        Args:
            command_id: Command ID
            timeout: Timeout in seconds
            
        Returns:
            Command object or None if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            command = self.active_commands.get(command_id)
            if command and command.status in [CommandStatus.COMPLETE, CommandStatus.FAILED]:
                return command
            time.sleep(0.1)
        
        # Timeout
        command = self.active_commands.get(command_id)
        if command:
            command.status = CommandStatus.TIMEOUT
        return command


# Export
__all__ = ['AICommandExecutor', 'AICommand', 'CommandStatus']
