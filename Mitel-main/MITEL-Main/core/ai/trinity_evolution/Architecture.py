import asyncio
import heapq
import time
from random import random


class DistributedTaskEngine:
    def __init__(self, mesh_nodes):
        self.mesh_nodes = mesh_nodes  # list of agents/nodes
        self.queue = []

    def propose_task(self, task, priority=0.5):
        # Assign task to least busy node
        node = min(self.mesh_nodes, key=lambda n: n["load"])
        node["load"] += 0.1  # increment load
        heapq.heappush(self.queue, (-priority, time.time(), task, node))

    async def execute(self):
        while True:
            if self.queue:
                _, _, task, node = heapq.heappop(self.queue)
                # safe local execution
                result = node["tools"].invoke(task, node["shell"].bus)
                node["memory"]["longterm"].store(f"Distributed: {task} -> {result}")
                node["load"] = max(0.0, node["load"] - 0.1)
            await asyncio.sleep(random()*0.5)


class GlobalMemorySync:
    def __init__(self, agents):
        self.agents = agents

    def broadcast(self, key, value):
        for agent in self.agents:
            agent["memory"]["shared"].sync(key, value)


class Orchestrator:
    def __init__(self, agents, mesh, scheduler, distributed_engine):
        self.agents = agents
        self.mesh = mesh
        self.scheduler = scheduler
        self.distributed = distributed_engine

    async def run_agent(self, agent):
        wake = agent["wake"]
        while True:
            triggered = await wake.detect()
            if not triggered:
                await asyncio.sleep(0.01)
                continue

            event = await agent["listener"].capture()
            processed = await agent["ghost"].process(event)
            await agent["echo"].observe(processed)
            await agent["shell"].execute(processed)

            # Persona evolution
            agent["persona"].update({"confidence":0.01,"focus":0.01,"initiative":0.02})

            # Predictive task generation
            prediction = agent["predictive"].anticipate(str(processed))
            if prediction:
                script = agent["script_gen"].propose(prediction)
                agent["goal_engine"].active_goals.append(script)
                self.distributed.propose_task({"intent": prediction, "script": script}, priority=0.7)

    async def heartbeat(self):
        while True:
            await self.mesh.distribute("heartbeat", "alive")
            await asyncio.sleep(1)

    async def run_all(self):
        tasks = [asyncio.create_task(self.heartbeat()),
                 asyncio.create_task(self.distributed.execute()),
                 asyncio.create_task(self.scheduler.run())]
        for agent in self.agents:
            tasks.append(asyncio.create_task(self.run_agent(agent)))
        await asyncio.gather(*tasks)
