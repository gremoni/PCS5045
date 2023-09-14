import asyncio
from typing import Optional
import spade
import json
import random

from datetime import datetime, timedelta
from spade_artifact import Artifact, ArtifactMixin
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour, TimeoutBehaviour, FSMBehaviour, State
from spade_pubsub import PubSubMixin
from spade.agent import Agent

XMPP_SERVER = "nave"
PUBSUB_JID = f"pubsub.{XMPP_SERVER}"

SCALE_PUBSUB = "scale"
STOCK_PUBSUB = "stock"

class OperationAgent(Agent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.operating_cost = operating_cost
        self.capacity = capacity
        self.duration = duration
        self.start_time = datetime.now()


class TruckAgent(PubSubMixin, Agent):
    def __init__(self, jid: str, password: str, operating_cost, deliver_period, verify_security: bool = False):
        self.operating_cost = operating_cost
        self.deliver_period = deliver_period
        self.start_delay = 10
        self.deliver_amounts = [1000, 1500, 2000, 2500, 3000]
        super().__init__(jid, password, verify_security)

    class TruckDeliverBehav(PeriodicBehaviour):
        def __init__(self, period: float, start_at: datetime, pubsub : PubSubMixin.PubSubComponent):
            self.pubsub = pubsub
            super().__init__(period, start_at)

        async def on_start(self):
           print(f"[{self.agent.name}] Starting Truck Deliver Behav")

        async def run(self):
            deliver_amount = random.choice(self.agent.deliver_amounts)
            
            try:
                await self.pubsub.publish(PUBSUB_JID, STOCK_PUBSUB, str(deliver_amount))
            except Exception:
                print(f"[{self.agent.name}] {STOCK_PUBSUB} PubSub Error")

            print(f"[{self.agent.name}] Delivered {deliver_amount}")
            random_delay_time = random.randrange(0, 20, 2)
            await asyncio.sleep(random_delay_time)

    async def setup(self):
        start_at = datetime.now() + timedelta(seconds=self.start_delay)
        deliver_behav = self.TruckDeliverBehav(period = self.deliver_period,
                                               start_at = start_at,
                                               pubsub = self.pubsub)
        self.add_behaviour(deliver_behav)


class InspectionAgent(PubSubMixin, OperationAgent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, verify_security: bool = False):
        super().__init__(jid, password, operating_cost, capacity, duration, verify_security)

    class WriteToScaleBehav(CyclicBehaviour):
        async def run(self):
            amount = 100
            try:
                await self.agent.pubsub.publish(PUBSUB_JID, SCALE_PUBSUB, str(amount))
            except Exception:
                print("erro")

            print("published")

            await asyncio.sleep(5)

    async def setup(self):
        # list_of_nodes = await self.pubsub.get_nodes(PUBSUB_JID)
        # print(f"[{self.name}] List of nodes: {list_of_nodes}")
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
            print(f"[{self.agent.name}] Running")
            await asyncio.sleep(2)
    
    async def setup(self):
        try:
            await self.pubsub.create(PUBSUB_JID, SCALE_PUBSUB)
        except:
            print("Node already exists")



# class ProductionAgent(OperationAgent):

# class BoxingAgent(OperationAgent):


async def main():
    inspection_agent_user = "agente1"
    manager_agent_user = "agente2"
    packing_agent_user = "agente3"
    password = "senhadoagente"

    manager_agent = ManagerAgent(
        jid = f"{manager_agent_user}@{XMPP_SERVER}",
        password = password,
    )
    await manager_agent.start()

    truck_agent = TruckAgent(
        jid = f"{packing_agent_user}@{XMPP_SERVER}",
        password = password,
        operating_cost = 10,
        deliver_period = 10
    )
    await truck_agent.start()

    # inspection_agent = InspectionAgent(
    #     jid = f"{inspection_agent_user}@{XMPP_SERVER}",
    #     password = password,
    #     capacity= 10,
    #     duration= 10,
    #     operating_cost= 10,
    # )
    # await inspection_agent.start()



    while True:
        try:
            await asyncio.sleep(1)
        except KeyboardInterrupt:
            break

    # Pare os agentes
    await manager_agent.stop()
    await inspection_agent.stop()
    await truck_agent.stop()

if __name__ == "__main__":
    spade.run(main())