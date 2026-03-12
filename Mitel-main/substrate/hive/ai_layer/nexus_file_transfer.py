#!/usr/bin/env python3
"""
NEXUS File Transfer Integration
================================

NEXUS (first-class citizen AI) controls file transfers intelligently.
NEXUS makes routing, priority, and optimization decisions.
"""

import sys
import os
import logging
from typing import Dict, Any, List, Optional

# Add paths
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_5_files_as_payloads'))

try:
    from trinity_enhanced_llm import TrinityEnhancedLLM
    from file_transfer_ai import FileTransferAI, TransferDecision, TransferPriority, NetworkCondition
    NEXUS_AVAILABLE = True
except ImportError as e:
    NEXUS_AVAILABLE = False
    logging.warning(f"[NEXUS_FT] Components not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NexusFileTransfer:
    """
    NEXUS-controlled file transfer.
    
    NEXUS (first-class citizen AI) makes intelligent decisions:
    - Routing (which peer to use)
    - Priority (how urgent)
    - Chunk size (optimization)
    - Retry strategy (when to retry)
    """
    
    def __init__(self, node_id: str, nexus_llm: TrinityEnhancedLLM = None):
        """
        Initialize NEXUS file transfer controller.
        
        Args:
            node_id: Node identifier
            nexus_llm: NEXUS LLM instance (creates new if None)
        """
        self.node_id = node_id
        
        # Initialize NEXUS if not provided
        if nexus_llm is None:
            try:
                self.nexus = TrinityEnhancedLLM()
                logger.info("[NEXUS_FT] NEXUS initialized")
            except Exception as e:
                logger.error(f"[NEXUS_FT] Failed to initialize NEXUS: {e}")
                self.nexus = None
        else:
            self.nexus = nexus_llm
        
        # Initialize FileTransferAI (fallback if NEXUS unavailable)
        self.file_transfer_ai = FileTransferAI(node_id=node_id)
        
        logger.info(f"[NEXUS_FT] Initialized for node {node_id[:12]}...")
        logger.info("[NEXUS_FT] NEXUS is controlling file transfers - first-class citizen active")
    
    def make_transfer_decision(self, file_path: str, file_size: int,
                              available_peers: List[str],
                              network_conditions: Dict[str, NetworkCondition] = None,
                              context: Dict[str, Any] = None) -> TransferDecision:
        """
        NEXUS makes intelligent transfer decision.
        
        Args:
            file_path: Path to file
            file_size: File size in bytes
            available_peers: Available peer IDs
            network_conditions: Network conditions per peer
            context: Additional context (urgency, system_file, etc.)
            
        Returns:
            Transfer decision with NEXUS intelligence
        """
        if not self.nexus:
            # Fallback to basic FileTransferAI
            logger.warning("[NEXUS_FT] NEXUS not available, using basic FileTransferAI")
            return self.file_transfer_ai.make_transfer_decision(
                file_path, file_size, available_peers, context
            )
        
        # Build context for NEXUS
        nexus_context = self._build_nexus_context(
            file_path, file_size, available_peers, network_conditions, context
        )
        
        # Ask NEXUS for decision (concise prompt to avoid context window issues)
        file_name = os.path.basename(file_path)
        size_mb = file_size / (1024*1024)
        peers_str = ', '.join(available_peers[:2])  # Limit peers
        network_str = self._format_network_conditions(network_conditions)[:100]  # Limit length
        
        nexus_prompt = f"""File transfer decision:
File: {file_name} ({size_mb:.1f}MB)
Peers: {peers_str}
Network: {network_str}
Urgent: {context.get('urgent', False) if context else False}

Respond format:
PRIORITY: [CRITICAL/HIGH/NORMAL/LOW]
CHUNK_SIZE_KB: [number]
BEST_PEER: [peer_id]
RETRY: [yes/no]
REASONING: [one sentence]"""
        
        # Get NEXUS decision
        nexus_response = self.nexus.chat(nexus_prompt)
        nexus_text = nexus_response['response']
        
        # Parse NEXUS decision
        decision = self._parse_nexus_decision(
            nexus_text, file_path, file_size, available_peers, network_conditions
        )
        
        logger.info(f"[NEXUS_FT] NEXUS Decision: {decision.reasoning}")
        logger.info(f"[NEXUS_FT] Priority: {decision.priority.name}, Chunk: {decision.optimal_chunk_size // 1024}KB, Peer: {decision.optimal_path[:12] if decision.optimal_path else 'none'}...")
        
        return decision
    
    def _build_nexus_context(self, file_path: str, file_size: int,
                            available_peers: List[str],
                            network_conditions: Dict[str, NetworkCondition],
                            context: Dict[str, Any]) -> str:
        """Build context string for NEXUS"""
        context_parts = []
        
        if context:
            if context.get('urgent'):
                context_parts.append("URGENT transfer")
            if context.get('system_file'):
                context_parts.append("System file")
        
        if network_conditions:
            best_peer = max(network_conditions.items(), 
                          key=lambda x: x[1].bandwidth_mbps if x[1] else 0)
            context_parts.append(f"Best bandwidth: {best_peer[1].bandwidth_mbps:.1f} Mbps on {best_peer[0]}")
        
        return ", ".join(context_parts) if context_parts else "Standard transfer"
    
    def _format_network_conditions(self, network_conditions: Dict[str, NetworkCondition]) -> str:
        """Format network conditions for NEXUS"""
        if not network_conditions:
            return "Unknown"
        
        formatted = []
        for peer_id, condition in list(network_conditions.items())[:3]:
            formatted.append(f"{peer_id[:8]}...: {condition.bandwidth_mbps:.1f}Mbps, {condition.latency_ms:.0f}ms")
        
        return "; ".join(formatted)
    
    def _parse_nexus_decision(self, nexus_text: str, file_path: str, file_size: int,
                              available_peers: List[str],
                              network_conditions: Dict[str, NetworkCondition]) -> TransferDecision:
        """Parse NEXUS response into TransferDecision"""
        # Extract values from NEXUS response
        priority = TransferPriority.NORMAL
        chunk_size_kb = 64
        best_peer = available_peers[0] if available_peers else None
        retry = True
        delay = 2.0
        reasoning = "NEXUS decision"
        
        nexus_upper = nexus_text.upper()
        
        # Parse priority
        if 'CRITICAL' in nexus_upper:
            priority = TransferPriority.CRITICAL
        elif 'HIGH' in nexus_upper:
            priority = TransferPriority.HIGH
        elif 'LOW' in nexus_upper or 'DEFERRED' in nexus_upper:
            priority = TransferPriority.LOW
        elif 'DEFERRED' in nexus_upper:
            priority = TransferPriority.DEFERRED
        
        # Parse chunk size
        if 'CHUNK_SIZE' in nexus_upper:
            import re
            match = re.search(r'CHUNK_SIZE[:\s]+(\d+)', nexus_upper)
            if match:
                chunk_size_kb = int(match.group(1))
        
        # Parse best peer
        if 'BEST_PEER' in nexus_upper or 'PEER' in nexus_upper:
            for peer in available_peers:
                if peer[:8].upper() in nexus_upper:
                    best_peer = peer
                    break
        
        # Parse retry
        if 'NO RETRY' in nexus_upper or 'RETRY: NO' in nexus_upper:
            retry = False
        if 'DELAY' in nexus_upper:
            import re
            match = re.search(r'DELAY[:\s]+(\d+)', nexus_upper)
            if match:
                delay = float(match.group(1))
        
        # Extract reasoning
        if 'REASONING:' in nexus_text:
            reasoning = nexus_text.split('REASONING:')[-1].strip()[:200]
        elif 'REASONING' in nexus_text:
            reasoning = nexus_text.split('REASONING')[-1].strip()[:200]
        
        # Convert chunk size to bytes
        optimal_chunk_size = chunk_size_kb * 1024
        
        # Ensure reasonable bounds
        optimal_chunk_size = max(16 * 1024, min(optimal_chunk_size, 1024 * 1024))
        
        return TransferDecision(
            priority=priority,
            optimal_chunk_size=int(optimal_chunk_size),
            optimal_path=best_peer,
            retry_delay=delay,
            should_retry=retry,
            reasoning=f"NEXUS: {reasoning}"
        )
    
    def update_network_metrics(self, peer_id: str, condition: NetworkCondition):
        """Update network metrics (delegates to FileTransferAI)"""
        self.file_transfer_ai.update_network_condition(peer_id, condition)
    
    def record_transfer_result(self, file_path: str, success: bool,
                              transfer_time: float, bytes_transferred: int,
                              peer_id: str, decision: TransferDecision):
        """Record transfer result and feed to NEXUS for learning"""
        # Record in FileTransferAI
        self.file_transfer_ai.record_transfer_result(
            file_path, success, transfer_time, bytes_transferred, peer_id, decision
        )
        
        # Feed to NEXUS for learning
        if self.nexus:
            learning_prompt = f"""Learn from this file transfer result:

File: {file_path}
Success: {success}
Time: {transfer_time:.2f}s
Peer: {peer_id}
Decision: Priority {decision.priority.name}, Chunk {decision.optimal_chunk_size // 1024}KB

What should I learn from this?"""
            
            # NEXUS processes and learns
            self.nexus.chat(learning_prompt)
            logger.info("[NEXUS_FT] NEXUS learned from transfer result")


# Export
__all__ = ['NexusFileTransfer', 'NEXUS_AVAILABLE']
