#!/usr/bin/env python3
"""
Task Migration Engine
=====================

Handles automatic task migration when nodes fail or become overloaded.
Ensures continuous operation through autonomous task redistribution.

Features:
- Automatic task migration on node failure
- Load-based task rebalancing
- Task state preservation
- Failover coordination
"""

import sys
import os
import json
import time
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MIGRATING = "migrating"


@dataclass
class Task:
    """Task definition"""
    task_id: str
    task_type: str
    assigned_node: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    data: Dict = field(default_factory=dict)
    priority: int = 5  # 1-10, higher = more important
    retries: int = 0
    max_retries: int = 3


@dataclass
class NodeState:
    """Node state for task migration"""
    node_id: str
    role: str
    resource_score: float
    load_percent: float
    active_tasks: List[str] = field(default_factory=list)
    last_seen: float = field(default_factory=time.time)
    is_alive: bool = True


class TaskMigration:
    """
    Task migration engine.
    
    Handles:
    - Automatic task migration on node failure
    - Load-based task rebalancing
    - Task state preservation
    - Failover coordination
    """
    
    def __init__(self, local_node_id: str):
        """
        Initialize task migration engine.
        
        Args:
            local_node_id: Local node identifier
        """
        self.local_node_id = local_node_id
        
        # Task registry
        self.tasks: Dict[str, Task] = {}
        self.task_lock = threading.Lock()
        
        # Node registry
        self.nodes: Dict[str, NodeState] = {}
        self.node_lock = threading.Lock()
        
        # Migration state
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_task_migrated: Optional[Callable] = None
        self.on_node_failed: Optional[Callable] = None
        
        # Configuration
        self.node_timeout = 30.0  # Seconds before considering node dead
        self.load_threshold = 80.0  # Percent load before rebalancing
        self.monitor_interval = 5.0  # Seconds between checks
        
        logger.info(f"[TASK_MIGRATION] Initialized for node {local_node_id[:12]}...")
    
    def start(self):
        """Start task migration monitoring"""
        if self.running:
            return
        
        self.running = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="task-migration-monitor"
        )
        self.monitor_thread.start()
        
        logger.info("[TASK_MIGRATION] Started monitoring")
    
    def stop(self):
        """Stop task migration monitoring"""
        self.running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
        logger.info("[TASK_MIGRATION] Stopped")
    
    def register_node(self, node_id: str, role: str, resource_score: float, load_percent: float):
        """Register or update node state"""
        with self.node_lock:
            if node_id in self.nodes:
                # Update existing node
                node = self.nodes[node_id]
                node.role = role
                node.resource_score = resource_score
                node.load_percent = load_percent
                node.last_seen = time.time()
                node.is_alive = True
            else:
                # Register new node
                node = NodeState(
                    node_id=node_id,
                    role=role,
                    resource_score=resource_score,
                    load_percent=load_percent
                )
                self.nodes[node_id] = node
                logger.info(f"[TASK_MIGRATION] Registered node: {node_id[:12]}... (role={role}, score={resource_score:.1f})")
    
    def create_task(self, task_id: str, task_type: str, data: Dict = None, priority: int = 5) -> Task:
        """Create new task and assign to best node"""
        with self.task_lock:
            # Find best node for task
            target_node = self._find_best_node_for_task(task_type)
            
            if not target_node:
                logger.warning(f"[TASK_MIGRATION] No available node for task {task_id}")
                target_node = self.local_node_id
            
            # Create task
            task = Task(
                task_id=task_id,
                task_type=task_type,
                assigned_node=target_node,
                data=data or {},
                priority=priority
            )
            
            self.tasks[task_id] = task
            
            # Update node's active tasks
            with self.node_lock:
                if target_node in self.nodes:
                    self.nodes[target_node].active_tasks.append(task_id)
            
            logger.info(f"[TASK_MIGRATION] Created task {task_id} → {target_node[:12]}... (type={task_type})")
            
            return task
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """Update task status"""
        with self.task_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                old_status = task.status
                task.status = status
                
                if status == TaskStatus.RUNNING and not task.started_at:
                    task.started_at = time.time()
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    task.completed_at = time.time()
                    # Remove from node's active tasks
                    with self.node_lock:
                        if task.assigned_node in self.nodes:
                            node = self.nodes[task.assigned_node]
                            if task_id in node.active_tasks:
                                node.active_tasks.remove(task_id)
                
                logger.debug(f"[TASK_MIGRATION] Task {task_id} status: {old_status.value} → {status.value}")
    
    def _find_best_node_for_task(self, task_type: str) -> Optional[str]:
        """Find best node for task based on load and capabilities"""
        with self.node_lock:
            if not self.nodes:
                return None
            
            # Filter alive nodes
            alive_nodes = [n for n in self.nodes.values() if n.is_alive]
            if not alive_nodes:
                return None
            
            # Sort by load (ascending) and resource score (descending)
            sorted_nodes = sorted(
                alive_nodes,
                key=lambda n: (n.load_percent, -n.resource_score)
            )
            
            # Return node with lowest load and highest resources
            return sorted_nodes[0].node_id
    
    def _monitor_loop(self):
        """Monitor nodes and migrate tasks on failure"""
        while self.running:
            try:
                current_time = time.time()
                
                # Check for dead nodes
                with self.node_lock:
                    for node_id, node in list(self.nodes.items()):
                        if node.is_alive and (current_time - node.last_seen) > self.node_timeout:
                            logger.warning(f"[TASK_MIGRATION] Node timeout: {node_id[:12]}...")
                            node.is_alive = False
                            
                            # Migrate tasks from dead node
                            self._migrate_tasks_from_node(node_id)
                            
                            # Notify callback
                            if self.on_node_failed:
                                self.on_node_failed(node_id)
                
                # Check for overloaded nodes
                self._rebalance_tasks()
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"[TASK_MIGRATION] Error in monitor loop: {e}")
                time.sleep(1)
    
    def _migrate_tasks_from_node(self, failed_node_id: str):
        """Migrate all tasks from failed node to other nodes"""
        with self.task_lock:
            # Find tasks assigned to failed node
            tasks_to_migrate = [
                task for task in self.tasks.values()
                if task.assigned_node == failed_node_id and task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
            ]
            
            if not tasks_to_migrate:
                return
            
            logger.info(f"[TASK_MIGRATION] Migrating {len(tasks_to_migrate)} tasks from {failed_node_id[:12]}...")
            
            for task in tasks_to_migrate:
                # Find new node
                new_node = self._find_best_node_for_task(task.task_type)
                
                if not new_node or new_node == failed_node_id:
                    logger.warning(f"[TASK_MIGRATION] No available node for task {task.task_id}")
                    task.status = TaskStatus.FAILED
                    continue
                
                # Migrate task
                old_node = task.assigned_node
                task.assigned_node = new_node
                task.status = TaskStatus.PENDING
                task.retries += 1
                
                # Update node's active tasks
                with self.node_lock:
                    if new_node in self.nodes:
                        self.nodes[new_node].active_tasks.append(task.task_id)
                
                logger.info(f"[TASK_MIGRATION] Migrated task {task.task_id}: {old_node[:12]}... → {new_node[:12]}...")
                
                # Notify callback
                if self.on_task_migrated:
                    self.on_task_migrated(task.task_id, old_node, new_node)
    
    def _rebalance_tasks(self):
        """Rebalance tasks across nodes based on load"""
        with self.node_lock, self.task_lock:
            # Find overloaded nodes
            overloaded_nodes = [
                n for n in self.nodes.values()
                if n.is_alive and n.load_percent > self.load_threshold and len(n.active_tasks) > 1
            ]
            
            if not overloaded_nodes:
                return
            
            # Find underutilized nodes
            available_nodes = [
                n for n in self.nodes.values()
                if n.is_alive and n.load_percent < self.load_threshold
            ]
            
            if not available_nodes:
                return
            
            # Migrate tasks from overloaded to available nodes
            for overloaded_node in overloaded_nodes:
                # Get lowest priority task
                node_tasks = [
                    self.tasks[tid] for tid in overloaded_node.active_tasks
                    if tid in self.tasks and self.tasks[tid].status == TaskStatus.PENDING
                ]
                
                if not node_tasks:
                    continue
                
                # Sort by priority (lowest first)
                node_tasks.sort(key=lambda t: t.priority)
                task_to_migrate = node_tasks[0]
                
                # Find best available node
                available_nodes.sort(key=lambda n: (n.load_percent, -n.resource_score))
                target_node = available_nodes[0]
                
                # Migrate task
                old_node = task_to_migrate.assigned_node
                task_to_migrate.assigned_node = target_node.node_id
                
                # Update node active tasks
                overloaded_node.active_tasks.remove(task_to_migrate.task_id)
                target_node.active_tasks.append(task_to_migrate.task_id)
                
                logger.info(f"[TASK_MIGRATION] Rebalanced task {task_to_migrate.task_id}: "
                           f"{old_node[:12]}... ({overloaded_node.load_percent:.1f}%) → "
                           f"{target_node.node_id[:12]}... ({target_node.load_percent:.1f}%)")
                
                # Notify callback
                if self.on_task_migrated:
                    self.on_task_migrated(task_to_migrate.task_id, old_node, target_node.node_id)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        with self.task_lock:
            return self.tasks.get(task_id)
    
    def get_node_tasks(self, node_id: str) -> List[Task]:
        """Get all tasks assigned to a node"""
        with self.task_lock:
            return [t for t in self.tasks.values() if t.assigned_node == node_id]
    
    def get_statistics(self) -> Dict:
        """Get task migration statistics"""
        with self.task_lock, self.node_lock:
            total_tasks = len(self.tasks)
            pending_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
            running_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)
            completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
            failed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
            
            total_nodes = len(self.nodes)
            alive_nodes = sum(1 for n in self.nodes.values() if n.is_alive)
            dead_nodes = total_nodes - alive_nodes
            
            return {
                "total_tasks": total_tasks,
                "pending_tasks": pending_tasks,
                "running_tasks": running_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "total_nodes": total_nodes,
                "alive_nodes": alive_nodes,
                "dead_nodes": dead_nodes
            }


def test_task_migration():
    """Test task migration"""
    print("=" * 70)
    print("TASK MIGRATION TEST")
    print("=" * 70)
    print()
    
    # Create migration engine
    local_node_id = f"test-node-{int(time.time())}"
    migration = TaskMigration(local_node_id)
    
    # Set up callbacks
    def on_task_migrated(task_id: str, old_node: str, new_node: str):
        print(f"✅ Task migrated: {task_id} → {old_node[:12]}... → {new_node[:12]}...")
    
    def on_node_failed(node_id: str):
        print(f"❌ Node failed: {node_id[:12]}...")
    
    migration.on_task_migrated = on_task_migrated
    migration.on_node_failed = on_node_failed
    
    # Register nodes
    print("Registering nodes...")
    migration.register_node("node-1", "master", 90.0, 30.0)
    migration.register_node("node-2", "ai_processor", 80.0, 50.0)
    migration.register_node("node-3", "drone_controller", 60.0, 70.0)
    print()
    
    # Create tasks
    print("Creating tasks...")
    migration.create_task("task-1", "ai", priority=8)
    migration.create_task("task-2", "sensor", priority=5)
    migration.create_task("task-3", "drone", priority=3)
    print()
    
    # Start monitoring
    migration.start()
    
    # Simulate node failure after 5 seconds
    print("Simulating node failure in 5 seconds...")
    time.sleep(5)
    
    # Mark node-2 as dead (simulate timeout)
    with migration.node_lock:
        if "node-2" in migration.nodes:
            migration.nodes["node-2"].last_seen = time.time() - 100
    
    # Wait for migration
    time.sleep(10)
    
    # Get statistics
    stats = migration.get_statistics()
    print()
    print("Final Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    migration.stop()


if __name__ == "__main__":
    test_task_migration()
