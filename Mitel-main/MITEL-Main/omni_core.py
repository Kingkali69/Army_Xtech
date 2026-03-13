#!/usr/bin/env python3
"""
OMNI CORE - Unified Orchestrator
=================================

Non-negotiable requirements:
- Auto-configure
- Launch
- Sync & update
- Failover
- Recovery
- Discovery
- Offline first
- Airgapped
- Zero cloud dependency

This is the master orchestrator that ties everything together.
"""

import os
import sys
import json
import time
import uuid
import socket
import logging
import threading
import platform
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

# Add paths
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_1_state_store'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_2_state_model'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_3_crdt_merge'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_4_sync_engine'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_5_files_as_payloads'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_6_self_healing'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_7_adapters'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'filesystem'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'discovery'))
sys.path.insert(0, os.path.join(base_dir, 'substrate'))

# Import substrate components
try:
    from step_1_state_store.state_store import (
        AuthoritativeStateStore, StateOp, OpType, get_state_store
    )
    from step_2_state_model.state_model import (
        StateModel, get_state_model
    )
except ImportError as e:
    # Fallback: try direct import
    import importlib.util
    spec1 = importlib.util.spec_from_file_location(
        "state_store",
        os.path.join(base_dir, 'substrate', 'step_1_state_store', 'state_store.py')
    )
    state_store_mod = importlib.util.module_from_spec(spec1)
    spec1.loader.exec_module(state_store_mod)
    
    spec2 = importlib.util.spec_from_file_location(
        "state_model",
        os.path.join(base_dir, 'substrate', 'step_2_state_model', 'state_model.py')
    )
    state_model_mod = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(state_model_mod)
    
    AuthoritativeStateStore = state_store_mod.AuthoritativeStateStore
    StateOp = state_store_mod.StateOp
    OpType = state_store_mod.OpType
    get_state_store = state_store_mod.get_state_store
    StateModel = state_model_mod.StateModel
    get_state_model = state_model_mod.get_state_model

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)
logger = logging.getLogger("omni.core")


class NodeStatus(Enum):
    """Node operational status"""
    INITIALIZING = "initializing"
    DISCOVERING = "discovering"
    SYNCING = "syncing"
    ONLINE = "online"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    OFFLINE = "offline"


@dataclass
class NodeInfo:
    """Node information"""
    node_id: str
    ip: str
    port: int
    platform: str
    capabilities: List[str] = field(default_factory=list)
    last_seen: float = field(default_factory=time.time)
    vector_clock: Dict[str, int] = field(default_factory=dict)
    is_master: bool = False
    health_score: float = 100.0


class OmniCore:
    """
    Master orchestrator for OMNI organism.
    
    Responsibilities:
    - Auto-configuration
    - Component lifecycle management
    - State synchronization
    - Failover and recovery
    - Offline-first discovery
    - Zero cloud dependency
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize OMNI core
        
        Args:
            config_path: Optional path to config file (auto-detected if None)
        """
        self.config = self._auto_configure(config_path)
        self.node_id = self._generate_node_id()
        self.status = NodeStatus.INITIALIZING
        
        # Core components
        self.state_store: Optional[AuthoritativeStateStore] = None
        self.state_model: Optional[StateModel] = None
        
        # Mesh networking
        self.mesh_port = self.config.get('mesh_port', 7777)
        self.peers: Dict[str, NodeInfo] = {}
        self.is_master = False
        self.master_node_id: Optional[str] = None
        
        # Discovery
        self.discovery_running = False
        self.discovery_thread: Optional[threading.Thread] = None
        self.auto_discovery = None  # Enhanced auto-discovery with standalone mode
        self.standalone_mode = False
        
        # Mesh listener
        self.mesh_listener_running = False
        self.mesh_listener_thread: Optional[threading.Thread] = None
        self.mesh_socket: Optional[socket.socket] = None
        
        # Sync engine (STEP 4)
        self.sync_engine = None
        self.sync_running = False
        self.sync_thread: Optional[threading.Thread] = None
        self.pending_ops: deque = deque(maxlen=10000)
        
        # Recovery
        self.recovery_enabled = True
        self.last_health_check = 0
        self.health_check_interval = 30
        
        # File transfer engine (STEP 5)
        self.file_transfer_engine = None
        
        # Recovery engine (STEP 6)
        self.recovery_engine = None
        
        # Adapter manager (STEP 7)
        self.adapter_manager = None
        
        # AI components (First-Class Citizen)
        self.ai_command_executor = None
        self.cross_platform_bridge = None
        
        # Shared NEXUS Container (Unified AI across mesh)
        self.nexus_container = None
        
        # Failover
        self.failover_enabled = True
        self.master_timeout = 60  # seconds
        
        # Threading
        self.running = False
        self.lock = threading.Lock()
        
        # Event listeners
        self.event_listeners: Dict[str, List[Callable]] = {}
        
        logger.info(f"[OMNI] Initializing node {self.node_id[:12]}...")
    
    def _auto_configure(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Auto-configure system.
        
        Detects platform, network, and sets defaults.
        Zero cloud dependency - all config is local.
        """
        config_dir = Path.home() / '.omni'
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / 'config.json'
        
        # Load existing config if present
        if config_path:
            config_file = Path(config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"[OMNI] Loaded config from {config_file}")
                return config
            except Exception as e:
                logger.warning(f"[OMNI] Failed to load config: {e}, using defaults")
        
        # Auto-detect platform
        system = platform.system().lower()
        if 'linux' in system:
            if 'android' in platform.platform().lower():
                platform_name = 'android'
            else:
                platform_name = 'linux'
        elif 'windows' in system:
            platform_name = 'windows'
        elif 'darwin' in system:
            platform_name = 'macos'
        else:
            platform_name = 'unknown'
        
        # Auto-detect network
        local_ip = self._get_local_ip()
        
        # Default config
        config = {
            'node_id': None,  # Will be generated
            'platform': platform_name,
            'local_ip': local_ip,
            'mesh_port': 7777,
            'discovery_port': 45678,
            'state_db_path': str(config_dir / 'state.db'),
            'data_dir': str(config_dir),
            'sync_interval': 5,  # seconds
            'discovery_interval': 10,  # seconds
            'heartbeat_interval': 30,  # seconds
            'max_peers': 50,
            'enable_recovery': True,
            'enable_failover': True,
            'offline_mode': True,  # Always offline-first
            'airgapped': True,  # No cloud dependency
        }
        
        # Save config
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"[OMNI] Auto-configured and saved to {config_file}")
        except Exception as e:
            logger.warning(f"[OMNI] Failed to save config: {e}")
        
        return config
    
    def _generate_node_id(self) -> str:
        """Generate unique node ID"""
        # Try to get from config first
        if self.config.get('node_id'):
            return self.config['node_id']
        
        # Generate based on hostname + MAC + timestamp
        try:
            import uuid as uuid_lib
            mac = ':'.join(['{:02x}'.format((uuid_lib.getnode() >> i) & 0xff) 
                           for i in range(0, 8*6, 8)][::-1])
        except:
            mac = str(uuid.uuid4())
        
        seed = f"{socket.gethostname()}{mac}{time.time()}"
        node_id = f"omni_{hashlib.sha256(seed.encode()).hexdigest()[:16]}"
        
        # Save to config
        self.config['node_id'] = node_id
        self._save_config()
        
        return node_id
    
    def _get_local_ip(self) -> str:
        """Get local IP address (offline-first, no cloud dependency)"""
        # Method 1: Try network interfaces directly
        try:
            import netifaces
            gateways = netifaces.gateways()
            if 'default' in gateways and netifaces.AF_INET in gateways['default']:
                interface = gateways['default'][netifaces.AF_INET][1]
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    if not ip.startswith('127.'):
                        return ip
        except:
            pass
        
        # Method 2: Try socket connection (works offline for local network)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Connect to non-routable address (doesn't actually connect)
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
            s.close()
            if not ip.startswith('127.'):
                return ip
        except:
            pass
        
        # Method 3: Try hostname
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if not ip.startswith('127.'):
                return ip
        except:
            pass
        
        # Fallback
        return '127.0.0.1'
    
    def _save_config(self):
        """Save current config"""
        config_file = Path.home() / '.omni' / 'config.json'
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.warning(f"[OMNI] Failed to save config: {e}")
    
    def initialize(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("[OMNI] Initializing components...")
            
            # 1. Initialize state store
            logger.info("[OMNI] Initializing state store...")
            self.state_store = get_state_store(db_path=self.config['state_db_path'])
            if not self.state_store.validate_db():
                logger.error("[OMNI] State store validation failed!")
                return False
            
            # 2. Initialize state model (with CRDT merge)
            logger.info("[OMNI] Initializing state model...")
            self.state_model = get_state_model(state_store=self.state_store, node_id=self.node_id)
            
            # 3. Register this node in state
            self._register_node()
            
            # 4. Start mesh listener (for sync requests)
            logger.info("[OMNI] Starting mesh listener...")
            self._start_mesh_listener()
            
            # 5. Start enhanced auto-discovery (with standalone mode support)
            logger.info("[OMNI] Starting enhanced auto-discovery...")
            try:
                auto_discovery_path = os.path.join(base_dir, 'substrate', 'discovery', 'auto_discovery.py')
                if os.path.exists(auto_discovery_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("auto_discovery", auto_discovery_path)
                    auto_discovery_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(auto_discovery_mod)
                    AutoDiscovery = auto_discovery_mod.AutoDiscovery
                    
                    # Determine if we're master (first node or configured)
                    is_master = self.config.get('is_master', False) or len(self.peers) == 0
                    
                    self.auto_discovery = AutoDiscovery(
                        node_id=self.node_id,
                        local_ip=self.config['local_ip'],
                        fabric_port=self.mesh_port,
                        is_master=is_master,
                        platform=self.config['platform']
                    )
                    
                    # Set up callbacks
                    self.auto_discovery.on_master_discovered = self._on_master_discovered
                    self.auto_discovery.on_standalone_entered = self._on_standalone_entered
                    self.auto_discovery.on_standalone_exited = self._on_standalone_exited
                    
                    self.auto_discovery.start()
                    logger.info("[OMNI] Enhanced auto-discovery started (standalone mode supported)")
                else:
                    logger.warning("[OMNI] Enhanced auto-discovery not available, using basic discovery")
                    self._start_discovery()  # Fallback to basic discovery
            except Exception as e:
                logger.warning(f"[OMNI] Enhanced auto-discovery not available: {e}")
                self._start_discovery()  # Fallback to basic discovery
            
            # 6. Initialize sync engine (STEP 4)
            logger.info("[OMNI] Initializing sync engine...")
            try:
                # Try import with resolved path
                sync_engine_path = os.path.join(base_dir, 'substrate', 'step_4_sync_engine', 'sync_engine.py')
                if os.path.exists(sync_engine_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("sync_engine", sync_engine_path)
                    sync_engine_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(sync_engine_mod)
                    SyncEngine = sync_engine_mod.SyncEngine
                    
                    self.sync_engine = SyncEngine(
                        state_model=self.state_model,
                        node_id=self.node_id,
                        sync_interval=self.config.get('sync_interval', 5.0)
                    )
                    self.sync_engine.start()
                    logger.info("[OMNI] Sync engine started (STEP 4)")
                else:
                    raise ImportError(f"Sync engine file not found: {sync_engine_path}")
            except Exception as e:
                logger.warning(f"[OMNI] Sync engine not available, using basic sync: {e}")
                self._start_sync()  # Fallback to basic sync
            
            # 6.5. Load peers from omni_peers.json after sync engine is ready
            self._load_peers_from_file()
            
            # 7. Initialize AI-enhanced file transfer engine (STEP 5 + AI)
            logger.info("[OMNI] Initializing AI-enhanced file transfer engine...")
            try:
                # Try AI-enhanced version first
                ai_integration_path = os.path.join(base_dir, 'substrate', 'ai_layer', 'ai_integration.py')
                if os.path.exists(ai_integration_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("ai_integration", ai_integration_path)
                    ai_integration_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(ai_integration_mod)
                    
                    if hasattr(ai_integration_mod, 'AI_INTEGRATION_AVAILABLE') and ai_integration_mod.AI_INTEGRATION_AVAILABLE:
                        # Try NEXUS-enhanced first (first-class citizen)
                        if hasattr(ai_integration_mod, 'NexusEnhancedFileTransferEngine'):
                            NexusEnhancedFileTransferEngine = ai_integration_mod.NexusEnhancedFileTransferEngine
                            # Initialize NEXUS LLM for file transfers
                            try:
                                nexus_path = os.path.join(base_dir, 'substrate', 'ai_layer', 'trinity_enhanced_llm.py')
                                if os.path.exists(nexus_path):
                                    import importlib.util
                                    spec = importlib.util.spec_from_file_location("trinity_enhanced_llm", nexus_path)
                                    nexus_mod = importlib.util.module_from_spec(spec)
                                    spec.loader.exec_module(nexus_mod)
                                    TrinityEnhancedLLM = nexus_mod.TrinityEnhancedLLM
                                    nexus_llm = TrinityEnhancedLLM()
                                    self.file_transfer_engine = NexusEnhancedFileTransferEngine(
                                        node_id=self.node_id,
                                        data_dir=os.path.join(self.config['data_dir'], 'files'),
                                        nexus_llm=nexus_llm
                                    )
                                    logger.info("[OMNI] NEXUS-controlled file transfer engine initialized (STEP 5 + NEXUS)")
                                else:
                                    raise ImportError("NEXUS not available")
                            except Exception as e:
                                logger.warning(f"[OMNI] NEXUS not available, using basic AI: {e}")
                                # Fallback to basic AI-enhanced
                                AIEnhancedFileTransferEngine = ai_integration_mod.AIEnhancedFileTransferEngine
                                self.file_transfer_engine = AIEnhancedFileTransferEngine(
                                    node_id=self.node_id,
                                    data_dir=os.path.join(self.config['data_dir'], 'files')
                                )
                                logger.info("[OMNI] AI-enhanced file transfer engine initialized (STEP 5 + AI)")
                        else:
                            # Fallback to basic AI-enhanced
                            AIEnhancedFileTransferEngine = ai_integration_mod.AIEnhancedFileTransferEngine
                            self.file_transfer_engine = AIEnhancedFileTransferEngine(
                                node_id=self.node_id,
                                data_dir=os.path.join(self.config['data_dir'], 'files')
                            )
                            logger.info("[OMNI] AI-enhanced file transfer engine initialized (STEP 5 + AI)")
                    else:
                        raise ImportError("AI integration not available")
                else:
                    # Fallback to base file transfer engine
                    file_transfer_path = os.path.join(base_dir, 'substrate', 'step_5_files_as_payloads', 'file_transfer.py')
                    if os.path.exists(file_transfer_path):
                        import importlib.util
                        spec = importlib.util.spec_from_file_location("file_transfer", file_transfer_path)
                        file_transfer_mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(file_transfer_mod)
                        FileTransferEngine = file_transfer_mod.FileTransferEngine
                        
                        self.file_transfer_engine = FileTransferEngine(
                            data_dir=os.path.join(self.config['data_dir'], 'files')
                        )
                        logger.info("[OMNI] File transfer engine initialized (STEP 5, AI not available)")
                    else:
                        logger.warning("[OMNI] File transfer engine not available")
            except Exception as e:
                logger.warning(f"[OMNI] File transfer engine not available: {e}")
            
            # 8. Initialize recovery engine (STEP 6)
            logger.info("[OMNI] Initializing recovery engine...")
            try:
                recovery_path = os.path.join(base_dir, 'substrate', 'step_6_self_healing', 'recovery_engine.py')
                if os.path.exists(recovery_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("recovery_engine", recovery_path)
                    recovery_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(recovery_mod)
                    RecoveryEngine = recovery_mod.RecoveryEngine
                    
                    self.recovery_engine = RecoveryEngine(
                        state_store=self.state_store,
                        state_model=self.state_model,
                        sync_engine=self.sync_engine,
                        file_transfer_engine=self.file_transfer_engine,
                        health_check_interval=self.health_check_interval
                    )
                    
                    # Register recovery callbacks
                    self.recovery_engine.register_recovery_callback(
                        "state_store",
                        self.recovery_engine.recover_database
                    )
                    self.recovery_engine.register_recovery_callback(
                        "state_model",
                        self.recovery_engine.recover_state_from_corruption
                    )
                    
                    self.recovery_engine.start()
                    logger.info("[OMNI] Recovery engine initialized (STEP 6)")
                else:
                    logger.warning("[OMNI] Recovery engine not available")
            except Exception as e:
                logger.warning(f"[OMNI] Recovery engine not available: {e}")
            
            # 9. Initialize adapter manager (STEP 7)
            logger.info("[OMNI] Initializing adapter manager...")
            try:
                adapter_path = os.path.join(base_dir, 'substrate', 'step_7_adapters', 'adapter_bridge.py')
                if os.path.exists(adapter_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("adapter_bridge", adapter_path)
                    adapter_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(adapter_mod)
                    AdapterManager = adapter_mod.AdapterManager
                    
                    self.adapter_manager = AdapterManager(
                        state_model=self.state_model,
                        node_id=self.node_id
                    )
                    
                    # Load platform adapter for current platform
                    platform_name = self.config['platform'].lower()
                    # Normalize platform name
                    if platform_name == 'darwin':
                        platform_name = 'macos'
                    elif platform_name not in ['linux', 'windows', 'macos', 'android', 'ios']:
                        platform_name = 'linux'  # Default to linux
                    
                    bridge = self.adapter_manager.load_platform_adapter(platform_name)
                    if bridge:
                        self.adapter_manager.start_all()
                        logger.info(f"[OMNI] Adapter manager initialized (STEP 7) - {platform_name} adapter loaded")
                    else:
                        logger.warning(f"[OMNI] Platform adapter not available for {platform_name}, trying generic")
                        # Try generic adapter as fallback
                        bridge = self.adapter_manager.load_platform_adapter('generic')
                        if bridge:
                            self.adapter_manager.start_all()
                            logger.info(f"[OMNI] Generic adapter loaded as fallback")
                else:
                    logger.warning("[OMNI] Adapter bridge not available")
            except Exception as e:
                logger.warning(f"[OMNI] Adapter manager not available: {e}")
            
            # 10. Initialize AI Command Executor (First-Class Citizen)
            logger.info("[OMNI] Initializing AI Command Executor...")
            try:
                ai_executor_path = os.path.join(base_dir, 'substrate', 'ai_layer', 'ai_command_executor.py')
                if os.path.exists(ai_executor_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("ai_command_executor", ai_executor_path)
                    ai_executor_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(ai_executor_mod)
                    AICommandExecutor = ai_executor_mod.AICommandExecutor
                    
                    self.ai_command_executor = AICommandExecutor(
                        node_id=self.node_id,
                        state_model=self.state_model,
                        nexus_container=self.nexus_container  # Shared container for unified AI
                    )
                    logger.info("[OMNI] AI Command Executor initialized - AI is FIRST-CLASS CITIZEN")
                else:
                    logger.warning("[OMNI] AI Command Executor not available")
            except Exception as e:
                logger.warning(f"[OMNI] AI Command Executor not available: {e}")
            
            # 11. Initialize Cross-Platform Bridge (Bank Teller)
            logger.info("[OMNI] Initializing Cross-Platform Bridge...")
            try:
                bridge_path = os.path.join(base_dir, 'substrate', 'filesystem', 'cross_platform_bridge.py')
                if os.path.exists(bridge_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("cross_platform_bridge", bridge_path)
                    bridge_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(bridge_mod)
                    CrossPlatformBridge = bridge_mod.CrossPlatformBridge
                    
                    self.cross_platform_bridge = CrossPlatformBridge(
                        node_id=self.node_id,
                        state_model=self.state_model
                    )
                    logger.info("[OMNI] Cross-Platform Bridge initialized - AI is 'bank teller'")
                else:
                    logger.warning("[OMNI] Cross-Platform Bridge not available")
            except Exception as e:
                logger.warning(f"[OMNI] Cross-Platform Bridge not available: {e}")
            
            # 11.5. Initialize Shared NEXUS Container (Unified AI across mesh)
            logger.info("[OMNI] Initializing Shared NEXUS Container...")
            try:
                nexus_container_path = os.path.join(base_dir, 'substrate', 'ai_layer', 'nexus_container_layer.py')
                if os.path.exists(nexus_container_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("nexus_container_layer", nexus_container_path)
                    nexus_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(nexus_mod)
                    NEXUSContainer = nexus_mod.NEXUSContainer
                    
                    # Use shared container path in data directory
                    container_path = os.path.join(self.config['data_dir'], 'nexus_container')
                    self.nexus_container = NEXUSContainer(container_path=container_path)
                    
                    # Register this node with the container
                    self.nexus_container.register_node(
                        node_id=self.node_id,
                        platform=self.config['platform'],
                        ip=self.config.get('local_ip', '127.0.0.1'),
                        capabilities=['ai_command_executor', 'sync_engine', 'file_transfer']
                    )
                    
                    logger.info("[OMNI] Shared NEXUS Container initialized - Unified AI across mesh")
                else:
                    logger.warning("[OMNI] NEXUS Container not available")
            except Exception as e:
                logger.warning(f"[OMNI] NEXUS Container not available: {e}")
            
            # 12. Initialize GhostLang transport for network isolation bypass
            logger.info("[OMNI] Initializing GhostLang transport...")
            try:
                ghostlang_path = os.path.join(base_dir, 'substrate', 'ghostlang_transport.py')
                if os.path.exists(ghostlang_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("ghostlang_transport", ghostlang_path)
                    ghostlang_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(ghostlang_mod)
                    GhostLangTransport = ghostlang_mod.GhostLangTransport
                    
                    self.ghostlang_transport = GhostLangTransport(
                        node_id=self.node_id,
                        data_dir=os.path.join(self.config['data_dir'], 'ghostlang'),
                        auth_key='omni_mesh'
                    )
                    
                    # Register callback for received mesh commands
                    self.ghostlang_transport.register_message_callback(self._handle_ghostlang_message)
                    
                    # Start transport
                    if self.ghostlang_transport.start():
                        logger.info("[OMNI] GhostLang transport initialized - can bypass network isolation")
                    else:
                        logger.warning("[OMNI] GhostLang transport failed to start")
                        self.ghostlang_transport = None
                else:
                    logger.debug("[OMNI] GhostLang transport not available")
                    self.ghostlang_transport = None
            except Exception as e:
                logger.warning(f"[OMNI] GhostLang transport not available: {e}")
                self.ghostlang_transport = None
            
            # 13. Initialize M.I.T.E.L. Zero-Trust Peripheral Authentication
            logger.info("[OMNI] Initializing M.I.T.E.L. subsystem...")
            try:
                mitel_path = os.path.join(base_dir, 'substrate', 'mitel_subsystem.py')
                if os.path.exists(mitel_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("mitel_subsystem", mitel_path)
                    mitel_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mitel_mod)
                    MITELSubsystem = mitel_mod.MITELSubsystem
                    
                    # M.I.T.E.L. configuration
                    mitel_config = {
                        'enabled': True,
                        'device_registry_file': os.path.join(self.config['data_dir'], 'mitel_devices.yaml'),
                        'behavioral_profiles_file': os.path.join(self.config['data_dir'], 'mitel_profiles.yaml'),
                        'anomaly_threshold': 0.8,
                        'auto_quarantine': True,
                        'require_admin_approval': False,
                        'scan_interval': 1.0,
                        'behavioral_analysis': True,
                        'real_time_monitoring': True,
                        'pos_mode': False,
                        'pos_skimmer_detection': True,
                        'linux_integration': True,
                        'windows_integration': True,
                        'android_integration': True,
                        'neural_analysis': True,
                        'behavioral_learning': True,
                        'log_level': 'INFO',
                        'audit_all_events': True,
                        'threat_event_retention': 30
                    }
                    
                    self.mitel_subsystem = MITELSubsystem(
                        config=mitel_config,
                        state_model=self.state_model,
                        node_id=self.node_id
                    )
                    
                    # Initialize M.I.T.E.L.
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    mitel_initialized = loop.run_until_complete(self.mitel_subsystem.initialize())
                    loop.close()
                    
                    if mitel_initialized:
                        # Start M.I.T.E.L. monitoring
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        mitel_started = loop.run_until_complete(self.mitel_subsystem.start())
                        loop.close()
                        
                        if mitel_started:
                            logger.info("[OMNI] M.I.T.E.L. zero-trust protection ACTIVE - threats propagate <10ms")
                        else:
                            logger.warning("[OMNI] M.I.T.E.L. failed to start")
                            self.mitel_subsystem = None
                    else:
                        logger.warning("[OMNI] M.I.T.E.L. initialization failed")
                        self.mitel_subsystem = None
                else:
                    logger.debug("[OMNI] M.I.T.E.L. subsystem not available")
                    self.mitel_subsystem = None
            except Exception as e:
                logger.warning(f"[OMNI] M.I.T.E.L. subsystem not available: {e}")
                self.mitel_subsystem = None
            
            # 14. Start health monitoring (legacy, now handled by recovery engine)
            logger.info("[OMNI] Starting health monitoring...")
            self._start_health_monitoring()
            
            self.status = NodeStatus.ONLINE
            logger.info("[OMNI] ✅ Initialization complete")
            
            return True
            
        except Exception as e:
            logger.error(f"[OMNI] Initialization failed: {e}", exc_info=True)
            self.status = NodeStatus.OFFLINE
            return False
    
    def _register_node(self):
        """Register this node in state"""
        node_op = StateOp(
            op_id=str(uuid.uuid4()),
            op_type=OpType.SET,
            key=f"nodes.{self.node_id}",
            value={
                'node_id': self.node_id,
                'ip': self.config['local_ip'],
                'port': self.mesh_port,
                'platform': self.config['platform'],
                'capabilities': ['sync', 'discovery', 'failover', 'recovery'],
                'registered_at': time.time(),
                'status': 'online'
            },
            node_id=self.node_id
        )
        
        if self.state_model.apply_op(node_op):
            logger.info(f"[OMNI] Node registered: {self.node_id}")
        else:
            logger.error("[OMNI] Failed to register node")
    
    def _load_peers_from_file(self):
        """Load peers from omni_peers.json file"""
        try:
            # Try current directory first
            peers_file = Path('omni_peers.json')
            if not peers_file.exists():
                # Try script directory
                script_dir = Path(__file__).parent
                peers_file = script_dir / 'omni_peers.json'
            
            if not peers_file.exists():
                logger.debug("[OMNI] No omni_peers.json found, skipping peer loading")
                return
            
            with open(peers_file, 'r') as f:
                peers_config = json.load(f)
            
            peers_list = peers_config.get('peers', [])
            if not peers_list:
                logger.debug("[OMNI] No peers configured in omni_peers.json")
                return
            
            logger.info(f"[OMNI] Loading {len(peers_list)} peers from omni_peers.json")
            
            for peer in peers_list:
                peer_ip = peer.get('ip')
                if not peer_ip:
                    continue
                
                # Skip self
                if peer_ip == self.config['local_ip']:
                    continue
                
                # Generate a temporary node ID for this peer
                peer_node_id = f"omni_peer_{hashlib.sha256(peer_ip.encode()).hexdigest()[:16]}"
                
                # Add to peers dict
                with self.lock:
                    self.peers[peer_node_id] = NodeInfo(
                        node_id=peer_node_id,
                        ip=peer_ip,
                        port=self.mesh_port,
                        platform='unknown',
                        capabilities=[],
                        last_seen=time.time()
                    )
                
                # Register with sync engine if available
                if self.sync_engine:
                    self.sync_engine.register_peer(peer_node_id, peer_ip, self.mesh_port)
                
                logger.info(f"[OMNI] Loaded peer from config: {peer_ip}")
            
            logger.info(f"[OMNI] Loaded {len(peers_list)} peers from omni_peers.json")
            
        except Exception as e:
            logger.warning(f"[OMNI] Failed to load peers from file: {e}")
    
    def _start_mesh_listener(self):
        """Start mesh listener for sync requests"""
        if self.mesh_listener_running:
            return
        
        self.mesh_listener_running = True
        self.mesh_listener_thread = threading.Thread(
            target=self._mesh_listener_loop,
            daemon=True,
            name="omni-mesh-listener"
        )
        self.mesh_listener_thread.start()
        logger.info("[OMNI] Mesh listener started")
    
    def _mesh_listener_loop(self):
        """Mesh listener loop - handles sync requests"""
        try:
            self.mesh_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.mesh_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.mesh_socket.bind(('0.0.0.0', self.mesh_port))
            self.mesh_socket.listen(100)
            self.mesh_socket.settimeout(1.0)
            
            logger.info(f"[OMNI] Mesh listener on port {self.mesh_port}")
            
            while self.mesh_listener_running and self.running:
                try:
                    conn, addr = self.mesh_socket.accept()
                    threading.Thread(
                        target=self._handle_mesh_connection,
                        args=(conn, addr),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.debug(f"[OMNI] Mesh listener error: {e}")
                    
        except Exception as e:
            logger.error(f"[OMNI] Failed to start mesh listener: {e}")
        finally:
            if self.mesh_socket:
                try:
                    self.mesh_socket.close()
                except:
                    pass
    
    def _handle_mesh_connection(self, conn: socket.socket, addr: tuple):
        """Handle incoming mesh connection"""
        try:
            data = conn.recv(65535).decode()
            if not data:
                return
            
            request = json.loads(data)
            req_type = request.get('type')
            
            if req_type == 'sync_request':
                self._handle_sync_request(conn, request)
            else:
                logger.debug(f"[OMNI] Unknown request type: {req_type}")
                
        except Exception as e:
            logger.debug(f"[OMNI] Mesh connection error: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
    
    def _handle_sync_request(self, conn: socket.socket, request: dict):
        """Handle sync request from peer"""
        try:
            peer_node_id = request.get('node_id')
            last_op_id = request.get('last_op_id')
            
            # Get ops since last_op_id (None = get all recent ops)
            ops = self.state_store.get_log_tail(last_op_id=last_op_id, limit=1000)
            
            # Serialize ops
            ops_data = []
            for op in ops:
                try:
                    ops_data.append(op.to_dict())
                except Exception as e:
                    logger.debug(f"[OMNI] Failed to serialize op {op.op_id}: {e}")
                    continue
            
            # Get vector clock for response
            vector_clock_dict = {}
            if self.state_model.crdt_engine:
                vector_clock_dict = self.state_model.crdt_engine.get_clock().to_dict()
            
            # Send response
            response = {
                'type': 'sync_response',
                'node_id': self.node_id,
                'ops': ops_data,
                'count': len(ops_data),
                'last_op_id': last_op_id,
                'vector_clock': vector_clock_dict,
                'timestamp': time.time()
            }
            
            conn.sendall(json.dumps(response).encode())
            logger.debug(f"[OMNI] Sent {len(ops_data)} ops to {peer_node_id[:12] if peer_node_id else 'unknown'}")
            
        except Exception as e:
            logger.error(f"[OMNI] Failed to handle sync request: {e}")
            try:
                # Send error response
                error_response = {
                    'type': 'sync_error',
                    'node_id': self.node_id,
                    'error': str(e),
                    'timestamp': time.time()
                }
                conn.sendall(json.dumps(error_response).encode())
            except:
                pass
    
    def _start_discovery(self):
        """Start offline-first discovery"""
        if self.discovery_running:
            return
        
        self.discovery_running = True
        self.discovery_thread = threading.Thread(
            target=self._discovery_loop,
            daemon=True,
            name="omni-discovery"
        )
        self.discovery_thread.start()
        logger.info("[OMNI] Discovery started")
    
    def _discovery_loop(self):
        """Discovery loop - offline-first, no cloud dependency"""
        discovery_port = self.config.get('discovery_port', 45678)
        interval = self.config.get('discovery_interval', 10)
        
        # UDP socket for broadcast discovery
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(1.0)
        except Exception as e:
            logger.error(f"[OMNI] Failed to create discovery socket: {e}")
            return
        
        # Listen for discovery messages
        listen_sock = None
        try:
            listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listen_sock.bind(('0.0.0.0', discovery_port))
            listen_sock.settimeout(1.0)
        except Exception as e:
            logger.error(f"[OMNI] Failed to create discovery listener: {e}")
            return
        
        logger.info(f"[OMNI] Discovery listening on port {discovery_port}")
        
        while self.discovery_running and self.running:
            try:
                # Send discovery broadcast
                discovery_msg = json.dumps({
                    'type': 'discovery',
                    'node_id': self.node_id,
                    'ip': self.config['local_ip'],
                    'port': self.mesh_port,
                    'platform': self.config['platform'],
                    'capabilities': ['sync', 'discovery', 'failover', 'recovery'],
                    'timestamp': time.time()
                }).encode()
                
                try:
                    sock.sendto(discovery_msg, ('255.255.255.255', discovery_port))
                except:
                    pass  # May fail in some network configs, continue
                
                # Listen for responses
                try:
                    data, addr = listen_sock.recvfrom(4096)
                    self._handle_discovery_message(data, addr)
                except socket.timeout:
                    pass
                except Exception as e:
                    logger.debug(f"[OMNI] Discovery receive error: {e}")
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"[OMNI] Discovery loop error: {e}")
                time.sleep(interval)
        
        if sock:
            sock.close()
        if listen_sock:
            listen_sock.close()
    
    def _on_master_discovered(self, peer):
        """Callback when master is discovered"""
        logger.info(f"[OMNI] Master discovered: {peer.node_id[:12]}... at {peer.ip}:{peer.port}")
        
        # Add to peers dict
        with self.lock:
            self.peers[peer.node_id] = NodeInfo(
                node_id=peer.node_id,
                ip=peer.ip,
                port=peer.port,
                platform=peer.platform,
                capabilities=peer.capabilities,
                last_seen=time.time()
            )
        
        # Register with sync engine
        if self.sync_engine:
            self.sync_engine.register_peer(peer.node_id, peer.ip, peer.port)
    
    def _on_standalone_entered(self):
        """Callback when entering standalone mode"""
        self.standalone_mode = True
        logger.warning("[OMNI] Entering standalone mode - master not available")
        self.status = NodeStatus.DEGRADED
    
    def _on_standalone_exited(self, master_peer):
        """Callback when exiting standalone mode"""
        self.standalone_mode = False
        logger.info("[OMNI] Exiting standalone mode - master available")
        self.status = NodeStatus.ONLINE
        # Reconnect sync engine
        if self.sync_engine and master_peer:
            self.sync_engine.register_peer(master_peer.node_id, master_peer.ip, master_peer.port)
    
    def _handle_discovery_message(self, data: bytes, addr: tuple):
        """Handle incoming discovery message"""
        try:
            msg = json.loads(data.decode())
            if msg.get('type') != 'discovery':
                return
            
            node_id = msg.get('node_id')
            if node_id == self.node_id:
                return  # Ignore self
            
            # Update peer info
            with self.lock:
                if node_id not in self.peers:
                    logger.info(f"[OMNI] Discovered peer: {node_id[:12]} at {addr[0]}")
                
                peer_ip = msg.get('ip', addr[0])
                peer_port = msg.get('port', self.mesh_port)
                
                self.peers[node_id] = NodeInfo(
                    node_id=node_id,
                    ip=peer_ip,
                    port=peer_port,
                    platform=msg.get('platform', 'unknown'),
                    capabilities=msg.get('capabilities', []),
                    last_seen=time.time()
                )
                
                # Register with sync engine (STEP 4)
                if self.sync_engine:
                    self.sync_engine.register_peer(node_id, peer_ip, peer_port)
                
                # Update state
                peer_op = StateOp(
                    op_id=str(uuid.uuid4()),
                    op_type=OpType.SET,
                    key=f"peers.{node_id}",
                    value={
                        'node_id': node_id,
                        'ip': peer_ip,
                        'port': peer_port,
                        'platform': msg.get('platform', 'unknown'),
                        'last_seen': time.time()
                    },
                    node_id=self.node_id
                )
                self.state_model.apply_op(peer_op)
                
        except Exception as e:
            logger.debug(f"[OMNI] Failed to handle discovery message: {e}")
    
    def _start_sync(self):
        """Start sync engine"""
        if self.sync_running:
            return
        
        self.sync_running = True
        self.sync_thread = threading.Thread(
            target=self._sync_loop,
            daemon=True,
            name="omni-sync"
        )
        self.sync_thread.start()
        logger.info("[OMNI] Sync engine started")
    
    def _sync_loop(self):
        """Sync loop - exchange ops with peers"""
        interval = self.config.get('sync_interval', 5)
        
        while self.sync_running and self.running:
            try:
                # Get last op ID we've seen from each peer
                last_op_ids = {}
                for node_id in self.peers.keys():
                    last_op = self.state_model.get(f"sync.last_op_id.{node_id}")
                    if last_op:
                        last_op_ids[node_id] = last_op
                
                # Exchange ops with peers
                for node_id, peer_info in list(self.peers.items()):
                    if time.time() - peer_info.last_seen > 300:  # 5 min timeout
                        continue  # Skip stale peers
                    
                    try:
                        self._sync_with_peer(node_id, peer_info, last_op_ids.get(node_id))
                    except Exception as e:
                        logger.debug(f"[OMNI] Sync with {node_id[:12]} failed: {e}")
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"[OMNI] Sync loop error: {e}")
                time.sleep(interval)
    
    def _sync_with_peer(self, node_id: str, peer_info: NodeInfo, last_op_id: Optional[str]):
        """Sync operations with a peer"""
        try:
            # Connect to peer
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((peer_info.ip, peer_info.port))
            
            # Request ops since last_op_id
            request = {
                'type': 'sync_request',
                'node_id': self.node_id,
                'last_op_id': last_op_id,
                'timestamp': time.time()
            }
            sock.sendall(json.dumps(request).encode())
            
            # Receive ops
            data = sock.recv(65535).decode()
            response = json.loads(data)
            
            if response.get('type') == 'sync_response':
                ops_data = response.get('ops', [])
                for op_data in ops_data:
                    op = StateOp.from_dict(op_data)
                    if op.node_id != self.node_id:  # Don't apply our own ops
                        self.state_model.apply_op(op)
                        # Update last op ID
                        update_op = StateOp(
                            op_id=str(uuid.uuid4()),
                            op_type=OpType.SET,
                            key=f"sync.last_op_id.{op.node_id}",
                            value=op.op_id,
                            node_id=self.node_id
                        )
                        self.state_model.apply_op(update_op)
            
            sock.close()
            
        except Exception as e:
            logger.debug(f"[OMNI] Sync with peer failed: {e}")
    
    def _start_health_monitoring(self):
        """Start health monitoring and recovery"""
        def health_loop():
            while self.running:
                try:
                    self._health_check()
                    time.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"[OMNI] Health check error: {e}")
                    time.sleep(self.health_check_interval)
        
        threading.Thread(target=health_loop, daemon=True, name="omni-health").start()
    
    def _health_check(self):
        """Perform health check and recovery"""
        # Check state store health
        if self.state_store and not self.state_store.validate_db():
            logger.warning("[OMNI] State store corruption detected - initiating recovery")
            if self.recovery_enabled:
                self._recover_state_store()
        
        # Check for stale peers
        now = time.time()
        stale_peers = []
        with self.lock:
            for node_id, peer in self.peers.items():
                if now - peer.last_seen > 300:  # 5 min
                    stale_peers.append(node_id)
        
        for node_id in stale_peers:
            logger.info(f"[OMNI] Removing stale peer: {node_id[:12]}")
            with self.lock:
                del self.peers[node_id]
        
        # Check master failover
        if self.failover_enabled and self.is_master:
            # Check if we're still master
            pass  # TODO: Implement master health check
    
    def _handle_ghostlang_message(self, message: Dict[str, Any]):
        """Handle mesh command received through GhostLang transport"""
        try:
            # Extract command type
            cmd_type = message.get('type')
            
            if cmd_type == 'sync_request':
                # Handle sync request from peer via GhostLang
                peer_node_id = message.get('node_id')
                last_op_id = message.get('last_op_id')
                
                # Get ops to send back
                ops = self.state_store.get_log_tail(last_op_id=last_op_id, limit=1000)
                ops_data = [op.to_dict() for op in ops]
                
                # Send response back through GhostLang
                response = {
                    'type': 'sync_response',
                    'node_id': self.node_id,
                    'ops': ops_data,
                    'count': len(ops_data),
                    'timestamp': time.time()
                }
                
                if self.ghostlang_transport:
                    self.ghostlang_transport.send_mesh_command(peer_node_id, response)
                
                logger.debug(f"[OMNI] Sent {len(ops_data)} ops to {peer_node_id[:12]} via GhostLang")
                
            elif cmd_type == 'sync_response':
                # Apply received ops
                ops_data = message.get('ops', [])
                for op_data in ops_data:
                    op = StateOp.from_dict(op_data)
                    if op.node_id != self.node_id:
                        self.state_model.apply_op(op)
                
                logger.debug(f"[OMNI] Applied {len(ops_data)} ops from GhostLang")
                
            elif cmd_type == 'peer_announce':
                # Peer announcing itself via GhostLang
                peer_node_id = message.get('node_id')
                peer_ip = message.get('ip')
                peer_port = message.get('port', self.mesh_port)
                
                with self.lock:
                    self.peers[peer_node_id] = NodeInfo(
                        node_id=peer_node_id,
                        ip=peer_ip,
                        port=peer_port,
                        platform=message.get('platform', 'unknown'),
                        capabilities=[],
                        last_seen=time.time()
                    )
                
                logger.info(f"[OMNI] Peer {peer_node_id[:12]} announced via GhostLang")
                
        except Exception as e:
            logger.error(f"[OMNI] Failed to handle GhostLang message: {e}")
    
    def _recover_state_store(self):
        """Recover from state store corruption"""
        logger.info("[OMNI] Initiating state store recovery...")
        try:
            # State store has built-in recovery
            # Just reinitialize
            self.state_store = get_state_store(db_path=self.config['state_db_path'])
            self.state_model = get_state_model(state_store=self.state_store)
            logger.info("[OMNI] State store recovery complete")
        except Exception as e:
            logger.error(f"[OMNI] Recovery failed: {e}")
    
    def start(self):
        """Start OMNI core"""
        if self.running:
            logger.warning("[OMNI] Already running")
            return True
        
        logger.info("[OMNI] Starting OMNI core...")
        self.running = True
        
        if not self.initialize():
            logger.error("[OMNI] Failed to initialize")
            self.running = False
            return False
        
        logger.info("[OMNI] ✅ OMNI core running")
        logger.info(f"[OMNI] Node ID: {self.node_id}")
        logger.info(f"[OMNI] Platform: {self.config['platform']}")
        logger.info(f"[OMNI] IP: {self.config['local_ip']}:{self.mesh_port}")
        logger.info(f"[OMNI] Status: {self.status.value}")
        return True
    
    def stop(self):
        """Stop OMNI core"""
        logger.info("[OMNI] Stopping...")
        self.running = False
        self.discovery_running = False
        self.sync_running = False
        self.mesh_listener_running = False
        
        # Stop enhanced auto-discovery
        if self.auto_discovery:
            self.auto_discovery.stop()
        
        # Stop adapter manager
        if self.adapter_manager:
            self.adapter_manager.stop_all()
        
        # Stop recovery engine
        if self.recovery_engine:
            self.recovery_engine.stop()
        
        # Stop sync engine
        if self.sync_engine:
            self.sync_engine.stop()
        
        if self.mesh_socket:
            try:
                self.mesh_socket.close()
            except:
                pass
        
        if self.state_store:
            self.state_store.close()
        
        logger.info("[OMNI] ✅ Stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        with self.lock:
            return {
                'node_id': self.node_id,
                'status': self.status.value,
                'platform': self.config['platform'],
                'ip': self.config['local_ip'],
                'port': self.mesh_port,
                'peers': len(self.peers),
                'is_master': self.is_master,
                'master_node_id': self.master_node_id,
                'state_keys': len(self.state_model.state) if self.state_model else 0,
            }
    
    def get_peers(self) -> List[Dict[str, Any]]:
        """Get list of peers"""
        with self.lock:
            return [
                {
                    'node_id': peer.node_id,
                    'ip': peer.ip,
                    'port': peer.port,
                    'platform': peer.platform,
                    'last_seen': peer.last_seen,
                    'health_score': peer.health_score
                }
                for peer in self.peers.values()
            ]


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OMNI Core - Unified Orchestrator')
    parser.add_argument('--config', help='Path to config file')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    args = parser.parse_args()
    
    core = OmniCore(config_path=args.config)
    
    if args.status:
        core.start()
        time.sleep(2)  # Give it time to initialize
        status = core.get_status()
        print(json.dumps(status, indent=2))
        core.stop()
        return
    
    # Start and run
    core.start()
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[OMNI] Shutting down...")
        core.stop()


if __name__ == "__main__":
    main()
