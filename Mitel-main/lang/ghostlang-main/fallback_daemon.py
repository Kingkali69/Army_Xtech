# Add to ghost_fallback_daemon.py
class FallbackAPI:
    """Simple REST API for fallback daemon"""
    
    def __init__(self, daemon, port=7899):
        self.daemon = daemon
        self.port = port
        self.app = Flask(__name__)
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/status')
        def status():
            return jsonify(self.daemon.get_status())
            
        @self.app.route('/commands')
        def commands():
            cmds = self.daemon.command_queue.get_all_commands()
            return jsonify({
                'commands': [cmd.to_dict() for cmd in cmds]
            })
            
        @self.app.route('/commands/ack', methods=['POST'])
        def ack_commands():
            data = request.json
            command_ids = data.get('command_ids', [])
            for cmd_id in command_ids:
                self.daemon.command_queue.mark_completed(cmd_id)
            return jsonify({'status': 'ok'})
    
    def start(self):
        threading.Thread(target=lambda: self.app.run(
            host='0.0.0.0', port=self.port, debug=False
        ), daemon=True).start()
