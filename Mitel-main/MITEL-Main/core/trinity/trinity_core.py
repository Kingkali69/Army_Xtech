import asyncio
import time
from typing import Dict, Any, List

class EventBus:
    def __init__(self):
        self.handlers = {}
    def on(self, event: str, handler):
        if event not in self.handlers:
            self.handlers[event] = []
        self.handlers[event].append(handler)
    async def emit(self, event: str, data: Any):
        if event in self.handlers:
            for handler in self.handlers[event]:
                result = handler(data)
                if asyncio.iscoroutine(result):
                    await result

class MemoryCore:
    def __init__(self):
        self.flash = {}
        self.session = []
        self.spectral = {}
    def update_flash(self, key: str, value: Any):
        self.flash[key] = value
    def get_flash(self, key: str, default=None):
        return self.flash.get(key, default)
    def push_session(self, value: Dict[str, Any]):
        value['timestamp'] = time.time()
        self.session.append(value)
        if len(self.session) > 100:
            self.session = self.session[-100:]
    def get_session(self, count: int = 10) -> List[Dict]:
        return self.session[-count:] if self.session else []
    def update_spectral(self, key: str, value: Any):
        self.spectral[key] = value
    def get_spectral(self, key: str, default=None):
        return self.spectral.get(key, default)

class EchoCore:
    def __init__(self, memory: MemoryCore):
        self.memory = memory
        self.patterns = []
    def analyze(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        analysis = {'user_length': len(user_message), 'response_length': len(ai_response), 'anomaly': False, 'pattern': None, 'intent': None}
        if len(user_message) > 3000:
            analysis['anomaly'] = True
            analysis['anomaly_reason'] = 'user_message_too_long'
        if len(ai_response) > 5000:
            analysis['anomaly'] = True
            analysis['anomaly_reason'] = 'response_too_long'
        user_lower = user_message.lower()
        if any(word in user_lower for word in ['help','how','what','explain']):
            analysis['intent'] = 'help'
        elif any(word in user_lower for word in ['build','create','code','implement']):
            analysis['intent'] = 'build'
        elif any(word in user_lower for word in ['scan','hack','security','pentest']):
            analysis['intent'] = 'security'
        else:
            analysis['intent'] = 'conversation'
        intent_count = self.memory.get_spectral(f'intent_{analysis["intent"]}', 0)
        self.memory.update_spectral(f'intent_{analysis["intent"]}', intent_count + 1)
        avg_length = self.memory.get_spectral('avg_user_length', 0)
        if avg_length == 0:
            avg_length = analysis['user_length']
        else:
            avg_length = (avg_length + analysis['user_length']) / 2
        self.memory.update_spectral('avg_user_length', avg_length)
        return analysis

class GhostCore:
    def __init__(self, memory: MemoryCore, echo: EchoCore):
        self.memory = memory
        self.echo = echo
    def process(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        self.memory.push_session({'user': user_message, 'ai': ai_response, 'timestamp': time.time()})
        analysis = self.echo.analyze(user_message, ai_response)
        recent = self.memory.get_session(5)
        context = {'has_history': len(recent) > 1, 'recent_intents': [self.echo.analyze(r.get('user',''), r.get('ai','')).get('intent') for r in recent[-3:]]}
        modified_response = ai_response
        actions = []
        if analysis.get('anomaly'):
            actions.append({'type': 'anomaly_detected', 'reason': analysis.get('anomaly_reason')})
        if context['has_history']:
            intent_counts = {}
            for intent in context['recent_intents']:
                if intent:
                    intent_counts[intent] = intent_counts.get(intent, 0) + 1
            if analysis['intent'] in intent_counts and intent_counts[analysis['intent']] >= 2:
                actions.append({'type': 'repeated_intent', 'intent': analysis['intent']})
        return {'response': modified_response, 'analysis': analysis, 'context': context, 'actions': actions, 'anomaly': analysis.get('anomaly', False)}

class ShellCore:
    def __init__(self, bus: EventBus):
        self.bus = bus
    async def execute(self, data: Dict[str, Any]):
        actions = data.get('actions', [])
        for action in actions:
            action_type = action.get('type')
            if action_type == 'anomaly_detected':
                await self.bus.emit('anomaly', {'reason': action.get('reason'), 'timestamp': time.time()})
            elif action_type == 'repeated_intent':
                await self.bus.emit('pattern_detected', {'intent': action.get('intent'), 'timestamp': time.time()})
        return {'executed': len(actions)}

class Trinity:
    def __init__(self):
        self.bus = EventBus()
        self.memory = MemoryCore()
        self.echo = EchoCore(self.memory)
        self.ghost = GhostCore(self.memory, self.echo)
        self.shell = ShellCore(self.bus)
        self.bus.on('anomaly', self._handle_anomaly)
        self.bus.on('pattern_detected', self._handle_pattern)
    def _handle_anomaly(self, data: Dict):
        print(f"[TRINITY] ANOMALY {data.get('reason')}")
    def _handle_pattern(self, data: Dict):
        print(f"[TRINITY] PATTERN {data.get('intent')}")
    async def run(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        processed = self.ghost.process(user_message, ai_response)
        if processed.get('actions'):
            await self.shell.execute(processed)
        return processed
    def get_status(self) -> Dict[str, Any]:
        return {'memory_flash_size': len(self.memory.flash), 'memory_session_size': len(self.memory.session), 'memory_spectral_size': len(self.memory.spectral), 'patterns_tracked': len(self.echo.patterns)}

