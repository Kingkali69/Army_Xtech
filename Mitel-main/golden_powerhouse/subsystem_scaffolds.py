# subsystem_scaffolds.py
# G.Legion Framework - Testable Subsystem Scaffolds

import asyncio
import logging
import yaml
import json
import uuid
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path
from abc import ABC, abstractmethod

# Base Subsystem Interface
class BaseSubsystem(ABC):
    """Base class for all G.Legion subsystems"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = {}
        self.running = False
        self.initialized = False
        self.subsystem_id = str(uuid.uuid4())[:8]
        self.logger = logging.getLogger(f"G.Legion.{self.__class__.__name__}")
        self.start_time = None
        
    @abstractmethod
    async def initialize(self):
        """Initialize the subsystem"""
        pass
    
    @abstractmethod
    async def start(self):
        """Start the subsystem"""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the subsystem"""
        pass
    
    async def health_check(self) -> bool:
        """Perform health check"""
        return self.running and self.initialized
    
    def get_status(self) -> Dict[str, Any]:
        """Get subsystem status"""
        return {
            'subsystem_id': self.subsystem_id,
            'running': self.running,
            'initialized': self.initialized,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }

# 1. Session Control Subsystem (SC-SUB)
class SessionControlSubsystem(BaseSubsystem):
    """Session Control Subsystem - Manages user sessions and access control"""
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.sessions = {}
        self.user_sessions = {}
        self.cleanup_task = None
        self.max_sessions = 10000
        self.session_timeout = 3600
        self.max_user_sessions = 5
        
    async def initialize(self):
        """Initialize SC-SUB"""
        try:
            # Load configuration
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            
            # Apply configuration
            self.max_sessions = self.config.get('max_sessions', 10000)
            self.session_timeout = self.config.get('session_timeout', 3600)
            self.max_user_sessions = self.config.get('max_user_sessions', 5)
            
            self.initialized = True
            self.logger.info(f"SC-SUB initialized (max_sessions: {self.max_sessions})")
            
        except Exception as e:
            self.logger.error(f"SC-SUB initialization failed: {e}", exc_info=True)
            raise
    
    async def start(self):
        """Start SC-SUB"""
        if not self.initialized:
            raise RuntimeError("SC-SUB not initialized")
        
        if self.running:
            return
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.running = True
        self.start_time = datetime.now()
        self.logger.info("SC-SUB started")
    
    async def stop(self):
        """Stop SC-SUB"""
        if not self.running:
            return
        
        self.running = False
        
        # Stop cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clear all sessions
        self.sessions.clear()
        self.user_sessions.clear()
        
        self.logger.info("SC-SUB stopped")
    
    async def create_session(self, user_id: str, metadata: Dict = None) -> str:
        """Create a new session"""
        if not self.running:
            raise RuntimeError("SC-SUB not running")
        
        # Check limits
        if len(self.sessions) >= self.max_sessions:
            raise RuntimeError("Maximum sessions exceeded")
        
        user_session_count = len(self.user_sessions.get(user_id, []))
        if user_session_count >= self.max_user_sessions:
            # Clean up oldest session for this user
            oldest_session = min(self.user_sessions[user_id], 
                               key=lambda s: self.sessions[s]['created_at'])
            await self.destroy_session(oldest_session)
        
        # Create session
        session_id = f"sess_{uuid.uuid4().hex[:16]}"
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'metadata': metadata or {}
        }
        
        self.sessions[session_id] = session_data
        
        # Track user sessions
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)
        
        self.logger.debug(f"Created session {session_id} for user {user_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if expired
        if self._is_expired(session):
            await self.destroy_session(session_id)
            return None
        
        # Update activity
        session['last_activity'] = datetime.now()
        return session.copy()
    
    async def destroy_session(self, session_id: str) -> bool:
        """Destroy a session"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        user_id = session['user_id']
        
        # Remove from sessions
        del self.sessions[session_id]
        
        # Remove from user sessions
        if user_id in self.user_sessions:
            self.user_sessions[user_id] = [
                s for s in self.user_sessions[user_id] if s != session_id
            ]
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
        
        self.logger.debug(f"Destroyed session {session_id}")
        return True
    
    def _is_expired(self, session: Dict) -> bool:
        """Check if session is expired"""
        last_activity = session['last_activity']
        return (datetime.now() - last_activity).total_seconds() > self.session_timeout
    
    async def _cleanup_loop(self):
        """Cleanup expired sessions"""
        cleanup_interval = self.config.get('cleanup_interval', 300)
        
        while self.running:
            try:
                expired_sessions = []
                for session_id, session in self.sessions.items():
                    if self._is_expired(session):
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    await self.destroy_session(session_id)
                
                if expired_sessions:
                    self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
                await asyncio.sleep(cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                await asyncio.sleep(10)

# 2. Event Bus Subsystem (EB-SUB)
class EventBusSubsystem(BaseSubsystem):
    """Event Bus Subsystem - Central event routing and messaging"""
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.subscribers = {}
        self.event_history = []
        self.max_events_per_second = 1000
        self.max_subscribers = 100
        self.event_retention_seconds = 3600
        self.cleanup_task = None
        
    async def initialize(self):
        """Initialize EB-SUB"""
        try:
            # Load configuration
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            
            # Apply configuration
            self.max_events_per_second = self.config.get('max_events_per_second', 1000)
            self.max_subscribers = self.config.get('max_subscribers', 100)
            self.event_retention_seconds = self.config.get('event_retention_seconds', 3600)
            
            self.initialized = True
            self.logger.info(f"EB-SUB initialized (max_events/s: {self.max_events_per_second})")
            
        except Exception as e:
            self.logger.error(f"EB-SUB initialization failed: {e}", exc_info=True)
            raise
    
    async def start(self):
        """Start EB-SUB"""
        if not self.initialized:
            raise RuntimeError("EB-SUB not initialized")
        
        if self.running:
            return
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.running = True
        self.start_time = datetime.now()
        self.logger.info("EB-SUB started")
    
    async def stop(self):
        """Stop EB-SUB"""
        if not self.running:
            return
        
        self.running = False
        
        # Stop cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clear subscribers and history
        self.subscribers.clear()
        self.event_history.clear()
        
        self.logger.info("EB-SUB stopped")
    
    def subscribe(self, event_type: str, callback, subscriber_id: str = None):
        """Subscribe to an event type"""
        if not self.running:
            raise RuntimeError("EB-SUB not running")
        
        if len(self.subscribers) >= self.max_subscribers:
            raise RuntimeError("Maximum subscribers exceeded")
        
        if event_type not in self.subscribers:
            self.subscribers[event_type] = {}
        
        sub_id = subscriber_id or f"sub_{uuid.uuid4().hex[:8]}"
        self.subscribers[event_type][sub_id] = callback
        
        self.logger.debug(f"Subscribed {sub_id} to {event_type}")
        
        # Return unsubscribe function
        def unsubscribe():
            if event_type in self.subscribers and sub_id in self.subscribers[event_type]:
                del self.subscribers[event_type][sub_id]
                if not self.subscribers[event_type]:
                    del self.subscribers[event_type]
                self.logger.debug(f"Unsubscribed {sub_id} from {event_type}")
        
        return unsubscribe
    
    async def publish(self, event_type: str, event_data: Dict, publisher_id: str = None):
        """Publish an event"""
        if not self.running:
            return
        
        # Create event
        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': event_type,
            'data': event_data,
            'publisher_id': publisher_id,
            'timestamp': datetime.now(),
            'processed': False
        }
        
        # Add to history
        self.event_history.append(event)
        
        # Notify subscribers
        subscribers = self.subscribers.get(event_type, {})
        for sub_id, callback in list(subscribers.items()):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_data)
                else:
                    callback(event_data)
            except Exception as e:
                self.logger.error(f"Error in subscriber {sub_id} for {event_type}: {e}")
        
        event['processed'] = True
        self.logger.debug(f"Published event {event_type} to {len(subscribers)} subscribers")
    
    async def _cleanup_loop(self):
        """Cleanup old events"""
        while self.running:
            try:
                cutoff_time = datetime.now() - timedelta(seconds=self.event_retention_seconds)
                original_count = len(self.event_history)
                
                self.event_history = [
                    event for event in self.event_history 
                    if event['timestamp'] > cutoff_time
                ]
                
                cleaned = original_count - len(self.event_history)
                if cleaned > 0:
                    self.logger.debug(f"Cleaned up {cleaned} old events")
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in event cleanup: {e}", exc_info=True)
                await asyncio.sleep(10)

# 3. Authentication Subsystem (AUTH-SUB)
class AuthSubsystem(BaseSubsystem):
    """Authentication Subsystem - User authentication and authorization"""
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.users = {}
        self.tokens = {}
        self.login_attempts = {}
        self.providers = ['local']
        self.token_expiry = 3600
        self.max_login_attempts = 5
        self.lockout_duration = 300
        
    async def initialize(self):
        """Initialize AUTH-SUB"""
        try:
            # Load configuration
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            
            # Apply configuration
            self.providers = self.config.get('providers', ['local'])
            self.token_expiry = self.config.get('token_expiry', 3600)
            self.max_login_attempts = self.config.get('max_login_attempts', 5)
            self.lockout_duration = self.config.get('lockout_duration', 300)
            
            # Create default admin user for testing
            await self._create_default_users()
            
            self.initialized = True
            self.logger.info(f"AUTH-SUB initialized (providers: {self.providers})")
            
        except Exception as e:
            self.logger.error(f"AUTH-SUB initialization failed: {e}", exc_info=True)
            raise
    
    async def start(self):
        """Start AUTH-SUB"""
        if not self.initialized:
            raise RuntimeError("AUTH-SUB not initialized")
        
        if self.running:
            return
        
        self.running = True
        self.start_time = datetime.now()
        self.logger.info("AUTH-SUB started")
    
    async def stop(self):
        """Stop AUTH-SUB"""
        if not self.running:
            return
        
        self.running = False
        
        # Clear tokens and attempts
        self.tokens.clear()
        self.login_attempts.clear()
        
        self.logger.info("AUTH-SUB stopped")
    
    async def authenticate(self, username: str, password: str, provider: str = 'local') -> Optional[str]:
        """Authenticate user and return token"""
        if not self.running:
            raise RuntimeError("AUTH-SUB not running")
        
        # Check if user is locked out
        if self._is_locked_out(username):
            raise RuntimeError("Account temporarily locked due to failed login attempts")
        
        # Authenticate user
        user = await self._verify_credentials(username, password, provider)
        if not user:
            self._record_failed_attempt(username)
            return None
        
        # Clear failed attempts
        if username in self.login_attempts:
            del self.login_attempts[username]
        
        # Generate token
        token = await self._generate_token(user)
        
        self.logger.info(f"User {username} authenticated successfully")
        return token
    
    async def validate_token(self, token: str) -> Optional[Dict]:
        """Validate token and return user info"""
        if token not in self.tokens:
            return None
        
        token_data = self.tokens[token]
        
        # Check expiry
        if datetime.now() > token_data['expires_at']:
            del self.tokens[token]
            return None
        
        return token_data['user'].copy()
    
    async def revoke_token(self, token: str) -> bool:
        """Revoke a token"""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False
    
    async def _create_default_users(self):
        """Create default users for testing"""
        # Create admin user
        admin_user = {
            'user_id': 'admin',
            'username': 'admin',
            'password_hash': self._hash_password('admin123'),  # Default password
            'roles': ['admin'],
            'created_at': datetime.now(),
            'active': True
        }
        self.users['admin'] = admin_user
        
        # Create test user
        test_user = {
            'user_id': 'testuser',
            'username': 'testuser',
            'password_hash': self._hash_password('test123'),
            'roles': ['user'],
            'created_at': datetime.now(),
            'active': True
        }
        self.users['testuser'] = test_user
    
    async def _verify_credentials(self, username: str, password: str, provider: str) -> Optional[Dict]:
        """Verify user credentials"""
        if provider != 'local':
            # Placeholder for other providers
            return None
        
        user = self.users.get(username)
        if not user or not user.get('active', False):
            return None
        
        # Verify password
        if self._verify_password(password, user['password_hash']):
            return user
        
        return None
    
    async def _generate_token(self, user: Dict) -> str:
        """Generate authentication token"""
        token = f"tok_{uuid.uuid4().hex}"
        expires_at = datetime.now() + timedelta(seconds=self.token_expiry)
        
        self.tokens[token] = {
            'user': user,
            'created_at': datetime.now(),
            'expires_at': expires_at
        }
        
        return token
    
    def _hash_password(self, password: str) -> str:
        """Hash password (simplified for scaffold)"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hash_value: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password) == hash_value
    
    def _is_locked_out(self, username: str) -> bool:
        """Check if user is locked out"""
        if username not in self.login_attempts:
            return False
        
        attempts = self.login_attempts[username]
        if len(attempts) < self.max_login_attempts:
            return False
        
        # Check if lockout period has expired
        last_attempt = max(attempts)
        lockout_expires = last_attempt + timedelta(seconds=self.lockout_duration)
        
        if datetime.now() > lockout_expires:
            # Reset attempts
            del self.login_attempts[username]
            return False
        
        return True
    
    def _record_failed_attempt(self, username: str):
        """Record failed login attempt"""
        if username not in self.login_attempts:
            self.login_attempts[username] = []
        
        self.login_attempts[username].append(datetime.now())
        
        # Keep only recent attempts
        cutoff = datetime.now() - timedelta(seconds=self.lockout_duration)
        sel
