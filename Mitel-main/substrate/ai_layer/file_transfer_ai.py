#!/usr/bin/env python3
"""
AI-Assisted File Transfer
==========================

First-class citizen AI for file transfers:
- Intelligent routing (choose best path)
- Bandwidth optimization (adaptive chunk sizing)
- Priority queuing (AI determines priority)
- Predictive retry (AI predicts retry success)
- Content-aware optimization (AI understands file content)
"""

import sys
import os
import logging
import time
import statistics
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Add paths for AI components
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(base_dir, 'core', 'ai'))

try:
    from learning_module import LearningModule
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logging.warning("[FILE_TRANSFER_AI] LearningModule not available, using fallback")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransferPriority(Enum):
    """Transfer priority levels (AI-determined)"""
    CRITICAL = 1  # System-critical files
    HIGH = 2      # Important user files
    NORMAL = 3    # Regular files
    LOW = 4       # Background transfers
    DEFERRED = 5  # Can wait


@dataclass
class NetworkCondition:
    """Network condition snapshot"""
    bandwidth_mbps: float  # Measured bandwidth
    latency_ms: float      # Round-trip latency
    packet_loss: float     # Packet loss percentage
    jitter_ms: float      # Jitter
    timestamp: float = field(default_factory=time.time)


@dataclass
class TransferDecision:
    """AI decision for file transfer"""
    priority: TransferPriority
    optimal_chunk_size: int  # AI-determined chunk size
    optimal_path: Optional[str]  # Best peer/node path
    retry_delay: float  # AI-predicted retry delay
    should_retry: bool  # AI decision: retry now or wait
    reasoning: str  # AI reasoning (for debugging)


class FileTransferAI:
    """
    AI layer for file transfers.
    
    Makes intelligent decisions about:
    - Transfer priority
    - Chunk sizing
    - Routing
    - Retry timing
    - Bandwidth optimization
    """
    
    def __init__(self, node_id: str):
        """
        Initialize file transfer AI.
        
        Args:
            node_id: Node identifier
        """
        self.node_id = node_id
        self.learning_module = None
        
        if AI_AVAILABLE:
            try:
                self.learning_module = LearningModule()
                logger.info("[FILE_TRANSFER_AI] LearningModule initialized")
            except Exception as e:
                logger.warning(f"[FILE_TRANSFER_AI] Failed to initialize LearningModule: {e}")
        
        # Network condition history
        self.network_history: Dict[str, List[NetworkCondition]] = {}
        
        # Transfer history (for learning)
        self.transfer_history: List[Dict[str, Any]] = []
        
        # File type patterns (for content-aware optimization)
        self.file_type_patterns = {
            'text': ['.txt', '.md', '.json', '.yaml', '.xml'],
            'binary': ['.bin', '.exe', '.so', '.dll'],
            'media': ['.mp4', '.mp3', '.jpg', '.png'],
            'archive': ['.zip', '.tar', '.gz'],
            'code': ['.py', '.js', '.rs', '.cpp', '.h']
        }
        
        logger.info(f"[FILE_TRANSFER_AI] Initialized for node {node_id[:12]}...")
    
    def analyze_file(self, file_path: str, file_size: int) -> Dict[str, Any]:
        """
        Analyze file to determine transfer strategy.
        
        Args:
            file_path: Path to file
            file_size: File size in bytes
            
        Returns:
            Analysis dict with file characteristics
        """
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        
        # Determine file type
        file_type = 'unknown'
        for ftype, exts in self.file_type_patterns.items():
            if extension in exts:
                file_type = ftype
                break
        
        # Determine if file is compressible
        compressible = file_type in ['text', 'code', 'json', 'xml']
        
        # Determine priority hints
        priority_hints = []
        if file_size < 1024:  # < 1KB
            priority_hints.append('small_file')
        elif file_size > 100 * 1024 * 1024:  # > 100MB
            priority_hints.append('large_file')
        
        if file_type == 'binary':
            priority_hints.append('binary_content')
        
        return {
            'file_type': file_type,
            'extension': extension,
            'compressible': compressible,
            'size_category': 'small' if file_size < 1024 * 1024 else 'large',
            'priority_hints': priority_hints
        }
    
    def determine_priority(self, file_path: str, file_size: int, 
                          context: Dict[str, Any] = None) -> TransferPriority:
        """
        AI determines transfer priority.
        
        Args:
            file_path: Path to file
            file_size: File size
            context: Additional context (e.g., user request, system state)
            
        Returns:
            Transfer priority
        """
        analysis = self.analyze_file(file_path, file_size)
        
        # Check context for urgency
        if context:
            if context.get('urgent', False):
                return TransferPriority.CRITICAL
            if context.get('system_file', False):
                return TransferPriority.HIGH
        
        # AI decision based on file characteristics
        if analysis['file_type'] == 'binary' and file_size < 1024 * 1024:
            # Small binaries are often critical
            return TransferPriority.HIGH
        elif analysis['size_category'] == 'small':
            # Small files get priority (quick wins)
            return TransferPriority.NORMAL
        elif file_size > 100 * 1024 * 1024:
            # Large files can be deferred
            return TransferPriority.LOW
        else:
            return TransferPriority.NORMAL
    
    def optimize_chunk_size(self, file_size: int, network_condition: NetworkCondition) -> int:
        """
        AI optimizes chunk size based on network conditions.
        
        Args:
            file_size: File size
            network_condition: Current network condition
            
        Returns:
            Optimal chunk size in bytes
        """
        base_chunk = 64 * 1024  # 64KB base
        
        # Adjust based on bandwidth
        if network_condition.bandwidth_mbps > 100:
            # High bandwidth: larger chunks
            optimal = base_chunk * 4  # 256KB
        elif network_condition.bandwidth_mbps > 10:
            # Medium bandwidth: standard chunks
            optimal = base_chunk  # 64KB
        else:
            # Low bandwidth: smaller chunks (more responsive)
            optimal = base_chunk // 2  # 32KB
        
        # Adjust based on latency
        if network_condition.latency_ms > 100:
            # High latency: larger chunks (fewer round trips)
            optimal = min(optimal * 2, 512 * 1024)  # Max 512KB
        
        # Adjust based on packet loss
        if network_condition.packet_loss > 0.01:  # > 1% loss
            # High loss: smaller chunks (less retransmission)
            optimal = max(optimal // 2, 16 * 1024)  # Min 16KB
        
        # Ensure reasonable bounds
        optimal = max(16 * 1024, min(optimal, 1024 * 1024))  # 16KB - 1MB
        
        return int(optimal)
    
    def update_network_condition(self, peer_id: str, condition: NetworkCondition):
        """
        Update network condition for a peer.
        
        Args:
            peer_id: Peer identifier
            condition: Network condition snapshot
        """
        if peer_id not in self.network_history:
            self.network_history[peer_id] = []
        
        self.network_history[peer_id].append(condition)
        
        # Keep only last 100 measurements
        if len(self.network_history[peer_id]) > 100:
            self.network_history[peer_id] = self.network_history[peer_id][-100:]
    
    def get_network_condition(self, peer_id: str) -> Optional[NetworkCondition]:
        """
        Get current network condition for a peer.
        
        Args:
            peer_id: Peer identifier
            
        Returns:
            Current network condition or None
        """
        if peer_id not in self.network_history or not self.network_history[peer_id]:
            return None
        
        history = self.network_history[peer_id]
        latest = history[-1]
        
        # Return averaged condition over last 5 measurements
        if len(history) >= 5:
            recent = history[-5:]
            return NetworkCondition(
                bandwidth_mbps=statistics.mean([c.bandwidth_mbps for c in recent]),
                latency_ms=statistics.mean([c.latency_ms for c in recent]),
                packet_loss=statistics.mean([c.packet_loss for c in recent]),
                jitter_ms=statistics.mean([c.jitter_ms for c in recent]),
                timestamp=latest.timestamp
            )
        
        return latest
    
    def select_optimal_path(self, available_peers: List[str]) -> Optional[str]:
        """
        AI selects optimal path/peer for transfer.
        
        Args:
            available_peers: List of available peer IDs
            
        Returns:
            Best peer ID or None
        """
        if not available_peers:
            return None
        
        best_peer = None
        best_score = -1
        
        for peer_id in available_peers:
            condition = self.get_network_condition(peer_id)
            if not condition:
                # No history: use default score
                score = 0.5
            else:
                # Score based on bandwidth, latency, packet loss
                bandwidth_score = min(condition.bandwidth_mbps / 100, 1.0)  # Normalize to 0-1
                latency_score = max(0, 1 - (condition.latency_ms / 500))  # Lower latency = higher score
                loss_score = max(0, 1 - (condition.packet_loss * 10))  # Lower loss = higher score
                
                score = (bandwidth_score * 0.5 + latency_score * 0.3 + loss_score * 0.2)
            
            if score > best_score:
                best_score = score
                best_peer = peer_id
        
        return best_peer
    
    def predict_retry_success(self, peer_id: str, failure_count: int) -> Tuple[bool, float]:
        """
        AI predicts if retry will succeed and optimal delay.
        
        Args:
            peer_id: Peer identifier
            failure_count: Number of consecutive failures
            
        Returns:
            Tuple of (should_retry_now, optimal_delay_seconds)
        """
        condition = self.get_network_condition(peer_id)
        
        if not condition:
            # No history: exponential backoff
            delay = min(2 ** failure_count, 60)  # Max 60 seconds
            return (failure_count < 3, delay)
        
        # Check if network condition improved
        if len(self.network_history[peer_id]) >= 2:
            recent = self.network_history[peer_id][-2:]
            if recent[1].bandwidth_mbps > recent[0].bandwidth_mbps * 1.2:
                # Bandwidth improved: retry now
                return (True, 1.0)
        
        # Network unstable: wait longer
        if condition.packet_loss > 0.05:  # > 5% loss
            delay = min(10 * failure_count, 120)  # Max 2 minutes
            return (False, delay)
        
        # Standard exponential backoff
        delay = min(2 ** failure_count, 60)
        return (failure_count < 5, delay)
    
    def make_transfer_decision(self, file_path: str, file_size: int,
                              available_peers: List[str],
                              context: Dict[str, Any] = None) -> TransferDecision:
        """
        AI makes comprehensive transfer decision.
        
        Args:
            file_path: Path to file
            file_size: File size
            available_peers: Available peer IDs
            context: Additional context
            
        Returns:
            Transfer decision
        """
        # Determine priority
        priority = self.determine_priority(file_path, file_size, context)
        
        # Select optimal path
        optimal_path = self.select_optimal_path(available_peers)
        
        # Get network condition for optimal path
        network_condition = None
        if optimal_path:
            network_condition = self.get_network_condition(optimal_path)
        
        if not network_condition:
            # Default network condition
            network_condition = NetworkCondition(
                bandwidth_mbps=10.0,  # Assume 10 Mbps
                latency_ms=50.0,      # Assume 50ms
                packet_loss=0.0,
                jitter_ms=5.0
            )
        
        # Optimize chunk size
        optimal_chunk_size = self.optimize_chunk_size(file_size, network_condition)
        
        # Predict retry (for future use)
        should_retry, retry_delay = self.predict_retry_success(optimal_path or "", 0)
        
        # Generate reasoning
        reasoning = f"Priority: {priority.name}, Chunk: {optimal_chunk_size // 1024}KB, "
        reasoning += f"Path: {optimal_path[:12] if optimal_path else 'none'}..., "
        reasoning += f"Bandwidth: {network_condition.bandwidth_mbps:.1f}Mbps"
        
        return TransferDecision(
            priority=priority,
            optimal_chunk_size=optimal_chunk_size,
            optimal_path=optimal_path,
            retry_delay=retry_delay,
            should_retry=should_retry,
            reasoning=reasoning
        )
    
    def record_transfer_result(self, file_path: str, success: bool, 
                              transfer_time: float, bytes_transferred: int,
                              peer_id: str, decision: TransferDecision):
        """
        Record transfer result for learning.
        
        Args:
            file_path: Path to file
            success: Whether transfer succeeded
            transfer_time: Time taken
            bytes_transferred: Bytes transferred
            peer_id: Peer used
            decision: Original decision
        """
        result = {
            'file_path': file_path,
            'success': success,
            'transfer_time': transfer_time,
            'bytes_transferred': bytes_transferred,
            'peer_id': peer_id,
            'priority': decision.priority.name,
            'chunk_size': decision.optimal_chunk_size,
            'timestamp': time.time()
        }
        
        self.transfer_history.append(result)
        
        # Keep only last 1000 transfers
        if len(self.transfer_history) > 1000:
            self.transfer_history = self.transfer_history[-1000:]
        
        # Learn from result
        if self.learning_module:
            try:
                # Feed result to learning module
                self.learning_module.record_pattern(
                    pattern_type='file_transfer',
                    pattern_data=result
                )
            except Exception as e:
                logger.debug(f"[FILE_TRANSFER_AI] Learning module error: {e}")


# Export
__all__ = ['FileTransferAI', 'TransferPriority', 'NetworkCondition', 'TransferDecision']
