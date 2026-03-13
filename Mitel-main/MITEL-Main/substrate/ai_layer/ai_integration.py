#!/usr/bin/env python3
"""
AI Integration Layer
====================

Integrates AI as first-class citizen into foundation components:
- FileTransferEngine + FileTransferAI
- SyncEngine + SyncAI (future)
- RecoveryEngine + HealthAI (future)
- AdapterBridge + AdapterAI (future)
"""

import sys
import os
import logging
from typing import Dict, List, Optional, Any

# Add paths
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_5_files_as_payloads'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))

try:
    from file_transfer import FileTransferEngine, FileTransfer, TransferStatus
    from file_transfer_ai import FileTransferAI, TransferDecision, NetworkCondition
    from nexus_file_transfer import NexusFileTransfer
    AI_INTEGRATION_AVAILABLE = True
    NEXUS_FT_AVAILABLE = True
except ImportError as e:
    AI_INTEGRATION_AVAILABLE = False
    NEXUS_FT_AVAILABLE = False
    logging.warning(f"[AI_INTEGRATION] AI components not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NexusEnhancedFileTransferEngine:
    """
    NEXUS-enhanced file transfer engine.
    
    NEXUS (first-class citizen AI) controls file transfers intelligently.
    """
    
    def __init__(self, node_id: str, data_dir: str = None, nexus_llm=None):
        """
        Initialize NEXUS-enhanced file transfer engine.
        
        Args:
            node_id: Node identifier
            data_dir: Directory for file storage
            nexus_llm: NEXUS LLM instance (creates new if None)
        """
        self.node_id = node_id
        
        # Initialize base engine
        self.engine = FileTransferEngine(data_dir=data_dir)
        
        # Initialize NEXUS file transfer controller
        if NEXUS_FT_AVAILABLE:
            try:
                self.nexus_ft = NexusFileTransfer(node_id=node_id, nexus_llm=nexus_llm)
                logger.info("[NEXUS_ENHANCED_FT] NEXUS file transfer controller initialized")
            except Exception as e:
                logger.warning(f"[NEXUS_ENHANCED_FT] NEXUS not available, using basic AI: {e}")
                self.nexus_ft = None
                # Fallback to basic AI
                self.ai = FileTransferAI(node_id=node_id)
        else:
            self.nexus_ft = None
            self.ai = FileTransferAI(node_id=node_id)
        
        logger.info(f"[NEXUS_ENHANCED_FT] Initialized for node {node_id[:12]}...")
        logger.info("[NEXUS_ENHANCED_FT] NEXUS is controlling file transfers - first-class citizen active")
    
    def initiate_transfer(self, file_path: str, target_peers: List[str],
                         context: Dict[str, Any] = None) -> Optional[str]:
        """
        Initiate NEXUS-controlled file transfer.
        
        Args:
            file_path: Path to file
            target_peers: List of available peer IDs
            context: Additional context (urgency, system_file, etc.)
            
        Returns:
            File ID if initiated successfully
        """
        if not os.path.exists(file_path):
            logger.error(f"[NEXUS_ENHANCED_FT] File not found: {file_path}")
            return None
        
        file_size = os.path.getsize(file_path)
        
        # Get network conditions
        network_conditions = {}
        if self.nexus_ft:
            for peer_id in target_peers:
                condition = self.nexus_ft.file_transfer_ai.get_network_condition(peer_id)
                if condition:
                    network_conditions[peer_id] = condition
        
        # NEXUS makes transfer decision
        if self.nexus_ft:
            decision = self.nexus_ft.make_transfer_decision(
                file_path=file_path,
                file_size=file_size,
                available_peers=target_peers,
                network_conditions=network_conditions,
                context=context or {}
            )
        else:
            # Fallback to basic AI
            decision = self.ai.make_transfer_decision(
                file_path, file_size, target_peers, context or {}
            )
        
        logger.info(f"[NEXUS_ENHANCED_FT] NEXUS Decision: {decision.reasoning}")
        
        # Use NEXUS-selected peer
        selected_peer = decision.optimal_path
        if selected_peer and selected_peer not in target_peers:
            selected_peer = target_peers[0] if target_peers else None
        
        # Override chunk size with NEXUS-optimized size
        original_chunk_size = self.engine.CHUNK_SIZE
        self.engine.CHUNK_SIZE = decision.optimal_chunk_size
        
        try:
            # Initiate transfer using base engine
            file_id = self.engine.initiate_transfer(file_path, selected_peer)
            
            if file_id:
                logger.info(f"[NEXUS_ENHANCED_FT] Transfer initiated: {file_id}")
                logger.info(f"[NEXUS_ENHANCED_FT] NEXUS Priority: {decision.priority.name}, "
                          f"Chunk: {decision.optimal_chunk_size // 1024}KB, "
                          f"Peer: {selected_peer[:12] if selected_peer else 'none'}...")
            
            return file_id
            
        finally:
            # Restore original chunk size
            self.engine.CHUNK_SIZE = original_chunk_size
    
    def update_network_metrics(self, peer_id: str, bandwidth_mbps: float,
                               latency_ms: float, packet_loss: float = 0.0,
                               jitter_ms: float = 0.0):
        """Update network metrics for NEXUS learning"""
        if self.nexus_ft:
            condition = NetworkCondition(
                bandwidth_mbps=bandwidth_mbps,
                latency_ms=latency_ms,
                packet_loss=packet_loss,
                jitter_ms=jitter_ms
            )
            self.nexus_ft.update_network_metrics(peer_id, condition)
        elif self.ai:
            self.ai.update_network_condition(peer_id, condition)
    
    def handle_transfer_completion(self, file_id: str, success: bool,
                                  transfer_time: float, peer_id: str):
        """Handle transfer completion and feed to NEXUS learning"""
        transfer = self.engine.transfers.get(file_id)
        if transfer and self.nexus_ft:
            decision = self.nexus_ft.make_transfer_decision(
                file_path=transfer.file_path,
                file_size=transfer.file_size,
                available_peers=[peer_id] if peer_id else [],
                context={}
            )
            
            self.nexus_ft.record_transfer_result(
                file_path=transfer.file_path,
                success=success,
                transfer_time=transfer_time,
                bytes_transferred=transfer.bytes_transferred,
                peer_id=peer_id or "unknown",
                decision=decision
            )
    
    # Delegate other methods to base engine
    def compute_file_hash(self, file_path: str) -> str:
        return self.engine.compute_file_hash(file_path)
    
    def read_chunk(self, file_path: str, chunk_id: int) -> Optional[Any]:
        return self.engine.read_chunk(file_path, chunk_id)
    
    def write_chunk(self, file_id: str, chunk: Any, target_path: str = None) -> bool:
        return self.engine.write_chunk(file_id, chunk, target_path)
    
    def resume_transfer(self, file_id: str) -> List[int]:
        return self.engine.resume_transfer(file_id)
    
    def get_transfer_progress(self, file_id: str) -> Dict[str, Any]:
        return self.engine.get_transfer_progress(file_id)


# Keep old class for backward compatibility
class AIEnhancedFileTransferEngine(NexusEnhancedFileTransferEngine):
    """Backward compatibility alias"""
    pass

    """
    AI-enhanced file transfer engine.
    
    Wraps FileTransferEngine with AI intelligence:
    - AI determines priority
    - AI optimizes chunk size
    - AI selects optimal path
    - AI predicts retry success
    """
    
    def __init__(self, node_id: str, data_dir: str = None):
        """
        Initialize AI-enhanced file transfer engine.
        
        Args:
            node_id: Node identifier
            data_dir: Directory for file storage
        """
        self.node_id = node_id
        
        # Initialize base engine
        self.engine = FileTransferEngine(data_dir=data_dir)
        
        # Initialize AI layer
        self.ai = FileTransferAI(node_id=node_id)
        
        logger.info(f"[AI_ENHANCED_FT] Initialized for node {node_id[:12]}...")
    
    def initiate_transfer(self, file_path: str, target_peers: List[str],
                         context: Dict[str, Any] = None) -> Optional[str]:
        """
        Initiate AI-enhanced file transfer.
        
        Args:
            file_path: Path to file
            target_peers: List of available peer IDs
            context: Additional context (urgency, system_file, etc.)
            
        Returns:
            File ID if initiated successfully
        """
        if not os.path.exists(file_path):
            logger.error(f"[AI_ENHANCED_FT] File not found: {file_path}")
            return None
        
        file_size = os.path.getsize(file_path)
        
        # AI makes transfer decision
        decision = self.ai.make_transfer_decision(
            file_path=file_path,
            file_size=file_size,
            available_peers=target_peers,
            context=context or {}
        )
        
        logger.info(f"[AI_ENHANCED_FT] AI Decision: {decision.reasoning}")
        
        # Use AI-selected peer if available
        selected_peer = decision.optimal_path
        if selected_peer and selected_peer not in target_peers:
            selected_peer = target_peers[0] if target_peers else None
        
        # Override chunk size with AI-optimized size
        original_chunk_size = self.engine.CHUNK_SIZE
        self.engine.CHUNK_SIZE = decision.optimal_chunk_size
        
        try:
            # Initiate transfer using base engine
            file_id = self.engine.initiate_transfer(file_path, selected_peer)
            
            if file_id:
                # Store AI decision with transfer
                transfer = self.engine.transfers.get(file_id)
                if transfer:
                    # Store AI metadata (we'll extend FileTransfer later)
                    logger.info(f"[AI_ENHANCED_FT] Transfer initiated: {file_id}")
                    logger.info(f"[AI_ENHANCED_FT] Priority: {decision.priority.name}, "
                              f"Chunk: {decision.optimal_chunk_size // 1024}KB, "
                              f"Peer: {selected_peer[:12] if selected_peer else 'none'}...")
            
            return file_id
            
        finally:
            # Restore original chunk size
            self.engine.CHUNK_SIZE = original_chunk_size
    
    def update_network_metrics(self, peer_id: str, bandwidth_mbps: float,
                               latency_ms: float, packet_loss: float = 0.0,
                               jitter_ms: float = 0.0):
        """
        Update network metrics for AI learning.
        
        Args:
            peer_id: Peer identifier
            bandwidth_mbps: Measured bandwidth in Mbps
            latency_ms: Round-trip latency in ms
            packet_loss: Packet loss percentage (0.0-1.0)
            jitter_ms: Jitter in ms
        """
        condition = NetworkCondition(
            bandwidth_mbps=bandwidth_mbps,
            latency_ms=latency_ms,
            packet_loss=packet_loss,
            jitter_ms=jitter_ms
        )
        self.ai.update_network_condition(peer_id, condition)
        logger.debug(f"[AI_ENHANCED_FT] Updated network metrics for {peer_id[:12]}...")
    
    def get_transfer_progress(self, file_id: str) -> Dict[str, Any]:
        """
        Get transfer progress (with AI insights).
        
        Args:
            file_id: File ID
            
        Returns:
            Progress dict with AI insights
        """
        progress = self.engine.get_transfer_progress(file_id)
        
        # Add AI insights if available
        transfer = self.engine.transfers.get(file_id)
        if transfer:
            # Analyze transfer performance
            if transfer.status == TransferStatus.IN_PROGRESS:
                elapsed = progress.get('elapsed_time', 0)
                bytes_transferred = progress.get('bytes_transferred', 0)
                if elapsed > 0:
                    current_speed = bytes_transferred / elapsed  # bytes/sec
                    progress['current_speed_mbps'] = (current_speed * 8) / (1024 * 1024)
        
        return progress
    
    def handle_transfer_completion(self, file_id: str, success: bool,
                                  transfer_time: float, peer_id: str):
        """
        Handle transfer completion and feed to AI learning.
        
        Args:
            file_id: File ID
            success: Whether transfer succeeded
            transfer_time: Time taken
            peer_id: Peer used
        """
        transfer = self.engine.transfers.get(file_id)
        if transfer:
            # Get AI decision (stored earlier)
            # For now, create a basic decision for learning
            decision = self.ai.make_transfer_decision(
                file_path=transfer.file_path,
                file_size=transfer.file_size,
                available_peers=[peer_id] if peer_id else [],
                context={}
            )
            
            # Record result for AI learning
            self.ai.record_transfer_result(
                file_path=transfer.file_path,
                success=success,
                transfer_time=transfer_time,
                bytes_transferred=transfer.bytes_transferred,
                peer_id=peer_id or "unknown",
                decision=decision
            )
            
            logger.info(f"[AI_ENHANCED_FT] Transfer {'completed' if success else 'failed'}: {file_id}")
            logger.info(f"[AI_ENHANCED_FT] AI learning updated")
    
    # Delegate other methods to base engine
    def compute_file_hash(self, file_path: str) -> str:
        """Compute file hash."""
        return self.engine.compute_file_hash(file_path)
    
    def read_chunk(self, file_path: str, chunk_id: int) -> Optional[Any]:
        """Read chunk from file."""
        return self.engine.read_chunk(file_path, chunk_id)
    
    def write_chunk(self, file_id: str, chunk: Any, target_path: str = None) -> bool:
        """Write chunk to file."""
        return self.engine.write_chunk(file_id, chunk, target_path)
    
    def resume_transfer(self, file_id: str) -> List[int]:
        """Resume transfer."""
        return self.engine.resume_transfer(file_id)


# Export
__all__ = ['AIEnhancedFileTransferEngine', 'AI_INTEGRATION_AVAILABLE']
