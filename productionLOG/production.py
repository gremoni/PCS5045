import asyncio
import spade
import json
import random
import logging
from datetime import datetime
from spade_artifact import Artifact, ArtifactMixin
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour, TimeoutBehaviour, FSMBehaviour, State
from spade_pubsub import PubSubMixin
from spade.agent import Agent

XMPP_SERVER = "desktop-5tqm7ia.mshome.net"
PUBSUB_JID = "pubsub.desktop-5tqm7ia.mshome.net"
SCALE_PUBSUB = "scale"

# LOGS CONF AQUI
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# FIM LOG CONF
class OperationAgent(Agent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.operating_cost = operating_cost
        self.capacity = capacity
        self.duration = duration
        self.start_time = datetime.now()


class TransportAgent(ArtifactMixin, OperationAgent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, artifact_jid, pubsub_server=None, *args, **kwargs):
        super().__init__(jid, password, operating_cost, capacity, duration, pubsub_server=pubsub_server, *args, **kwargs)
        self.artifact_jid = artifact_jid

    def truck_callback(self, artifact, payload):
        print(f"Received: [{artifact}] -> {payload}")

    class TransportBehav(CyclicBehaviour):
        async def on_start(self):
            print(f"[{self.agent.name}] Starting Behav")

        async def run(self):
            await asyncio.sleep(10)

    async def setup(self):
        self.presence.approve_all = True
        self.presence.subscribe(self.artifact_jid)
        self.presence.set_available()
        await self.artifacts.focus(self.artifact_jid, self.truck_callback)
        transport_behav = self.TransportBehav()
        self.add_behaviour(transport_behav)


class InspectionAgent(PubSubMixin, OperationAgent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, verify_security: bool = False):
        super().__init__(jid, password, operating_cost, capacity, duration, verify_security)

    class WriteToScaleBehav(OneShotBehaviour):
        async def run(self):
            amount = 100
            try:
                await self.agent.pubsub.publish(PUBSUB_JID, SCALE_PUBSUB, str(amount))
            except Exception:
                print("erro")

            print("published")

    async def setup(self):
        behav = self.WriteToScaleBehav()
        self.add_behaviour(behav)


class PackingAgent(PubSubMixin, OperationAgent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, verify_security: bool = False):
        super().__init__(jid, password, operating_cost, capacity, duration, verify_security)

    def scale_callback(self, jid, node, item, message=None):
        print(f"[{self.name}] Received: [{node}] -> {item.registered_payload.data}")

    async def setup(self):
        self.presence.approve_all = True
        self.presence.set_available()
        await self.pubsub.subscribe(PUBSUB_JID, SCALE_PUBSUB)
        self.pubsub.set_on_item_published(self.scale_callback)


class ManagerAgent(PubSubMixin, Agent):
    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)

    class DummyBehav(CyclicBehaviour):
        async def run(self):
            logger.info(f"[{self.agent.name}] Running")  # REGISTRAR LOG
            await asyncio.sleep(2)

    async def setup(self):
        try:
            await self.pubsub.create(PUBSUB_JID, SCALE_PUBSUB)
        except:
            print("Node already exists")

# CALSSE DUMMY
class DummyAgent(Agent):
    async def setup(self):
        while True:
            logger.info("REGISTRO DE LOG AGENTE DUMMY")
            await asyncio.sleep(10)

async def main():
    inspection_agent_user = "agente1"
    manager_agent_user = "agente2"
    packing_agent_user = "agente3"
    password = "senhadoagente"

    manager_agent = ManagerAgent(
        jid=f"{manager_agent_user}@{XMPP_SERVER}",
        password=password,
    )
    await manager_agent.start()

    inspection_agent = InspectionAgent(
        jid=f"{inspection_agent_user}@{XMPP_SERVER}",
        password=password,
        capacity=10,
        duration=10,
        operating_cost=10,
    )
    await inspection_agent.start()

    packing_agent = PackingAgent(
        jid=f"{packing_agent_user}@{XMPP_SERVER}",
        password=password,
        capacity=10,
        duration=10,
        operating_cost=10,
    )
    await packing_agent.start()

    # AGENTE DUMMY
    dummy_agent = DummyAgent(
        jid="dummy@desktop-5tqm7ia.mshome.net",
        password=password,
    )
    await dummy_agent.start()

if __name__ == "__main__":
    spade.run(main())
