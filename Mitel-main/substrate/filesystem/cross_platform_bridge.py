#!/usr/bin/env python3
"""
Cross-Platform File System Bridge
==================================

Seamless file access across operating systems:
- Linux Thunar integration
- Windows Explorer integration
- macOS Finder integration
- AI as "bank teller" - always available

No matter which OS you're on, you can access files from any OS.
AI handles the routing, transfer, and coordination.
"""

import sys
import os
import logging
import platform
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add paths
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_5_files_as_payloads'))

try:
    from ai_command_executor import AICommandExecutor
    from ai_integration import AIEnhancedFileTransferEngine
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    logging.warning(f"[CROSS_PLATFORM_BRIDGE] AI components not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CrossPlatformBridge:
    """
    Cross-platform file system bridge.
    
    Provides seamless file access across OS boundaries.
    AI acts as "bank teller" - always available to pull/push files.
    """
    
    def __init__(self, node_id: str, state_model=None):
        """
        Initialize cross-platform bridge.
        
        Args:
            node_id: Node identifier
            state_model: State model for substrate operations
        """
        self.node_id = node_id
        self.current_platform = platform.system().lower()
        
        # Initialize AI components
        self.ai_executor = None
        self.ai_file_transfer = None
        
        if AI_AVAILABLE:
            try:
                self.ai_executor = AICommandExecutor(node_id=node_id, state_model=state_model)
                self.ai_file_transfer = AIEnhancedFileTransferEngine(node_id=node_id)
                logger.info("[CROSS_PLATFORM_BRIDGE] AI components initialized")
            except Exception as e:
                logger.warning(f"[CROSS_PLATFORM_BRIDGE] Failed to initialize AI: {e}")
        
        # Platform-specific paths
        self.platform_paths = {
            'linux': {
                'home': os.path.expanduser('~'),
                'desktop': os.path.join(os.path.expanduser('~'), 'Desktop'),
                'documents': os.path.join(os.path.expanduser('~'), 'Documents'),
            },
            'windows': {
                'home': os.path.expanduser('~'),
                'desktop': os.path.join(os.path.expanduser('~'), 'Desktop'),
                'documents': os.path.join(os.path.expanduser('~'), 'Documents'),
            },
            'darwin': {  # macOS
                'home': os.path.expanduser('~'),
                'desktop': os.path.join(os.path.expanduser('~'), 'Desktop'),
                'documents': os.path.join(os.path.expanduser('~'), 'Documents'),
            }
        }
        
        logger.info(f"[CROSS_PLATFORM_BRIDGE] Initialized for {self.current_platform}")
        logger.info("[CROSS_PLATFORM_BRIDGE] AI is the 'bank teller' - always available")
    
    def get_file(self, remote_path: str, local_path: str = None, 
                 target_node: str = None) -> Dict[str, Any]:
        """
        Get file from remote node (AI handles routing).
        
        Args:
            remote_path: Path on remote node
            local_path: Local destination path (None = same name in current dir)
            target_node: Target node ID (None = discover)
            
        Returns:
            Result dict with status
        """
        if not self.ai_executor:
            return {'error': 'AI executor not available'}
        
        logger.info(f"[CROSS_PLATFORM_BRIDGE] Getting file: {remote_path} from {target_node or 'auto'}...")
        
        # AI executes command through substrate
        command_id = self.ai_executor.execute_command(
            command_type='file_pull',
            target_node=target_node,
            parameters={
                'file_path': remote_path,
                'target_path': local_path
            }
        )
        
        # Wait for command
        command = self.ai_executor.wait_for_command(command_id, timeout=60.0)
        
        if command and command.status.value == 'complete':
            return {
                'success': True,
                'command_id': command_id,
                'result': command.result
            }
        else:
            error = command.error if command else "Command timeout"
            return {
                'success': False,
                'error': error,
                'command_id': command_id
            }
    
    def put_file(self, local_path: str, remote_path: str,
                 target_node: str = None) -> Dict[str, Any]:
        """
        Put file to remote node (AI handles routing).
        
        Args:
            local_path: Local source path
            remote_path: Path on remote node
            target_node: Target node ID (None = discover)
            
        Returns:
            Result dict with status
        """
        if not self.ai_executor:
            return {'error': 'AI executor not available'}
        
        logger.info(f"[CROSS_PLATFORM_BRIDGE] Putting file: {local_path} to {remote_path} on {target_node or 'auto'}...")
        
        # AI executes command through substrate
        command_id = self.ai_executor.execute_command(
            command_type='file_push',
            target_node=target_node,
            parameters={
                'source_path': local_path,
                'target_path': remote_path
            }
        )
        
        # Wait for command
        command = self.ai_executor.wait_for_command(command_id, timeout=60.0)
        
        if command and command.status.value == 'complete':
            return {
                'success': True,
                'command_id': command_id,
                'result': command.result
            }
        else:
            error = command.error if command else "Command timeout"
            return {
                'success': False,
                'error': error,
                'command_id': command_id
            }
    
    def list_files(self, directory: str, target_node: str = None) -> Dict[str, Any]:
        """
        List files on remote node (AI handles routing).
        
        Args:
            directory: Directory path
            target_node: Target node ID (None = local)
            
        Returns:
            Result dict with file list
        """
        if not self.ai_executor:
            return {'error': 'AI executor not available'}
        
        # AI executes command through substrate
        command_id = self.ai_executor.execute_command(
            command_type='file_list',
            target_node=target_node,
            parameters={
                'directory': directory
            }
        )
        
        # Wait for command
        command = self.ai_executor.wait_for_command(command_id, timeout=30.0)
        
        if command and command.status.value == 'complete':
            return {
                'success': True,
                'command_id': command_id,
                'result': command.result
            }
        else:
            error = command.error if command else "Command timeout"
            return {
                'success': False,
                'error': error,
                'command_id': command_id
            }
    
    def file_exists(self, file_path: str, target_node: str = None) -> bool:
        """
        Check if file exists on remote node.
        
        Args:
            file_path: File path
            target_node: Target node ID (None = local)
            
        Returns:
            True if exists
        """
        if not self.ai_executor:
            return False
        
        command_id = self.ai_executor.execute_command(
            command_type='file_exists',
            target_node=target_node,
            parameters={
                'file_path': file_path
            }
        )
        
        command = self.ai_executor.wait_for_command(command_id, timeout=10.0)
        
        if command and command.status.value == 'complete':
            return command.result.get('exists', False)
        return False
    
    def normalize_path(self, path: str, target_platform: str = None) -> str:
        """
        Normalize path for target platform.
        
        Args:
            path: Path to normalize
            target_platform: Target platform (None = current)
            
        Returns:
            Normalized path
        """
        if target_platform is None:
            target_platform = self.current_platform
        
        # Handle platform-specific path separators
        if target_platform == 'windows':
            return path.replace('/', '\\')
        else:
            return path.replace('\\', '/')


# Platform-specific integrations

class ThunarIntegration:
    """Linux Thunar file manager integration"""
    
    @staticmethod
    def register_protocol():
        """Register custom protocol handler for Thunar"""
        # This would register a custom protocol like "omni://" for Thunar
        pass


class WindowsExplorerIntegration:
    """Windows Explorer integration"""
    
    @staticmethod
    def register_protocol():
        """Register custom protocol handler for Explorer"""
        pass


class MacOSFinderIntegration:
    """macOS Finder integration"""
    
    @staticmethod
    def register_protocol():
        """Register custom protocol handler for Finder"""
        pass


# Export
__all__ = ['CrossPlatformBridge', 'ThunarIntegration', 'WindowsExplorerIntegration', 'MacOSFinderIntegration']
