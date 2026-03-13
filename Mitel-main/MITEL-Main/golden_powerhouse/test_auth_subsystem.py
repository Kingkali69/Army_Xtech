import pytest
import asyncio
import os
import yaml
import json
from unittest.mock import AsyncMock, MagicMock, patch, call
from pathlib import Path

# Import engine_core components
from engine_core import EngineCore, SubsystemState
from auth_subsystem_enhanced import AuthSubsystem

@pytest.fixture
def mock_event_bus():
    """Create a mock event bus"""
    event_bus = AsyncMock()
    event_bus.subscribe = AsyncMock()
    event_bus.publish = AsyncMock()
    event_bus.running = True
    return event_bus

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def engine_with_mock_auth():
    """Create engine with mocked AuthSubsystem"""
    with patch('engine_core.AuthSubsystem') as mock_auth_class:
        # Create mock instance
        mock_auth = AsyncMock()
        mock_auth.initialize = AsyncMock()
        mock_auth.start = AsyncMock()
        mock_auth.stop = AsyncMock()
        mock_auth.get_status = AsyncMock(return_value={
            'active': True,
            'version': '1.0.0',
            'user_count': 5,
            'failed_attempts': 2,
            'locked_accounts': 1,
            'providers': {'local': True, 'oauth': False}
        })
        
        # Make the class return our mock instance
        mock_auth_class.return_value = mock_auth
        
        # Create engine
        engine = EngineCore()
        
        # Add our mock to the engine
        engine.subsystems['auth_sub'] = mock_auth
        engine.subsystem_states['auth_sub'] = SubsystemState.READY
        
        yield engine, mock_auth

@pytest.mark.asyncio
async def test_auth_subsystem_initialization(temp_config_dir):
    """Test AUTH-SUB initialization with default config"""
    config_path = temp_config_dir / "engine_config.yaml"
    auth_config_path = temp_config_dir / "auth_config.yaml"
    
    # Setup minimal engine config
    engine_config = {
        "subsystems": {
            "auth_sub": {
                "enabled": True,
                "config_path": str(auth_config_path),
                "critical": False
            }
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(engine_config, f)
    
    with patch('engine_core.AuthSubsystem') as mock_auth_class:
        mock_auth = AsyncMock()
        mock_auth_class.return_value = mock_auth
        
        # Initialize engine
        engine = EngineCore(config_path=str(config_path))
        await engine.initialize()
        
        # Check if the auth config was created
        assert auth_config_path.exists()
        
        # Check if AUTH-SUB was initialized
        mock_auth_class.assert_called_once_with(str(auth_config_path))
        mock_auth.initialize.assert_called_once()
        
        # Check if subsystem was registered
        assert 'auth_sub' in engine.subsystems
        assert engine.subsystem_states['auth_sub'] == SubsystemState.READY

@pytest.mark.asyncio
async def test_auth_subsystem_event_bus_integration(temp_config_dir, mock_event_bus):
    """Test AUTH-SUB integration with event bus"""
    config_path = temp_config_dir / "engine_config.yaml"
    auth_config_path = temp_config_dir / "auth_config.yaml"
    
    # Setup minimal engine config
    engine_config = {
        "subsystems": {
            "auth_sub": {
                "enabled": True,
                "config_path": str(auth_config_path),
                "critical": False
            }
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(engine_config, f)
    
    with patch('engine_core.AuthSubsystem') as mock_auth_class:
        mock_auth = AsyncMock()
        mock_auth_class.return_value = mock_auth
        
        # Initialize engine with event bus
        engine = EngineCore(config_path=str(config_path))
        engine.event_bus = mock_event_bus
        
        # Initialize AUTH-SUB
        await engine._init_auth_subsystem(engine_config['subsystems']['auth_sub'])
        
        # Check if event bus was passed to AUTH-SUB
        mock_auth.set_event_bus.assert_called_once_with(mock_event_bus)
        
        # Simulate auth event
        auth_event = {
            'type': 'auth.login_attempt',
            'username': 'testuser',
            'success': True
        }
        
        # Publish event
        await engine.event_bus.publish('auth.login_attempt', auth_event)
        engine.event_bus.publish.assert_called_with('auth.login_attempt', auth_event)

@pytest.mark.asyncio
async def test_auth_subsystem_cli_commands(engine_with_mock_auth):
    """Test AUTH-SUB CLI commands"""
    engine, mock_auth = engine_with_mock_auth
    
    # Test status command
    mock_args = MagicMock()
    mock_args.command = 'auth'
    mock_args.status = True
    
    # Add CLI to engine
    engine.cli = MagicMock()
    engine.cli.process_command = AsyncMock()
    
    # Setup test user data
    mock_auth.list_users = AsyncMock(return_value=[
        {'username': 'admin', 'email': 'admin@example.com', 'status': 'active', 'role': 'admin'},
        {'username': 'user1', 'email': 'user1@example.com', 'status': 'active', 'role': 'user'},
    ])
    
    mock_auth.create_user = AsyncMock(return_value={'success': True})
    mock_auth.delete_user = AsyncMock(return_value={'success': True})
    mock_auth.reset_password = AsyncMock(return_value={'success': True})
    
    with patch('engine_core.AuthCommands._handle_auth_status', new_callable=AsyncMock) as mock_handle_status:
        mock_handle_status.return_value = 0
        
        from engine_core import AuthCommands
        result = await AuthCommands.handle_command(engine, mock_args)
        
        assert result == 0
        mock_handle_status.assert_called_once_with(mock_auth, mock_args)
        mock_auth.get_status.assert_called_once()

@pytest.mark.asyncio
async def test_auth_subsystem_start_stop_lifecycle(engine_with_mock_auth):
    """Test AUTH-SUB startup and shutdown lifecycle"""
    engine, mock_auth = engine_with_mock_auth
    
    # Test subsystem start
    await engine.start()
    mock_auth.start.assert_called_once()
    assert engine.subsystem_states['auth_sub'] == SubsystemState.RUNNING
    
    # Test subsystem stop
    await engine.stop()
    mock_auth.stop.assert_called_once()
    assert engine.subsystem_states['auth_sub'] == SubsystemState.STOPPED

@pytest.mark.asyncio
async def test_auth_subsystem_user_management_commands(engine_with_mock_auth):
    """Test AUTH-SUB user management CLI commands"""
    engine, mock_auth = engine_with_mock_auth
    
    # Setup test user data
    mock_auth.list_users = AsyncMock(return_value=[
        {'username': 'admin', 'email': 'admin@example.com', 'status': 'active', 'role': 'admin'},
        {'username': 'user1', 'email': 'user1@example.com', 'status': 'active', 'role': 'user'},
    ])
    
    mock_auth.create_user = AsyncMock(return_value={'success': True})
    mock_auth.delete_user = AsyncMock(return_value={'success': True})
    mock_auth.reset_password = AsyncMock(return_value={'success': True})
    
    from engine_core import AuthCommands
    
    # Test list users command
    list_args = MagicMock()
    list_args.user_command = 'list'
    list_args.filter = None
    
    result = await AuthCommands._handle_user_command(mock_auth, list_args)
    assert result == 0
    mock_auth.list_users.assert_called_once_with(None)
    
    # Test create user command
    create_args = MagicMock()
    create_args.user_command = 'create'
    create_args.username = 'newuser'
    create_args.password = 'password123'
    create_args.email = 'newuser@example.com'
    create_args.role = 'user'
    
    result = await AuthCommands._handle_user_command(mock_auth, create_args)
    assert result == 0
    mock_auth.create_user.assert_called_once_with(
        username='newuser',
        password='password123',
        email='newuser@example.com',
        role='user'
    )
    
    # Test delete user command
    delete_args = MagicMock()
    delete_args.user_command = 'delete'
    delete_args.username = 'user1'
    
    result = await AuthCommands._handle_user_command(mock_auth, delete_args)
    assert result == 0
    mock_auth.delete_user.assert_called_once_with('user1')

@pytest.mark.asyncio
async def test_auth_subsystem_error_handling(temp_config_dir):
    """Test AUTH-SUB error handling and non-critical failures"""
    config_path = temp_config_dir / "engine_config.yaml"
    auth_config_path = temp_config_dir / "auth_config.yaml"
    
    # Setup engine config where AUTH-SUB is NOT critical
    engine_config = {
        "subsystems": {
            "auth_sub": {
                "enabled": True,
                "config_path": str(auth_config_path),
                "critical": False
            }
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(engine_config, f)
    
    with patch('engine_core.AuthSubsystem') as mock_auth_class:
        # Make initialization fail
        mock_auth = AsyncMock()
        mock_auth.initialize = AsyncMock(side_effect=Exception("Auth initialization failed"))
        mock_auth_class.return_value = mock_auth
        
        # Initialize engine
        engine = EngineCore(config_path=str(config_path))
        
        # Since AUTH-SUB is not critical, this should not raise an exception
        await engine.initialize()
        
        # Check that subsystem is marked as ERROR
        assert engine.subsystem_states['auth_sub'] == SubsystemState.ERROR
        
        # Engine should still be usable
        assert engine.running == False  # Not started yet
        
        # Other subsystems should be unaffected
        if 'sp_sub' in engine.subsystems:
            assert engine.subsystem_states['sp_sub'] != SubsystemState.ERROR

@pytest.mark.asyncio
async def test_auth_subsystem_critical_failure(temp_config_dir):
    """Test AUTH-SUB critical failure propagation"""
    config_path = temp_config_dir / "engine_config.yaml"
    auth_config_path = temp_config_dir / "auth_config.yaml"
    
    # Setup engine config where AUTH-SUB IS critical
    engine_config = {
        "subsystems": {
            "auth_sub": {
                "enabled": True,
                "config_path": str(auth_config_path),
                "critical": True  # Mark as critical
            }
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(engine_config, f)
    
    with patch('engine_core.AuthSubsystem') as mock_auth_class:
        # Make initialization fail
        mock_auth = AsyncMock()
        mock_auth.initialize = AsyncMock(side_effect=Exception("Auth initialization failed"))
        mock_auth_class.return_value = mock_auth
        
        # Initialize engine
        engine = EngineCore(config_path=str(config_path))
        
        # Since AUTH-SUB is critical, this should raise an exception
        with pytest.raises(Exception) as excinfo:
            await engine.initialize()
        
        assert "Critical subsystem" in str(excinfo.value)

@pytest.mark.asyncio
async def test_auth_subsystem_cli_integration(engine_with_mock_auth):
    """Test AUTH-SUB CLI integration with engine"""
    engine, mock_auth = engine_with_mock_auth
    
    # Mock the CLI command processor
    engine.cli = MagicMock()
    engine.cli.process_command = AsyncMock(return_value=0)
    
    # Create mock CLI args
    cli_args = ["auth", "--status"]
    
    # Process CLI command
    result = await engine.process_cli_command(cli_args)
    
    # Verify CLI command was processed
    engine.cli.process_command.assert_called_once()
    assert result == 0

@pytest.mark.asyncio
async def test_auth_subsystem_restart(engine_with_mock_auth):
    """Test restarting AUTH-SUB subsystem"""
    engine, mock_auth = engine_with_mock_auth
    
    # Start the subsystem
    await engine.start()
    assert engine.subsystem_states['auth_sub'] == SubsystemState.RUNNING
    
    # Restart the subsystem
    result = await engine.restart_subsystem('auth_sub')
    
    # Verify the restart sequence
    assert result is True
    assert mock_auth.stop.call_count == 1
    assert mock_auth.start.call_count == 2  # Once for initial start, once for restart
    assert engine.subsystem_states['auth_sub'] == SubsystemState.RUNNING
