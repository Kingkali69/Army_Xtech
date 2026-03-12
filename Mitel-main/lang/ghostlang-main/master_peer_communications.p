# Add this to ghost_comms.py
def connectivity_change_handler(old_status, new_status):
    """Handle connectivity status changes"""
    if new_status == ConnectivityStatus.ONLINE:
        # We're back online, process queued commands
        process_offline_commands()
    elif new_status == ConnectivityStatus.LOCAL_ONLY:
        # Local network only, use mesh
        switch_to_mesh_only()
    elif new_status == ConnectivityStatus.ISOLATED:
        # Completely isolated, use USB or Lo-Fi
        switch_to_offline_mode()
