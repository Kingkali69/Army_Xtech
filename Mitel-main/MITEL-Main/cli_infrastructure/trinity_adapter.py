import asyncio
from trinity_core import Trinity

_trinity_instance = None

def get_trinity() -> Trinity:
    global _trinity_instance
    if _trinity_instance is None:
        _trinity_instance = Trinity()
        print("[TRINITY] READY")
    return _trinity_instance

def process(user_message: str, ai_response: str):
    try:
        trinity = get_trinity()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            processed = loop.run_until_complete(trinity.run(user_message, ai_response))
        finally:
            loop.close()
        return {'response': processed.get('response', ai_response), 'analysis': processed.get('analysis', {}), 'anomaly': processed.get('anomaly', False), 'trinity_enabled': True}
    except Exception as e:
        return {'response': ai_response, 'trinity_enabled': False, 'error': str(e)}

