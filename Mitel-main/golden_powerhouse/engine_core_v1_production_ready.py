# engine_core.py
# G.Legion Framework - Engine Core (Production Ready)

import asyncio
import logging
import sys
import os
import yaml
import json
import signal
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from enum import Enum
# Global logger setup
logger = logging.getLogger("G.Legion.Core")

class GhostSubsystem:
    """Base class for all Ghost Engine subsystems"""
    def __init__(self, name: str):
        self.name = name
        self.event_bus = None
        self.config = {}
        self.logger = logging.getLogger(f"G.Legion.{name}")
        
    async def initialize(self):
        pass
        
    async def start(self):
        pass
        
    async def stop(self):
        pass
# Import SP-SUB (Synchronization Protocol Subsystem)
from sp_subsystem_v5_complete import EnhancedGhostSyncProtocol, SPEventBusIntegration

# Attempt to import other subsystems if available
try:
    from session_control_subsystem import SessionControlSubsystem
    SC_SUB_AVAILABLE = True
except ImportError:
    SC_SUB_AVAILABLE = False

try:
    from event_bus_subsystem import EventBusSubsystem
    EB_SUB_AVAILABLE = True
except ImportError:
    EB_SUB_AVAILABLE = False

try:
    from auth_subsystem import AuthSubsystem
    AUTH_SUB_AVAILABLE = True
except ImportError:
    AUTH_SUB_AVAILABLE = False

try:
    from security_subsystem import SecuritySubsystem
    SEC_SUB_AVAILABLE = True
except ImportError:
    SEC_SUB_AVAILABLE = False

try:
    from advanced_operations_subsystem import AOSubsystem
    AO_SUB_AVAILABLE = True
except ImportError:
    AO_SUB_AVAILABLE = False

# Global logger setup
logger = logging.getLogger("G.Legion.Core")

class SubsystemState(Enum):
    """Enum for tracking subsystem states"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class SimpleEventBus:
    """Simple internal event bus implementation when EB-SUB isn't available"""
    
    def __init__(self):
        self.subscribers = {}
        self.logger = logging.getLogger("G.Legion.SimpleEventBus")
        self.running = False
    
    def subscribe(self, event_type: str, callback):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = set()
        self.subscribers[event_type].add(callback)
        return lambda: self.subscribers[event_type].discard(callback)
    
    async def publish(self, event_type: str, event_data: Dict):
        """Publish an event to subscribers"""
        if not self.running:
            return
            
        callbacks = self.subscribers.get(event_type, set())
        for callback in list(callbacks):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_data)
                else:
                    callback(event_data)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event_type}: {e}")
    
    async def initialize(self):
        """Initialize the event bus"""
        self.logger.info("Simple Event Bus initializing")
    
    async def start(self):
        """Start the event bus"""
        self.running = True
        self.logger.info("Simple Event Bus started")
    
    async def stop(self):
        """Stop the event bus"""
        self.running = False
        self.subscribers.clear()
        self.logger.info("Simple Event Bus stopped")

class EngineCore:
    """G.Legion Engine Core - Main runtime environment"""
    
    def __init__(self, config_path: str = "config/engine_config.yaml"):
        self.config_path = config_path
        self.config = {}
        self.node_id = None
        self.start_time = datetime.now()
        
        # Subsystem registry
        self.subsystems = {}
        self.subsystem_states = {}
        
        # Event bus (central communication)
        self.event_bus = None
        
        # Runtime state
        self.running = False
        self.shutdown_requested = False
        self._shutdown_event = asyncio.Event()
        
        # Health monitoring
        self.health_check_interval = 30
        self.last_health_check = None
        
        # Performance metrics
        self.metrics = {
            'total_events': 0,
            'errors': 0,
            'subsystem_restarts': 0
        }
    
    async def initialize(self):
        """Initialize the engine core and all subsystems"""
        try:
            logger.info("G.Legion Engine Core initializing...")
            
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Load configuration
            await self._load_config()
            
            # Setup node ID
            self._setup_node_id()
            
            # Setup signal handlers
            self._setup_signal_handlers()
            
            logger.info(f"G.Legion Engine Core initializing (node: {self.node_id})")
            
            # Initialize Event Bus first if available
            await self._init_event_bus()
            
            # Initialize subsystems
            await self._init_subsystems()
            
            logger.info("G.Legion Engine Core initialization complete")
            
        except Exception as e:
            logger.error(f"Engine core initialization failed: {e}", exc_info=True)
            raise
    
    async def _load_config(self):
        """Load engine configuration"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {self.config_path}, creating default")
                # Create default config
                default_config = {
                    "engine": {
                        "name": "G.Legion Ghost Engine",
                        "version": "1.0.0",
                        "log_level": "INFO",
                        "health_check_interval": 30,
                        "max_restart_attempts": 3
                    },
                    "subsystems": {
                        "sp_sub": {
                            "enabled": True,
                            "config_path": "config/sp_config.yaml",
                            "critical": True
                        },
                        "sc_sub": {
                            "enabled": SC_SUB_AVAILABLE,
                            "config_path": "config/sc_config.yaml",
                            "critical": False
                        },
                        "eb_sub": {
                            "enabled": EB_SUB_AVAILABLE,
                            "config_path": "config/eb_config.yaml",
                            "critical": False
                        },
                        "auth_sub": {
                            "enabled": AUTH_SUB_AVAILABLE,
                            "config_path": "config/auth_config.yaml",
                            "critical": False
                        },
                        "sec_sub": {
                            "enabled": SEC_SUB_AVAILABLE,
                            "config_path": "config/sec_config.yaml",
                            "critical": False
                        },
                        "ao_sub": {
                            "enabled": AO_SUB_AVAILABLE,
                            "config_path": "config/ao_config.yaml",
                            "critical": False
                        }
                    },
                    "node": {
                        "id": None,  # Will be auto-generated if not set
                        "persistent_id": True
                    },
                    "monitoring": {
                        "enabled": True,
                        "metrics_interval": 60,
                        "log_metrics": True
                    }
                }
                
                # Create config directory if it doesn't exist
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                
                with open(config_file, 'w') as f:
                    yaml.dump(default_config, f, default_flow_style=False)
                
                self.config = default_config
            else:
                with open(config_file, 'r') as f:
                    self.config = yaml.safe_load(f)
                
            logger.info(f"Configuration loaded from {self.config_path}")
            
            # Ensure required configuration sections exist
            if 'engine' not in self.config:
                self.config['engine'] = {}
            if 'subsystems' not in self.config:
                self.config['subsystems'] = {}
            if 'node' not in self.config:
                self.config['node'] = {}
            if 'monitoring' not in self.config:
                self.config['monitoring'] = {}
            
            # Update health check interval from config
            self.health_check_interval = self.config.get('engine', {}).get('health_check_interval', 30)
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}", exc_info=True)
            raise
    
    def _setup_node_id(self):
        """Set up unique node identifier"""
        # Try to get node ID from config
        node_config = self.config.get('node', {})
        self.node_id = node_config.get('id')
        
        # If not configured, check if we have a persisted one
        if not self.node_id and node_config.get('persistent_id', True):
            node_id_file = Path("config/node_id")
            if node_id_file.exists():
                try:
                    self.node_id = node_id_file.read_text().strip()
                except:
                    pass
        
        # Generate a new one if needed
        if not self.node_id:
            self.node_id = f"ghost-{str(uuid.uuid4())[:8]}"
            logger.info(f"Generated new node ID: {self.node_id}")
            
            # Persist if configured
            if node_config.get('persistent_id', True):
                try:
                    os.makedirs("config", exist_ok=True)
                    with open("config/node_id", 'w') as f:
                        f.write(self.node_id)
                except Exception as e:
                    logger.warning(f"Failed to persist node ID: {e}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.shutdown_requested = True
            self._shutdown_event.set()
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except Exception as e:
            logger.warning(f"Could not setup signal handlers: {e}")
    
    async def _init_event_bus(self):
        """Initialize the event bus subsystem"""
        if not EB_SUB_AVAILABLE:
            # Create a simple internal event bus
            self.event_bus = SimpleEventBus()
            await self.event_bus.initialize()
            logger.info("Using internal simple event bus")
            return
        
        try:
            eb_config = self.config.get('subsystems', {}).get('eb_sub', {})
            if not eb_config.get('enabled', True):
                # Create a simple internal event bus
                self.event_bus = SimpleEventBus()
                await self.event_bus.initialize()
                logger.info("Using internal simple event bus (EB-SUB disabled)")
                return
            
            # Create EB-SUB configuration if not present
            eb_config_path = eb_config.get('config_path', 'config/eb_config.yaml')
            if not os.path.exists(eb_config_path):
                # Create default EB-SUB config
                eb_default_config = {
                    "max_events_per_second": 1000,
                    "max_subscribers": 100,
                    "event_retention_seconds": 3600,
                    "persistent_events": False,
                    "compression": False
                }
                
                os.makedirs(os.path.dirname(eb_config_path), exist_ok=True)
                with open(eb_config_path, 'w') as f:
                    yaml.dump(eb_default_config, f)
                logger.info(f"Created default EB-SUB config at {eb_config_path}")
            
            # Initialize Event Bus Subsystem
            self.event_bus = EventBusSubsystem(eb_config_path)
            await self.event_bus.initialize()
            
            # Register with subsystems
            self.subsystems['eb_sub'] = self.event_bus
            self.subsystem_states['eb_sub'] = SubsystemState.READY
            
            logger.info("Event Bus Subsystem initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Event Bus: {e}", exc_info=True)
            # Fall back to simple internal event bus
            self.event_bus = SimpleEventBus()
            await self.event_bus.initialize()
            logger.info("Using internal simple event bus (fallback)")
    
    async def _init_subsystems(self):
        """Initialize all required subsystems"""
        subsystem_configs = self.config.get('subsystems', {})
        
        # Initialize subsystems in dependency order
        initialization_order = [
            ('sp_sub', self._init_sp_subsystem),
            ('sc_sub', self._init_sc_subsystem),
            ('auth_sub', self._init_auth_subsystem),
            ('sec_sub', self._init_sec_subsystem),
            ('ao_sub', self._init_ao_subsystem)
        ]
        
        for subsystem_name, init_func in initialization_order:
            config = subsystem_configs.get(subsystem_name, {})
            try:
                await init_func(config)
            except Exception as e:
                logger.error(f"Failed to initialize {subsystem_name}: {e}", exc_info=True)
                # Mark as error but continue with other subsystems
                self.subsystem_states[subsystem_name] = SubsystemState.ERROR
                
                # If it's a critical subsystem, we should fail
                if config.get('critical', False):
                    raise Exception(f"Critical subsystem {subsystem_name} failed to initialize")
    
    async def _init_sp_subsystem(self, config: Dict):
        """Initialize Synchronization Protocol Subsystem"""
        if not config.get('enabled', True):
            logger.info("SP-SUB disabled in configuration")
            return
        
        try:
            # Create SP-SUB configuration if not present
            sp_config_path = config.get('config_path', 'config/sp_config.yaml')
            if not os.path.exists(sp_config_path):
                # Create default SP-SUB config
                sp_config = {
                    "sync": {
                        "interval_seconds": 300,
                        "batch_size": 100,
                        "max_retries": 3,
                        "timeout_seconds": 30,
                        "offline_mode": True,
                        "compression_enabled": True,
                        "encryption_enabled": True
                    },
                    "protocol": {
                        "mode": "mesh",
                        "listen_port": 8443,
                        "discovery_port": 8444,
                        "offline_first": True,
                        "max_connections": 50,
                        "heartbeat_interval": 60
                    },
                    "storage": {
                        "data_dir": "data/sp_sub",
                        "max_storage_mb": 1024,
                        "cleanup_interval": 3600
                    }
                }
                
                os.makedirs(os.path.dirname(sp_config_path), exist_ok=True)
                with open(sp_config_path, 'w') as f:
                    yaml.dump(sp_config, f, default_flow_style=False)
                logger.info(f"Created default SP-SUB config at {sp_config_path}")
            
            # Load SP-SUB config
            with open(sp_config_path, 'r') as f:
                sp_config = yaml.safe_load(f)
            
            # Update subsystem state
            self.subsystem_states['sp_sub'] = SubsystemState.INITIALIZING
            
            # Initialize SP-SUB protocol
            self.subsystems['sp_sub'] = EnhancedGhostSyncProtocol(sp_config, self.node_id)
            
            # Connect SP-SUB to Event Bus if available
            if self.event_bus:
                sp_events = SPEventBusIntegration(self.subsystems['sp_sub'], self.event_bus)
                await sp_events.initialize()
                logger.info("SP-SUB connected to Event Bus")
            
            self.subsystem_states['sp_sub'] = SubsystemState.READY
            logger.info("SP-SUB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SP-SUB: {e}", exc_info=True)
            self.subsystem_states['sp_sub'] = SubsystemState.ERROR
            raise
    
    async def _init_sc_subsystem(self, config: Dict):
        """Initialize Session Control Subsystem"""
        if not SC_SUB_AVAILABLE or not config.get('enabled', True):
            logger.info("SC-SUB not available or disabled")
            return
        
        try:
            # Create SC-SUB configuration if not present
            sc_config_path = config.get('config_path', 'config/sc_config.yaml')
            if not os.path.exists(sc_config_path):
                # Create default SC-SUB config
                sc_config = {
                    "max_sessions": 10000,
                    "session_timeout": 3600,
                    "max_user_sessions": 5,
                    "cleanup_interval": 300,
                    "monitoring_enabled": True,
                    "anomaly_thresholds": {
                        "max_requests": 1000,
                        "max_error_rate": 0.1,
                        "max_data_transfer": 100000000
                    },
                    "auth_providers": ["local"],
                    "storage": {
                        "type": "memory",
                        "persistent": False
                    }
                }
                
                os.makedirs(os.path.dirname(sc_config_path), exist_ok=True)
                with open(sc_config_path, 'w') as f:
                    yaml.dump(sc_config, f, default_flow_style=False)
                logger.info(f"Created default SC-SUB config at {sc_config_path}")
            
            # Load SC-SUB config
            with open(sc_config_path, 'r') as f:
                sc_config = yaml.safe_load(f)
            
            # Update subsystem state
            self.subsystem_states['sc_sub'] = SubsystemState.INITIALIZING
            
            # Initialize SC-SUB
            self.subsystems['sc_sub'] = SessionControlSubsystem(sc_config)
            
            self.subsystem_states['sc_sub'] = SubsystemState.READY
            logger.info("SC-SUB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SC-SUB: {e}", exc_info=True)
            self.subsystem_states['sc_sub'] = SubsystemState.ERROR
    
    async def _init_auth_subsystem(self, config: Dict):
        """Initialize Authentication Subsystem"""
        if not AUTH_SUB_AVAILABLE or not config.get('enabled', True):
            logger.info("AUTH-SUB not available or disabled")
            return
        
        try:
            # Create AUTH-SUB configuration if not present
            auth_config_path = config.get('config_path', 'config/auth_config.yaml')
            if not os.path.exists(auth_config_path):
                auth_config = {
                    "providers": ["local"],
                    "token_expiry": 3600,
                    "max_login_attempts": 5,
                    "lockout_duration": 300,
                    "password_policy": {
                        "min_length": 8,
                        "require_uppercase": True,
                        "require_lowercase": True,
                        "require_numbers": True,
                        "require_symbols": False
                    },
                    "encryption": {
                        "algorithm": "bcrypt",
                        "rounds": 12
                    },
                    "session_management": {
                        "concurrent_sessions": 3,
                        "idle_timeout": 1800
                    }
                }
                
                os.makedirs(os.path.dirname(auth_config_path), exist_ok=True)
                with open(auth_config_path, 'w') as f:
                    yaml.dump(auth_config, f, default_flow_style=False)
                logger.info(f"Created default AUTH-SUB config at {auth_config_path}")
            
            self.subsystem_states['auth_sub'] = SubsystemState.INITIALIZING
            self.subsystems['auth_sub'] = AuthSubsystem(auth_config_path)
            self.subsystem_states['auth_sub'] = SubsystemState.READY
            logger.info("AUTH-SUB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AUTH-SUB: {e}", exc_info=True)
            self.subsystem_states['auth_sub'] = SubsystemState.ERROR
    
    async def _init_sec_subsystem(self, config: Dict):
        """Initialize Security Subsystem"""
        if not SEC_SUB_AVAILABLE or not config.get('enabled', True):
            logger.info("SEC-SUB not available or disabled")
            return
        
        try:
            # Create SEC-SUB configuration if not present
            sec_config_path = config.get('config_path', 'config/sec_config.yaml')
            if not os.path.exists(sec_config_path):
                sec_config = {
                    "encryption": {
                        "default_algorithm": "AES-256-GCM",
                        "key_rotation_interval": 86400,
                        "secure_key_storage": True
                    },
                    "access_control": {
                        "default_policy": "deny",
                        "audit_enabled": True,
                        "rate_limiting": {
                            "enabled": True,
                            "requests_per_minute": 60
                        }
                    },
                    "threat_detection": {
                        "enabled": True,
                        "anomaly_threshold": 0.8,
                        "quarantine_suspicious": True
                    },
                    "compliance": {
                        "standards": ["ISO27001", "SOC2"],
                        "audit_retention_days": 365
                    }
                }
                
                os.makedirs(os.path.dirname(sec_config_path), exist_ok=True)
                with open(sec_config_path, 'w') as f:
                    yaml.dump(sec_config, f, default_flow_style=False)
                logger.info(f"Created default SEC-SUB config at {sec_config_path}")
            
            self.subsystem_states['sec_sub'] = SubsystemState.INITIALIZING
            self.subsystems['sec_sub'] = SecuritySubsystem(sec_config_path)
            self.subsystem_states['sec_sub'] = SubsystemState.READY
            logger.info("SEC-SUB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SEC-SUB: {e}", exc_info=True)
            self.subsystem_states['sec_sub'] = SubsystemState.ERROR
    
    async def _init_ao_subsystem(self, config: Dict):
        """Initialize Advanced Operations Subsystem"""
        if not AO_SUB_AVAILABLE or not config.get('enabled', True):
            logger.info("AO-SUB not available or disabled")
            return
        
        try:
            # Create AO-SUB configuration if not present
            ao_config_path = config.get('config_path', 'config/ao_config.yaml')
            if not os.path.exists(ao_config_path):
                ao_config = {
                    "operations": {
                        "max_concurrent": 10,
                        "timeout_seconds": 300,
                        "retry_attempts": 3,
                        "queue_size": 1000
                    },
                    "automation": {
                        "enabled": True,
                        "schedule_check_interval": 60,
                        "max_automated_operations": 50
                    },
                    "analytics": {
                        "enabled": True,
                        "data_retention_days": 30,
                        "performance_monitoring": True
                    },
                    "integrations": {
                        "external_apis": [],
                        "webhooks_enabled": False,
                        "notification_channels": []
                    }
                }
                
                os.makedirs(os.path.dirname(ao_config_path), exist_ok=True)
                with open(ao_config_path, 'w') as f:
                    yaml.dump(ao_config, f, default_flow_style=False)
                logger.info(f"Created default AO-SUB config at {ao_config_path}")
            
            self.subsystem_states['ao_sub'] = SubsystemState.INITIALIZING
            self.subsystems['ao_sub'] = AOSubsystem(ao_config_path)
            self.subsystem_states['ao_sub'] = SubsystemState.READY
            logger.info("AO-SUB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AO-SUB: {e}", exc_info=True)
            self.subsystem_states['ao_sub'] = SubsystemState.ERROR
    
    async def start(self):
        """Start the engine core and all subsystems"""
        if self.running:
            logger.warning("Engine core already running")
            return
        
        logger.info("Starting G.Legion Engine Core...")
        
        # Start Event Bus first if available
        if 'eb_sub' in self.subsystems:
            try:
                self.subsystem_states['eb_sub'] = SubsystemState.STARTING
                await self.subsystems['eb_sub'].start()
                self.subsystem_states['eb_sub'] = SubsystemState.RUNNING
                logger.info("Event Bus Subsystem started")
            except Exception as e:
                logger.error(f"Failed to start Event Bus: {e}", exc_info=True)
                self.subsystem_states['eb_sub'] = SubsystemState.ERROR
        else:
            # Start simple event bus
            if self.event_bus:
                await self.event_bus.start()
        
        # Start subsystems in order
        startup_order = ['sp_sub', 'sc_sub', 'auth_sub', 'sec_sub', 'ao_sub']
        
        for subsystem_name in startup_order:
            if subsystem_name in self.subsystems:
                try:
                    self.subsystem_states[subsystem_name] = SubsystemState.STARTING
                    await self.subsystems[subsystem_name].start()
                    self.subsystem_states[subsystem_name] = SubsystemState.RUNNING
                    logger.info(f"{subsystem_name.upper()} started")
                except Exception as e:
                    logger.error(f"Failed to start {subsystem_name}: {e}", exc_info=True)
                    self.subsystem_states[subsystem_name] = SubsystemState.ERROR
                    
                    # Check if it's critical
                    subsystem_config = self.config.get('subsystems', {}).get(subsystem_name, {})
                    if subsystem_config.get('critical', False):
                        raise Exception(f"Critical subsystem {subsystem_name} failed to start")
        
        self.running = True
        self.start_time = datetime.now()
        
        # Publish startup event
        if self.event_bus:
            await self.event_bus.publish('engine.started', {
                'node_id': self.node_id,
                'timestamp': self.start_time.isoformat(),
                'subsystems': list(self.subsystems.keys())
            })
        
        logger.info("G.Legion Engine Core started successfully")
    
    async def stop(self):
        """Stop all subsystems gracefully"""
        if not self.running:
            logger.warning("Engine core not running")
            return
        
        logger.info("Stopping G.Legion Engine Core...")
        self.shutdown_requested = True
        self.running = False
        
        # Publish shutdown event
        if self.event_bus and self.event_bus.running:
            try:
                await self.event_bus.publish('engine.stopping', {
                    'node_id': self.node_id,
                    'timestamp': datetime.now().isoformat(),
                    'uptime': (datetime.now() - self.start_time).total_seconds()
                })
            except Exception as e:
                logger.warning(f"Failed to publish shutdown event: {e}")
        
        # Stop subsystems in reverse order
        shutdown_order = ['ao_sub', 'sec_sub', 'auth_sub', 'sc_sub', 'sp_sub', 'eb_sub']
        
        for subsystem_name in shutdown_order:
            if subsystem_name in self.subsystems:
                try:
                    self.subsystem_states[subsystem_name] = SubsystemState.STOPPING
                    if hasattr(self.subsystems[subsystem_name], 'stop'):
                        await self.subsystems[subsystem_name].stop()
                    self.subsystem_states[subsystem_name] = SubsystemState.STOPPED
                    logger.info(f"{subsystem_name.upper()} stopped")
                except Exception as e:
                    logger.error(f"Error stopping {subsystem_name}: {e}", exc_info=True)
                    self.subsystem_states[subsystem_name] = SubsystemState.ERROR
        
        # Stop event bus last
        if self.event_bus:
            try:
                await self.event_bus.stop()
            except Exception as e:
                logger.error(f"Error stopping event bus: {e}", exc_info=True)
        
        logger.info("G.Legion Engine Core stopped")
    
    async def run(self):
        """Main runtime loop"""
        logger.info("G.Legion Engine Core entering main loop")
        
        try:
            while self.running and not self.shutdown_requested:
                # Basic health check and monitoring
                await self._health_check()
                
                # Log metrics periodically
                monitoring_config = self.config.get('monitoring', {})
                if monitoring_config.get('log_metrics', True):
                    await self._log_metrics()
                
                # Wait for shutdown signal or timeout
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(), 
                        timeout=self.health_check_interval
                    )
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    pass  # Continue monitoring loop
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Runtime error: {e}", exc_info=True)
            self.metrics['errors'] += 1
        finally:
            await self.stop()
    
    async def _health_check(self):
        """Perform basic health checks on subsystems"""
        self.last_health_check = datetime.now()
        
        for name, subsystem in self.subsystems.items():
            state = self.subsystem_states.get(name, SubsystemState.UNINITIALIZED)
            
            if state == SubsystemState.ERROR:
                logger.warning(f"Subsystem {name} in error state")
                # Attempt restart if configured
                max_restarts = self.config.get('engine', {}).get('max_restart_attempts', 3)
                if self.metrics['subsystem_restarts'] < max_restarts:
                    logger.info(f"Attempting to restart {name}")
                    try:
                        if hasattr(subsystem, 'start'):
                            self.subsystem_states[name] = SubsystemState.STARTING
                            await subsystem.start()
                            self.subsystem_states[name] = SubsystemState.RUNNING
                            self.metrics['subsystem_restarts'] += 1
                            logger.info(f"Successfully restarted {name}")
                    except Exception as e:
                        logger.error(f"Failed to restart {name}: {e}")
                        self.subsystem_states[name] = SubsystemState.ERROR
            
            elif state == SubsystemState.RUNNING:
                # Optionally perform deeper health checks here
                if hasattr(subsystem, 'health_check'):
                    try:
                        health = await subsystem.health_check()
                        if not health:
                            logger.warning(f"Health check failed for {name}")
                    except Exception as e:
                        logger.warning(f"Health check error for {name}: {e}")
    
    async def _log_metrics(self):
        """Log performance metrics"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        metrics_data = {
            'node_id': self.node_id,
            'uptime': uptime,
            'subsystems_running': len([s for s in self.subsystem_states.values() 
                                     if s == SubsystemState.RUNNING]),
            'subsystems_error': len([s for s in self.subsystem_states.values() 
                                   if s == SubsystemState.ERROR]),
            'total_events': self.metrics['total_events'],
            'errors': self.metrics['errors'],
            'restarts': self.metrics['subsystem_restarts']
        }
        
        logger.info(f"Engine metrics: {json.dumps(metrics_data)}")
        
        # Publish metrics event
        if self.event_bus:
            await self.event_bus.publish('engine.metrics', metrics_data)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            "node_id": self.node_id,
            "running": self.running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "subsystems": {
                name: {
                    "state": state.value,
                    "available": name in self.subsystems
                }
                for name, state in self.subsystem_states.items()
            },
            "metrics": self.metrics.copy(),
            "config_loaded": bool(self.config)
        }
    
    async def restart_subsystem(self, subsystem_name: str) -> bool:
        """Restart a specific subsystem"""
        if subsystem_name not in self.subsystems:
            logger.error(f"Subsystem {subsystem_name} not found")
            return False
        
        try:
            logger.info(f"Restarting subsystem {subsystem_name}")
            
            # Stop the subsystem
            self.subsystem_states[subsystem_name] = SubsystemState.STOPPING
            if hasattr(self.subsystems[subsystem_name], 'stop'):
                await self.subsystems[subsystem_name].stop()
            
            # Start the subsystem
            self.subsystem_states[subsystem_name] = SubsystemState.STARTING
            await self.subsystems[subsystem_name].start()
            self.subsystem_states[subsystem_name] = SubsystemState.RUNNING
            
            logger.info(f"Successfully restarted {subsystem_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart {subsystem_name}: {e}", exc_info=True)
            self.subsystem_states[subsystem_name] = SubsystemState.ERROR
            return False

async def main():
    """Main entry point for G.Legion Engine Core"""
    # Setup logging
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/engine_core.log', 'a') if os.path.exists('logs') or os.makedirs('logs', exist_ok=True) else logging.StreamHandler()
        ]
    )
    
    # Create and run engine
    config_path = os.environ.get('ENGINE_CONFIG', 'config/engine_config.yaml')
    engine = EngineCore(config_path)
    
    try:
        await engine.initialize()
        await engine.start()
        await engine.run()
    except Exception as e:
        logger.error(f"Engine startup failed: {e}", exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        try:
            await engine.stop()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
