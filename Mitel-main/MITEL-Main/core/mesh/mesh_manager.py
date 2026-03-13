import os, sys, logging
logging.basicConfig(level=logging.INFO)
try:
    import importlib.util
except ImportError:
    importlib = None
MODULES_DIR = os.path.dirname(__file__)
MESH_PREFIX = 'mesh'
mesh_modules = {}
def load_mesh_modules():
    global mesh_modules
    mesh_modules.clear()
    for fname in os.listdir(MODULES_DIR):
        if fname.startswith(MESH_PREFIX) and fname.endswith('.py') and fname != 'mesh_manager.py':
            modname = fname[:-3]
            try:
                spec = importlib.util.spec_from_file_location(modname, os.path.join(MODULES_DIR, fname))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                # Only add if mesh contract present
                if all(hasattr(mod, x) for x in ['send','receive','broadcast','get_peers','status','start_tunnel']):
                    mesh_modules[modname] = mod
            except Exception as e:
                logging.error(f"[mesh_manager] Failed loading {fname}: {e}")
    logging.info(f"[mesh_manager] Mesh modules loaded: {list(mesh_modules.keys())}")
def broadcast_all(data=None):
    results = {}
    for name, mod in mesh_modules.items():
        try:
            results[name] = mod.broadcast(data=data)
        except Exception as e:
            results[name] = {"error": str(e)}
    return results
def send_all(target=None, data=None):
    results = {}
    for name, mod in mesh_modules.items():
        try:
            results[name] = mod.send(target=target, data=data)
        except Exception as e:
            results[name] = {"error": str(e)}
    return results
def start_tunnel_all(target=None, port=None):
    results = {}
    for name, mod in mesh_modules.items():
        try:
            results[name] = mod.start_tunnel(target=target, port=port)
        except Exception as e:
            results[name] = {"error": str(e)}
    return results
def get_all_peers():
    return {name:mod.get_peers() for name,mod in mesh_modules.items()}
def status_all():
    return {name:mod.status() for name,mod in mesh_modules.items()}
def register(api, core_api=None):
    load_mesh_modules()
    api.register_command('broadcast', broadcast_all, 'Broadcast to all mesh modules')
    api.register_command('send', send_all, 'Send to all mesh modules')
    api.register_command('start_tunnel', start_tunnel_all, 'Start tunnel on all mesh modules')
    api.register_command('get_peers', get_all_peers, 'Get all mesh peers')
    api.register_command('status_all', status_all, 'Get status from all mesh modules')
    # Optional: module reload endpoint
    api.register_command('reload', lambda :load_mesh_modules() or list(mesh_modules.keys()), 'Reload mesh modules')
