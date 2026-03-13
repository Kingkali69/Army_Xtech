#!/usr/bin/env python3
"""
GhostHUD Mesh Network - Configuration Management
Centralized configuration system with environment variable support
"""

import os
from pathlib import Path
from typing import Optional, Any, Dict
from dataclasses import dataclass, field
import json
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)


@dataclass
class NodeConfig:
    """Node-specific configuration"""
    node_id: Optional[str] = None
    host: str = '0.0.0.0'
    port: int = 5000
    secret_key: Optional[str] = None
    debug: bool = False


@dataclass
class NetworkConfig:
    """Network configuration"""
    discovery_enabled: bool = True
    discovery_port: int = 45678
    discovery_interval: int = 30
    peer_timeout: int = 120
    master_heartbeat_interval: int = 10


@dataclass
class SecurityConfig:
    """Security configuration"""
    jwt_enabled: bool = True
    jwt_algorithm: str = 'HS256'
    jwt_expiration: int = 3600
    encryption_enabled: bool = True
    tls_enabled: bool = False
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = 'INFO'
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    file_path: Optional[str] = None
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class StorageConfig:
    """Data storage configuration"""
    backend: str = 'memory'  # memory, redis, sqlite
    redis_host: Optional[str] = None
    redis_port: Optional[int] = None
    sqlite_path: Optional[str] = None
    sync_enabled: bool = True


@dataclass
class Config:
    """Main configuration container"""
    node: NodeConfig = field(default_factory=NodeConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)

    @classmethod
    def from_env(cls) -> 'Config':
        """
        Load configuration from environment variables

        Returns:
            Config instance with values from environment
        """
        config = cls()

        # Node configuration
        config.node.node_id = os.getenv('NODE_ID')
        config.node.host = os.getenv('NODE_HOST', '0.0.0.0')
        config.node.port = int(os.getenv('NODE_PORT', '5000'))
        config.node.secret_key = os.getenv('SECRET_KEY')
        config.node.debug = os.getenv('DEBUG', 'false').lower() == 'true'

        # Network configuration
        config.network.discovery_enabled = os.getenv('DISCOVERY_ENABLED', 'true').lower() == 'true'
        config.network.discovery_port = int(os.getenv('DISCOVERY_PORT', '45678'))
        config.network.discovery_interval = int(os.getenv('DISCOVERY_INTERVAL', '30'))
        config.network.peer_timeout = int(os.getenv('PEER_TIMEOUT', '120'))
        config.network.master_heartbeat_interval = int(os.getenv('MASTER_HEARTBEAT_INTERVAL', '10'))

        # Security configuration
        config.security.jwt_enabled = os.getenv('JWT_ENABLED', 'true').lower() == 'true'
        config.security.jwt_algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        config.security.jwt_expiration = int(os.getenv('JWT_EXPIRATION', '3600'))
        config.security.encryption_enabled = os.getenv('ENCRYPTION_ENABLED', 'true').lower() == 'true'
        config.security.tls_enabled = os.getenv('TLS_ENABLED', 'false').lower() == 'true'
        config.security.tls_cert_path = os.getenv('TLS_CERT_PATH')
        config.security.tls_key_path = os.getenv('TLS_KEY_PATH')

        # Logging configuration
        config.logging.level = os.getenv('LOG_LEVEL', 'INFO')
        config.logging.format = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        config.logging.file_path = os.getenv('LOG_FILE_PATH')
        config.logging.max_bytes = int(os.getenv('LOG_MAX_BYTES', '10485760'))
        config.logging.backup_count = int(os.getenv('LOG_BACKUP_COUNT', '5'))

        # Storage configuration
        config.storage.backend = os.getenv('STORAGE_BACKEND', 'memory')
        config.storage.redis_host = os.getenv('REDIS_HOST')
        config.storage.redis_port = int(os.getenv('REDIS_PORT', '6379')) if os.getenv('REDIS_PORT') else None
        config.storage.sqlite_path = os.getenv('SQLITE_PATH')
        config.storage.sync_enabled = os.getenv('STORAGE_SYNC_ENABLED', 'true').lower() == 'true'

        return config

    @classmethod
    def from_file(cls, file_path: str) -> 'Config':
        """
        Load configuration from a JSON file

        Args:
            file_path: Path to the configuration file

        Returns:
            Config instance with values from file
        """
        with open(file_path, 'r') as f:
            data = json.load(f)

        config = cls()

        # Node configuration
        if 'node' in data:
            node_data = data['node']
            config.node.node_id = node_data.get('node_id')
            config.node.host = node_data.get('host', '0.0.0.0')
            config.node.port = node_data.get('port', 5000)
            config.node.secret_key = node_data.get('secret_key')
            config.node.debug = node_data.get('debug', False)

        # Network configuration
        if 'network' in data:
            net_data = data['network']
            config.network.discovery_enabled = net_data.get('discovery_enabled', True)
            config.network.discovery_port = net_data.get('discovery_port', 45678)
            config.network.discovery_interval = net_data.get('discovery_interval', 30)
            config.network.peer_timeout = net_data.get('peer_timeout', 120)
            config.network.master_heartbeat_interval = net_data.get('master_heartbeat_interval', 10)

        # Security configuration
        if 'security' in data:
            sec_data = data['security']
            config.security.jwt_enabled = sec_data.get('jwt_enabled', True)
            config.security.jwt_algorithm = sec_data.get('jwt_algorithm', 'HS256')
            config.security.jwt_expiration = sec_data.get('jwt_expiration', 3600)
            config.security.encryption_enabled = sec_data.get('encryption_enabled', True)
            config.security.tls_enabled = sec_data.get('tls_enabled', False)
            config.security.tls_cert_path = sec_data.get('tls_cert_path')
            config.security.tls_key_path = sec_data.get('tls_key_path')

        # Logging configuration
        if 'logging' in data:
            log_data = data['logging']
            config.logging.level = log_data.get('level', 'INFO')
            config.logging.format = log_data.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            config.logging.file_path = log_data.get('file_path')
            config.logging.max_bytes = log_data.get('max_bytes', 10485760)
            config.logging.backup_count = log_data.get('backup_count', 5)

        # Storage configuration
        if 'storage' in data:
            storage_data = data['storage']
            config.storage.backend = storage_data.get('backend', 'memory')
            config.storage.redis_host = storage_data.get('redis_host')
            config.storage.redis_port = storage_data.get('redis_port')
            config.storage.sqlite_path = storage_data.get('sqlite_path')
            config.storage.sync_enabled = storage_data.get('sync_enabled', True)

        return config

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary

        Returns:
            Dictionary representation of the configuration
        """
        return {
            'node': {
                'node_id': self.node.node_id,
                'host': self.node.host,
                'port': self.node.port,
                'secret_key': self.node.secret_key,
                'debug': self.node.debug
            },
            'network': {
                'discovery_enabled': self.network.discovery_enabled,
                'discovery_port': self.network.discovery_port,
                'discovery_interval': self.network.discovery_interval,
                'peer_timeout': self.network.peer_timeout,
                'master_heartbeat_interval': self.network.master_heartbeat_interval
            },
            'security': {
                'jwt_enabled': self.security.jwt_enabled,
                'jwt_algorithm': self.security.jwt_algorithm,
                'jwt_expiration': self.security.jwt_expiration,
                'encryption_enabled': self.security.encryption_enabled,
                'tls_enabled': self.security.tls_enabled,
                'tls_cert_path': self.security.tls_cert_path,
                'tls_key_path': self.security.tls_key_path
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_path': self.logging.file_path,
                'max_bytes': self.logging.max_bytes,
                'backup_count': self.logging.backup_count
            },
            'storage': {
                'backend': self.storage.backend,
                'redis_host': self.storage.redis_host,
                'redis_port': self.storage.redis_port,
                'sqlite_path': self.storage.sqlite_path,
                'sync_enabled': self.storage.sync_enabled
            }
        }

    def to_file(self, file_path: str):
        """
        Save configuration to a JSON file

        Args:
            file_path: Path to save the configuration file
        """
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

        logger.info(f"Configuration saved to {file_path}")

    def validate(self) -> bool:
        """
        Validate the configuration

        Returns:
            True if configuration is valid, False otherwise
        """
        errors = []

        # Validate node configuration
        if self.node.port < 1 or self.node.port > 65535:
            errors.append(f"Invalid port: {self.node.port}")

        # Validate network configuration
        if self.network.discovery_port < 1 or self.network.discovery_port > 65535:
            errors.append(f"Invalid discovery port: {self.network.discovery_port}")

        if self.network.peer_timeout < 1:
            errors.append(f"Invalid peer timeout: {self.network.peer_timeout}")

        # Validate security configuration
        if self.security.tls_enabled:
            if not self.security.tls_cert_path:
                errors.append("TLS enabled but no certificate path provided")
            if not self.security.tls_key_path:
                errors.append("TLS enabled but no key path provided")

        # Validate logging configuration
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.logging.level.upper() not in valid_levels:
            errors.append(f"Invalid log level: {self.logging.level}")

        # Validate storage configuration
        valid_backends = ['memory', 'redis', 'sqlite']
        if self.storage.backend not in valid_backends:
            errors.append(f"Invalid storage backend: {self.storage.backend}")

        if self.storage.backend == 'redis':
            if not self.storage.redis_host:
                errors.append("Redis backend selected but no host provided")

        if self.storage.backend == 'sqlite':
            if not self.storage.sqlite_path:
                errors.append("SQLite backend selected but no database path provided")

        if errors:
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
            return False

        logger.info("Configuration validated successfully")
        return True


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance

    Returns:
        Global Config instance
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def set_config(config: Config):
    """
    Set the global configuration instance

    Args:
        config: Config instance to set as global
    """
    global _config
    _config = config


def load_config(file_path: Optional[str] = None) -> Config:
    """
    Load configuration from file or environment

    Args:
        file_path: Optional path to configuration file

    Returns:
        Loaded Config instance
    """
    if file_path and os.path.exists(file_path):
        config = Config.from_file(file_path)
    else:
        config = Config.from_env()

    set_config(config)
    return config


if __name__ == '__main__':
    # Example usage
    config = Config.from_env()
    print("Configuration loaded from environment:")
    print(json.dumps(config.to_dict(), indent=2))

    # Validate
    if config.validate():
        print("\nConfiguration is valid!")
    else:
        print("\nConfiguration has errors!")
