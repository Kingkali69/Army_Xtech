#!/usr/bin/env python3
"""
Dynamic Role Assignment Engine
================================

Automatically assigns roles to nodes based on available resources (CPU, GPU, memory).
Enables autonomous task distribution without manual configuration.

Features:
- CPU/GPU/memory detection
- Dynamic role assignment based on capabilities
- Role migration on resource changes
- Load-based task routing
"""

import sys
import os
import psutil
import platform
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NodeRole(Enum):
    """Node roles based on capabilities"""
    MASTER = "master"                    # Highest resources, coordinates mesh
    AI_PROCESSOR = "ai_processor"        # GPU available, runs AI workloads
    SENSOR_AGGREGATOR = "sensor_aggregator"  # High CPU, aggregates sensor data
    DRONE_CONTROLLER = "drone_controller"    # Medium resources, drone coordination
    BACKUP = "backup"                    # Low resources, backup/redundancy
    EDGE_NODE = "edge_node"              # Minimal resources, data collection only


@dataclass
class NodeCapabilities:
    """Node hardware capabilities"""
    cpu_count: int
    cpu_percent: float
    memory_total_gb: float
    memory_available_gb: float
    memory_percent: float
    gpu_available: bool = False
    gpu_count: int = 0
    gpu_memory_gb: float = 0.0
    platform: str = "unknown"
    architecture: str = "unknown"
    
    def get_resource_score(self) -> float:
        """Calculate overall resource score (0-100)"""
        # Base score from CPU and memory
        cpu_score = min(self.cpu_count * 10, 40)  # Max 40 points for CPU
        memory_score = min(self.memory_total_gb / 32 * 30, 30)  # Max 30 points for memory
        
        # GPU bonus
        gpu_score = 30 if self.gpu_available else 0  # Max 30 points for GPU
        
        total = cpu_score + memory_score + gpu_score
        return min(total, 100)


@dataclass
class NodeRoleAssignment:
    """Node role assignment with metadata"""
    node_id: str
    role: NodeRole
    capabilities: NodeCapabilities
    resource_score: float
    assigned_at: float = field(default_factory=time.time)
    tasks: List[str] = field(default_factory=list)
    load_percent: float = 0.0


class DynamicRoleAssignment:
    """
    Dynamic role assignment engine.
    
    Automatically assigns roles based on node capabilities:
    - MASTER: Highest resource score, coordinates mesh
    - AI_PROCESSOR: GPU available, runs AI workloads
    - SENSOR_AGGREGATOR: High CPU, aggregates sensor data
    - DRONE_CONTROLLER: Medium resources, drone coordination
    - BACKUP: Low resources, backup/redundancy
    - EDGE_NODE: Minimal resources, data collection only
    """
    
    def __init__(self, node_id: str):
        """
        Initialize role assignment engine.
        
        Args:
            node_id: Node identifier
        """
        self.node_id = node_id
        self.capabilities = self._detect_capabilities()
        self.assigned_role: Optional[NodeRole] = None
        self.role_assignment: Optional[NodeRoleAssignment] = None
        
        logger.info(f"[ROLE_ASSIGNMENT] Initialized for node {node_id[:12]}...")
        logger.info(f"[ROLE_ASSIGNMENT] Capabilities: {self.capabilities.cpu_count} CPU, "
                   f"{self.capabilities.memory_total_gb:.1f}GB RAM, GPU={self.capabilities.gpu_available}")
    
    def _detect_capabilities(self) -> NodeCapabilities:
        """Detect node hardware capabilities"""
        try:
            # CPU detection
            cpu_count = psutil.cpu_count(logical=True)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory detection
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            memory_percent = memory.percent
            
            # GPU detection (basic check)
            gpu_available = False
            gpu_count = 0
            gpu_memory_gb = 0.0
            
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_available = True
                    gpu_count = torch.cuda.device_count()
                    if gpu_count > 0:
                        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            except ImportError:
                pass
            
            # Platform info
            platform_name = platform.system().lower()
            architecture = platform.machine()
            
            capabilities = NodeCapabilities(
                cpu_count=cpu_count,
                cpu_percent=cpu_percent,
                memory_total_gb=memory_total_gb,
                memory_available_gb=memory_available_gb,
                memory_percent=memory_percent,
                gpu_available=gpu_available,
                gpu_count=gpu_count,
                gpu_memory_gb=gpu_memory_gb,
                platform=platform_name,
                architecture=architecture
            )
            
            logger.info(f"[ROLE_ASSIGNMENT] Detected capabilities:")
            logger.info(f"  CPU: {cpu_count} cores ({cpu_percent}% used)")
            logger.info(f"  Memory: {memory_total_gb:.1f}GB total, {memory_available_gb:.1f}GB available")
            logger.info(f"  GPU: {gpu_available} ({gpu_count} devices, {gpu_memory_gb:.1f}GB)")
            logger.info(f"  Platform: {platform_name} ({architecture})")
            logger.info(f"  Resource Score: {capabilities.get_resource_score():.1f}/100")
            
            return capabilities
            
        except Exception as e:
            logger.error(f"[ROLE_ASSIGNMENT] Failed to detect capabilities: {e}")
            # Return minimal capabilities
            return NodeCapabilities(
                cpu_count=1,
                cpu_percent=50.0,
                memory_total_gb=1.0,
                memory_available_gb=0.5,
                memory_percent=50.0,
                platform=platform.system().lower(),
                architecture=platform.machine()
            )
    
    def assign_role(self, force_master: bool = False) -> NodeRole:
        """
        Assign role based on capabilities.
        
        Args:
            force_master: Force assignment as master (for initial node)
        
        Returns:
            Assigned role
        """
        if force_master:
            self.assigned_role = NodeRole.MASTER
            logger.info(f"[ROLE_ASSIGNMENT] Forced role: MASTER")
        else:
            self.assigned_role = self._calculate_optimal_role()
            logger.info(f"[ROLE_ASSIGNMENT] Assigned role: {self.assigned_role.value}")
        
        # Create role assignment
        self.role_assignment = NodeRoleAssignment(
            node_id=self.node_id,
            role=self.assigned_role,
            capabilities=self.capabilities,
            resource_score=self.capabilities.get_resource_score()
        )
        
        return self.assigned_role
    
    def _calculate_optimal_role(self) -> NodeRole:
        """Calculate optimal role based on capabilities"""
        score = self.capabilities.get_resource_score()
        
        # GPU available → AI Processor
        if self.capabilities.gpu_available:
            logger.info(f"[ROLE_ASSIGNMENT] GPU detected → AI_PROCESSOR")
            return NodeRole.AI_PROCESSOR
        
        # High resources (score > 70) → Sensor Aggregator or Master candidate
        if score > 70:
            if self.capabilities.cpu_count >= 8:
                logger.info(f"[ROLE_ASSIGNMENT] High CPU ({self.capabilities.cpu_count} cores) → SENSOR_AGGREGATOR")
                return NodeRole.SENSOR_AGGREGATOR
            else:
                logger.info(f"[ROLE_ASSIGNMENT] High resources (score {score:.1f}) → MASTER candidate")
                return NodeRole.MASTER
        
        # Medium resources (score 40-70) → Drone Controller
        if score > 40:
            logger.info(f"[ROLE_ASSIGNMENT] Medium resources (score {score:.1f}) → DRONE_CONTROLLER")
            return NodeRole.DRONE_CONTROLLER
        
        # Low resources (score 20-40) → Backup
        if score > 20:
            logger.info(f"[ROLE_ASSIGNMENT] Low resources (score {score:.1f}) → BACKUP")
            return NodeRole.BACKUP
        
        # Minimal resources → Edge Node
        logger.info(f"[ROLE_ASSIGNMENT] Minimal resources (score {score:.1f}) → EDGE_NODE")
        return NodeRole.EDGE_NODE
    
    def get_role(self) -> Optional[NodeRole]:
        """Get assigned role"""
        return self.assigned_role
    
    def get_role_assignment(self) -> Optional[NodeRoleAssignment]:
        """Get full role assignment"""
        return self.role_assignment
    
    def update_load(self, load_percent: float):
        """Update current load percentage"""
        if self.role_assignment:
            self.role_assignment.load_percent = load_percent
    
    def add_task(self, task_id: str):
        """Add task to node"""
        if self.role_assignment:
            self.role_assignment.tasks.append(task_id)
    
    def remove_task(self, task_id: str):
        """Remove task from node"""
        if self.role_assignment and task_id in self.role_assignment.tasks:
            self.role_assignment.tasks.remove(task_id)
    
    def can_accept_task(self, task_type: str) -> bool:
        """Check if node can accept a specific task type"""
        if not self.assigned_role:
            return False
        
        # Role-based task acceptance
        role_capabilities = {
            NodeRole.MASTER: ["coordination", "sync", "discovery", "ai", "sensor", "drone"],
            NodeRole.AI_PROCESSOR: ["ai", "ml", "inference", "training"],
            NodeRole.SENSOR_AGGREGATOR: ["sensor", "data_processing", "aggregation"],
            NodeRole.DRONE_CONTROLLER: ["drone", "flight_control", "telemetry"],
            NodeRole.BACKUP: ["sync", "backup", "redundancy"],
            NodeRole.EDGE_NODE: ["data_collection", "monitoring"]
        }
        
        accepted_tasks = role_capabilities.get(self.assigned_role, [])
        return task_type in accepted_tasks
    
    def get_status_dict(self) -> Dict:
        """Get role assignment status as dictionary"""
        if not self.role_assignment:
            return {"error": "No role assigned"}
        
        return {
            "node_id": self.role_assignment.node_id[:12] + "...",
            "role": self.role_assignment.role.value,
            "resource_score": round(self.role_assignment.resource_score, 1),
            "cpu_count": self.capabilities.cpu_count,
            "memory_gb": round(self.capabilities.memory_total_gb, 1),
            "gpu_available": self.capabilities.gpu_available,
            "load_percent": round(self.role_assignment.load_percent, 1),
            "active_tasks": len(self.role_assignment.tasks),
            "assigned_at": time.strftime("%Y-%m-%d %H:%M:%S", 
                                         time.localtime(self.role_assignment.assigned_at))
        }


def test_role_assignment():
    """Test role assignment"""
    print("=" * 70)
    print("DYNAMIC ROLE ASSIGNMENT TEST")
    print("=" * 70)
    print()
    
    # Create role assignment
    node_id = f"test-node-{int(time.time())}"
    role_engine = DynamicRoleAssignment(node_id)
    
    # Assign role
    assigned_role = role_engine.assign_role()
    
    print()
    print("Role Assignment:")
    print(f"  Node ID: {node_id[:12]}...")
    print(f"  Assigned Role: {assigned_role.value}")
    print()
    
    # Get status
    status = role_engine.get_status_dict()
    print("Node Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    print()
    
    # Test task acceptance
    print("Task Acceptance:")
    test_tasks = ["ai", "sensor", "drone", "coordination", "data_collection"]
    for task in test_tasks:
        can_accept = role_engine.can_accept_task(task)
        print(f"  {task}: {'✅ Yes' if can_accept else '❌ No'}")
    print()


if __name__ == "__main__":
    test_role_assignment()
