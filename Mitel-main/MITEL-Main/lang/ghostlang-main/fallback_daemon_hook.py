# Add this to linux_master_updated.py and win_peer_updated.py
def check_fallback_daemon():
    """Check for commands in the fallback daemon"""
    try:
        # Get fallback status via API
        response = requests.get("http://localhost:7899/status")
        if response.status_code == 200:
            data = response.json()
            
            # Process any pending commands
            if data.get('pending_commands', 0) > 0:
                response = requests.get("http://localhost:7899/commands")
                if response.status_code == 200:
                    commands = response.json().get('commands', [])
                    for cmd in commands:
                        # Process command
                        process_command(cmd)
                        
                    # Mark commands as processed
                    requests.post("http://localhost:7899/commands/ack", 
                                 json={"command_ids": [c['id'] for c in commands]})
    except:
        pass  # Silently fail if daemon not available
