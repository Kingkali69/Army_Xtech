import asyncio
from core.ghost_core import GhostCore
from core.echo_core import EchoCore
from core.shell_core import ShellCore
from core.orchestrator import Orchestrator
from core.persona_dynamic import DynamicPersona
from core.behavior_expander import BehaviorExpander
from core.autonomy import GoalEngine
from core.predictive import PredictiveEngine
from core.scheduler import TaskScheduler
from core.script_generator import ScriptGenerator
from core.distributed_task import DistributedTaskEngine
from modules.language import LanguageModule
from modules.signals import SignalModule
from modules.insights import InsightModule
from modules.voice_io import VoiceIO
from modules.wakeword import WakeWord
from memory.flash import FlashMemory
from memory.session import SessionMemory
from memory.spectral import SpectralMemory
from memory.shared import SharedMemory
from memory.longterm import LongTermMemory
from memory.agent_sync import AgentSync
from memory.global_sync import GlobalMemorySync
from analytics.patterns import PatternMapper
from analytics.behavior import BehaviorTracker
from analytics.anomaly import AnomalyScorer
from analytics.sentinel import Sentinel
from runtime.listener import Listener
from runtime.mesh_discovery import MeshDiscovery
from runtime.mesh_sync import MeshSync
from tools.loader import ToolInvoker
from runtime.event_bus import EventBus
from runtime.plugin_bus import PluginBus


def build_agent(role):
    # Memory
    flash = FlashMemory()
    session = SessionMemory()
    spectral = SpectralMemory()
    shared = SharedMemory()
    longterm = LongTermMemory()
    agent_sync = AgentSync()

    memory = {
        "flash": flash, "session": session, "spectral": spectral,
        "shared": shared, "longterm": longterm, "sync": agent_sync
    }

    # Modules
    modules = {
        "language": LanguageModule(),
        "signals": SignalModule(),
        "insights": InsightModule(),
        "voice": VoiceIO()
    }

    # Analytics
    analytics = {
        "patterns": PatternMapper(),
        "behavior": BehaviorTracker(),
        "anomaly": AnomalyScorer(),
        "sentinel": Sentinel()
    }

    # Tools & buses
    tools = ToolInvoker()
    event_bus = EventBus()
    plugin_bus = PluginBus()

    # Cores
    ghost = GhostCore(memory, modules)
    echo = EchoCore(analytics, spectral)
    shell = ShellCore(tools, event_bus)
    listener = Listener()
    wake = WakeWord(keyword=role.lower())
    persona = DynamicPersona()
    behavior_expander = BehaviorExpander()
    goal_engine = GoalEngine(longterm)
    predictive = PredictiveEngine(longterm)
    script_gen = ScriptGenerator()

    return {
        "ghost": ghost,
        "echo": echo,
        "shell": shell,
        "listener": listener,
        "wake": wake,
        "persona": persona,
        "behavior_expander": behavior_expander,
        "tools": tools,
        "goal_engine": goal_engine,
        "predictive": predictive,
        "script_gen": script_gen,
        "load": 0.0  # Node load for distributed task assignment
    }


async def main():
    # Build agents
    ghost_agent = build_agent("ghost")
    trinity_agent = build_agent("trinity")

    agents = [ghost_agent, trinity_agent]

    # Mesh & global sync
    mesh = MeshSync(agents)
    global_sync = GlobalMemorySync(agents)

    # Scheduler & distributed task engine
    scheduler = TaskScheduler()
    distributed_engine = DistributedTaskEngine(agents)

    # Orchestrator
    orchestrator = Orchestrator(
        agents,
        mesh,
        scheduler,
        distributed_engine
    )

    print("TRINITY LEVEL 5 ONLINE — GHOST & TRINITY ACTIVE")
    await orchestrator.run_all()


if __name__ == "__main__":
    asyncio.run(main())
