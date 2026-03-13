#!/usr/bin/env python3
"""
AI Agent Shell - Core Framework
Apache 2.0 Licensed Universal AI Agent Framework

A modular, extensible framework for building specialized AI agents.
The security modules plug into this core shell system.

Copyright 2024 - Licensed under Apache 2.0
"""

import asyncio
import json
import logging
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Type, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import importlib
import sys

# Core framework version
__version__ = "1.0.0"
__license__ = "Apache-2.0"


class AgentState(Enum):
    """AI Agent operational states"""
    INITIALIZING = "initializing"
    READY = "ready"
    WORKING = "working"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class MessageType(Enum):
    """Inter-agent communication message types"""
    TASK = "task"
    RESULT = "result"
    STATUS = "status"
    ERROR = "error"
    CONTROL = "control"
    DATA = "data"


@dataclass
class AgentMessage:
    """Universal message format for agent communication"""
    id: str
    type: MessageType
    sender: str
    receiver: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 1  # 1=low, 5=critical
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCapability:
    """Describes what an agent or module can do"""
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    requirements: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "Unknown"


@dataclass
class AgentMetrics:
    """Performance and operational metrics"""
    tasks_processed: int = 0
    tasks_successful: int = 0
    tasks_failed: int = 0
    average_processing_time: float = 0.0
    uptime: timedelta = field(default_factory=lambda: timedelta())
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    last_activity: datetime = field(default_factory=datetime.now)


class AIModule(ABC):
    """
    Base class for all AI modules that plug into the shell
    
    This is what your security modules inherit from to integrate
    with the AI shell framework
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.shell: Optional['AIAgentShell'] = None
        self.logger = logging.getLogger(f"module.{name}")
        self.config = {}
        self.state = AgentState.INITIALIZING
        self.metrics = AgentMetrics()
        self._capabilities: List[AgentCapability] = []
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the module with configuration"""
        pass
    
    @abstractmethod
    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process an incoming message and return response"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """Return list of capabilities this module provides"""
        pass
    
    async def shutdown(self):
        """Clean shutdown of the module"""
        self.state = AgentState.SHUTDOWN
        self.logger.info(f"Module {self.name} shutting down")
    
    def can_handle(self, message: AgentMessage) -> bool:
        """Check if this module can handle the given message"""
        return False
    
    def register_shell(self, shell: 'AIAgentShell'):
        """Register the parent shell for inter-module communication"""
        self.shell = shell
    
    async def send_message(self, message: AgentMessage):
        """Send message through the shell's message bus"""
        if self.shell:
            await self.shell.route_message(message)
    
    def update_metrics(self, processing_time: float, success: bool):
        """Update module performance metrics"""
        self.metrics.tasks_processed += 1
        if success:
            self.metrics.tasks_successful += 1
        else:
            self.metrics.tasks_failed += 1
        
        # Update average processing time
        total_tasks = self.metrics.tasks_processed
        current_avg = self.metrics.average_processing_time
        self.metrics.average_processing_time = (
            (current_avg * (total_tasks - 1) + processing_time) / total_tasks
        )
        
        self.metrics.last_activity = datetime.now()


class MessageBus:
    """
    Central message routing system for inter-agent communication
    Handles pub/sub, direct messaging, and broadcast
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_history: List[AgentMessage] = []
        self.max_history = 1000
        self.logger = logging.getLogger("MessageBus")
    
    def subscribe(self, topic: str, callback: Callable[[AgentMessage], None]):
        """Subscribe to messages on a specific topic"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
        self.logger.debug(f"New subscriber for topic: {topic}")
    
    def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribe from a topic"""
        if topic in self.subscribers:
            self.subscribers[topic].remove(callback)
    
    async def publish(self, topic: str, message: AgentMessage):
        """Publish message to all subscribers of a topic"""
        self._add_to_history(message)
        
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    self.logger.error(f"Error in subscriber callback: {e}")
    
    async def send_direct(self, message: AgentMessage):
        """Send message directly to specific receiver"""
        self._add_to_history(message)
        topic = f"direct.{message.receiver}"
        await self.publish(topic, message)
    
    async def broadcast(self, message: AgentMessage):
        """Broadcast message to all subscribers"""
        self._add_to_history(message)
        for topic in self.subscribers:
            await self.publish(topic, message)
    
    def _add_to_history(self, message: AgentMessage):
        """Add message to history with size limit"""
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)
    
    def get_message_history(self, limit: int = 100) -> List[AgentMessage]:
        """Get recent message history"""
        return self.message_history[-limit:]


class ModuleRegistry:
    """
    Registry system for managing AI modules
    Handles module discovery, loading, and lifecycle management
    """
    
    def __init__(self):
        self.modules: Dict[str, AIModule] = {}
        self.module_types: Dict[str, Type[AIModule]] = {}
        self.logger = logging.getLogger("ModuleRegistry")
    
    def register_module_type(self, module_class: Type[AIModule]):
        """Register a module class for later instantiation"""
        module_name = getattr(module_class, '_module_name', module_class.__name__)
        self.module_types[module_name] = module_class
        self.logger.info(f"Registered module type: {module_name}")
    
    async def load_module(self, module_name: str, config: Dict[str, Any] = None) -> AIModule:
        """Load and initialize a module instance"""
        if module_name not in self.module_types:
            raise ValueError(f"Unknown module type: {module_name}")
        
        module_class = self.module_types[module_name]
        module_instance = module_class(module_name)
        
        # Initialize the module
        if config is None:
            config = {}
        
        success = await module_instance.initialize(config)
        if not success:
            raise RuntimeError(f"Failed to initialize module: {module_name}")
        
        self.modules[module_name] = module_instance
        module_instance.state = AgentState.READY
        
        self.logger.info(f"Loaded module: {module_name}")
        return module_instance
    
    async def unload_module(self, module_name: str):
        """Unload a module instance"""
        if module_name in self.modules:
            module = self.modules[module_name]
            await module.shutdown()
            del self.modules[module_name]
            self.logger.info(f"Unloaded module: {module_name}")
    
    def get_module(self, module_name: str) -> Optional[AIModule]:
        """Get a loaded module instance"""
        return self.modules.get(module_name)
    
    def list_modules(self) -> List[str]:
        """List all loaded modules"""
        return list(self.modules.keys())
    
    def list_available_types(self) -> List[str]:
        """List all registered module types"""
        return list(self.module_types.keys())
    
    def get_capabilities(self) -> Dict[str, List[AgentCapability]]:
        """Get capabilities of all loaded modules"""
        capabilities = {}
        for name, module in self.modules.items():
            capabilities[name] = module.get_capabilities()
        return capabilities
    
    def find_modules_for_task(self, task_type: str) -> List[str]:
        """Find modules that can handle a specific task type"""
        capable_modules = []
        for name, module in self.modules.items():
            capabilities = module.get_capabilities()
            for cap in capabilities:
                if task_type in cap.input_types:
                    capable_modules.append(name)
                    break
        return capable_modules


class WorkflowEngine:
    """
    Orchestrates complex multi-module workflows
    Handles task chaining, parallel processing, and error recovery
    """
    
    def __init__(self, message_bus: MessageBus, registry: ModuleRegistry):
        self.message_bus = message_bus
        self.registry = registry
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("WorkflowEngine")
    
    def define_workflow(self, workflow_id: str, workflow_definition: Dict[str, Any]):
        """Define a reusable workflow"""
        self.workflows[workflow_id] = workflow_definition
        self.logger.info(f"Defined workflow: {workflow_id}")
    
    async def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a defined workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        
        workflow_def = self.workflows[workflow_id]
        execution_id = f"{workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.active_workflows[execution_id] = {
            "workflow_id": workflow_id,
            "definition": workflow_def,
            "input_data": input_data,
            "status": "running",
            "start_time": datetime.now(),
            "results": {}
        }
        
        try:
            result = await self._execute_workflow_steps(workflow_def, input_data)
            self.active_workflows[execution_id]["status"] = "completed"
            self.active_workflows[execution_id]["results"] = result
            return result
        
        except Exception as e:
            self.active_workflows[execution_id]["status"] = "failed"
            self.active_workflows[execution_id]["error"] = str(e)
            self.logger.error(f"Workflow {execution_id} failed: {e}")
            raise
    
    async def _execute_workflow_steps(self, workflow_def: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual workflow steps"""
        steps = workflow_def.get("steps", [])
        results = {}
        current_data = data.copy()
        
        for step in steps:
            step_name = step["name"]
            module_name = step["module"]
            step_config = step.get("config", {})
            
            self.logger.info(f"Executing workflow step: {step_name}")
            
            # Get the module
            module = self.registry.get_module(module_name)
            if not module:
                raise RuntimeError(f"Module not found for step {step_name}: {module_name}")
            
            # Create message for the module
            message = AgentMessage(
                id=f"workflow_step_{step_name}",
                type=MessageType.TASK,
                sender="workflow_engine",
                receiver=module_name,
                payload={
                    "step_name": step_name,
                    "config": step_config,
                    "data": current_data
                }
            )
            
            # Process the step
            response = await module.process(message)
            step_result = response.payload
            
            # Store step result
            results[step_name] = step_result
            
            # Update current data for next step
            if step.get("pass_data", True):
                current_data.update(step_result.get("output_data", {}))
        
        return {
            "workflow_results": results,
            "final_data": current_data
        }


class AIAgentShell:
    """
    Main AI Agent Shell - The core framework that everything plugs into
    
    This is the central nervous system that coordinates all modules,
    handles communication, manages workflows, and provides the runtime environment.
    """
    
    def __init__(self, name: str = "AI-Agent-Shell", config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.state = AgentState.INITIALIZING
        self.logger = logging.getLogger("AIAgentShell")
        
        # Core components
        self.message_bus = MessageBus()
        self.module_registry = ModuleRegistry()
        self.workflow_engine = WorkflowEngine(self.message_bus, self.module_registry)
        
        # Runtime state
        self.running = False
        self.start_time = datetime.now()
        self.metrics = AgentMetrics()
        
        # Thread pool for CPU-intensive tasks
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.get('max_workers', 4),
            thread_name_prefix="ai-agent"
        )
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        self.logger.info(f"AI Agent Shell '{name}' initialized")
    
    async def initialize(self):
        """Initialize the shell and all components"""
        self.logger.info("Initializing AI Agent Shell...")
        
        # Subscribe to system messages
        self.message_bus.subscribe("system", self._handle_system_message)
        self.message_bus.subscribe("control", self._handle_control_message)
        
        # Load modules from config
        modules_config = self.config.get('modules', {})
        for module_name, module_config in modules_config.items():
            try:
                await self.module_registry.load_module(module_name, module_config)
                # Register shell with module for communication
                module = self.module_registry.get_module(module_name)
                if module:
                    module.register_shell(self)
            except Exception as e:
                self.logger.error(f"Failed to load module {module_name}: {e}")
        
        # Load workflows from config
        workflows_config = self.config.get('workflows', {})
        for workflow_id, workflow_def in workflows_config.items():
            self.workflow_engine.define_workflow(workflow_id, workflow_def)
        
        self.state = AgentState.READY
        self.logger.info("AI Agent Shell initialized successfully")
    
    async def start(self):
        """Start the agent shell"""
        if self.state != AgentState.READY:
            await self.initialize()
        
        self.running = True
        self.state = AgentState.WORKING
        self.start_time = datetime.now()
        
        self.logger.info(f"AI Agent Shell '{self.name}' started")
        
        # Emit start event
        await self._emit_event("agent_started", {"agent_name": self.name})
        
        # Main event loop
        try:
            while self.running:
                await self._process_pending_tasks()
                await asyncio.sleep(0.1)  # Prevent busy waiting
        
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            self.state = AgentState.ERROR
        
        finally:
            await self.shutdown()
    
    async def stop(self):
        """Stop the agent shell"""
        self.logger.info("Stopping AI Agent Shell...")
        self.running = False
    
    async def shutdown(self):
        """Clean shutdown of the shell and all modules"""
        self.logger.info("Shutting down AI Agent Shell...")
        
        # Shutdown all modules
        for module_name in self.module_registry.list_modules():
            await self.module_registry.unload_module(module_name)
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        self.state = AgentState.SHUTDOWN
        await self._emit_event("agent_shutdown", {"agent_name": self.name})
        
        self.logger.info("AI Agent Shell shutdown complete")
    
    async def route_message(self, message: AgentMessage):
        """Route message through the system"""
        self.logger.debug(f"Routing message {message.id} from {message.sender} to {message.receiver}")
        
        # Direct message routing
        if message.receiver != "broadcast":
            await self.message_bus.send_direct(message)
        else:
            await self.message_bus.broadcast(message)
    
    async def process_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task using appropriate modules"""
        # Find capable modules
        capable_modules = self.module_registry.find_modules_for_task(task_type)
        
        if not capable_modules:
            raise ValueError(f"No modules available for task type: {task_type}")
        
        # Use the first capable module (could be enhanced with load balancing)
        module_name = capable_modules[0]
        module = self.module_registry.get_module(module_name)
        
        # Create task message
        message = AgentMessage(
            id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type=MessageType.TASK,
            sender="shell",
            receiver=module_name,
            payload={"task_type": task_type, "task_data": task_data}
        )
        
        # Process task
        start_time = datetime.now()
        try:
            response = await module.process(message)
            processing_time = (datetime.now() - start_time).total_seconds()
            module.update_metrics(processing_time, True)
            
            return response.payload
        
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            module.update_metrics(processing_time, False)
            raise
    
    def register_module_type(self, module_class: Type[AIModule]):
        """Register a module type with the shell"""
        self.module_registry.register_module_type(module_class)
    
    async def load_module(self, module_name: str, config: Dict[str, Any] = None) -> AIModule:
        """Load a modu
