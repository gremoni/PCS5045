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
from spade.message import Message
from spade.template import Template
from aioxmpp import JID, forms


XMPP_SERVER = "nave"
PUBSUB_JID = f"pubsub.{XMPP_SERVER}"

SCALE_PUBSUB = "scale"
STOCK_PUBSUB = "stock"
CONVEYOR_BELT_1_PUBSUB = "conveyor_belt_1"
CONVEYOR_BELT_2_PUBSUB = "conveyor_belt_2"

class OperationAgent(Agent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, manager_user, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.operating_cost = operating_cost
        self.capacity = capacity
        self.duration = duration
        self.manager_user = manager_user
        self.start_time = datetime.now()


class TruckAgent(PubSubMixin, Agent):
    def __init__(self, jid: str, password: str, operating_cost, deliver_period, manager_user, verify_security: bool = False):
        self.operating_cost = operating_cost
        self.deliver_period = deliver_period
        self.manager_user = manager_user
        self.start_delay = 10
        self.deliver_amounts = [1000, 1500, 2000, 2500, 3000]
        super().__init__(jid, password, verify_security)
    
    class SetPublishAffiliationBehav(OneShotBehaviour):
        async def run(self):
            msg = Message(to=f"{self.agent.manager_user}@{XMPP_SERVER}")
            msg.set_metadata("performative", "request")
            msg.set_metadata("action", "affiliation_publish")
            msg.body = STOCK_PUBSUB
            await self.send(msg)

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
        self.add_behaviour(self.SetPublishAffiliationBehav())
        start_at = datetime.now() + timedelta(seconds=self.start_delay)
        deliver_behav = self.TruckDeliverBehav(period = self.deliver_period,
                                               start_at = start_at,
                                               pubsub = self.pubsub)
        self.add_behaviour(deliver_behav)

class ProductionAgent(PubSubMixin, OperationAgent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, manager_user, activity : str, receive_pubsub, deliver_pubsub, verify_security: bool = False):
        self.activity = activity
        self.receive_pubsub = receive_pubsub
        self.deliver_pubsub = deliver_pubsub
        self.stock = 0
        super().__init__(jid, password, operating_cost, capacity, duration, manager_user, verify_security)
    
    def receive_callback(self, jid, node, item, message=None):
        if node == self.receive_pubsub:
            received_amount = int(item.registered_payload.data)
            print(f"[{self.name}] Received: [{node}] -> {str(received_amount)}")
            self.stock += received_amount
    
    class SetPublishAffiliationBehav(OneShotBehaviour):
        async def run(self):
            msg = Message(to=f"{self.agent.manager_user}@{XMPP_SERVER}")
            msg.set_metadata("performative", "request")
            msg.set_metadata("action", "affiliation_publish")
            msg.body = self.agent.deliver_pubsub
            await self.send(msg)

    class ProcessStockBehav(CyclicBehaviour):
        def __init__(self, pubsub : PubSubMixin.PubSubComponent):
            self.pubsub = pubsub
            super().__init__()

        async def on_start(self):
           print(f"[{self.agent.name}] Starting Process {self.agent.activity} Behav")

        async def run(self):
            processed = 0
            if self.agent.stock > 0:
                if self.agent.stock > self.agent.capacity:
                    processed = self.agent.capacity
                    self.agent.stock -= self.agent.capacity
                else:
                    processed = self.agent.stock
                    self.agent.stock = 0
                await asyncio.sleep(self.agent.duration)
                await self.pubsub.publish(PUBSUB_JID, self.agent.deliver_pubsub, str(processed))
                print(f"[{self.agent.name}] {self.agent.activity} Processed  {processed}")
                print(f"[{self.agent.name}] {self.agent.activity} Stock  {self.agent.stock}")
            else:
                await asyncio.sleep(5)
    
    async def setup(self):
        self.presence.approve_all = True
        self.presence.set_available()
        await self.pubsub.subscribe(PUBSUB_JID, self.receive_pubsub)
        self.add_behaviour(self.SetPublishAffiliationBehav())
        self.pubsub.set_on_item_published(self.receive_callback)
        self.add_behaviour(self.ProcessStockBehav(self.pubsub))


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
    
    class ChangeAffiliationPublishBehav(CyclicBehaviour):
      async def run(self):
          msg = await self.receive(timeout=10) # wait for a message for 10 seconds
          if msg:
              node = msg.body
              requester_jid = msg.sender
              await self.agent.pubsub.change_node_affiliations(PUBSUB_JID, node, [(requester_jid, "publisher")])
              print(f"[{self.agent.name}] Updated Affiliation Agent: {requester_jid.localpart} Node: {node} Affiliation: Publisher")         

    
    async def setup(self):
        try:
            await self.pubsub.create(PUBSUB_JID, SCALE_PUBSUB)
        except:
            print(f"[{self.name}] Node {SCALE_PUBSUB} already exists")
        try:
            await self.pubsub.create(PUBSUB_JID, STOCK_PUBSUB)
        except:
            print(f"[{self.name}] Node {STOCK_PUBSUB} already exists")
        try:
            await self.pubsub.create(PUBSUB_JID, CONVEYOR_BELT_1_PUBSUB)
        except:
            print(f"[{self.name}] Node {CONVEYOR_BELT_1_PUBSUB} already exists")
        try:
            await self.pubsub.create(PUBSUB_JID, CONVEYOR_BELT_2_PUBSUB)
        except:
            print(f"[{self.name}] Node {CONVEYOR_BELT_2_PUBSUB} already exists")
        
        change_affiliation_template = Template()
        change_affiliation_template.set_metadata("performative", "request")
        change_affiliation_template.set_metadata("action", "affiliation_publish")
        change_affiliation_behav = self.ChangeAffiliationPublishBehav()
        self.add_behaviour(change_affiliation_behav, change_affiliation_template)
        

# class BoxingAgent(OperationAgent):


async def main():
    manager_agent_user = "agente1"
    truck_agent_user = "agente2"
    slicer_agent_user = "agente3"
    fryer_agent_user = "agente4"
    password = "senhadoagente"

    manager_agent = ManagerAgent(
        jid = f"{manager_agent_user}@{XMPP_SERVER}",
        password = password,
    )
    await manager_agent.start()

    truck_agent = TruckAgent(
        jid = f"{truck_agent_user}@{XMPP_SERVER}",
        password = password,
        operating_cost = 10,
        deliver_period = 100,
        manager_user = manager_agent_user
    )
    await truck_agent.start()

    slicer_agent = ProductionAgent(
        jid = f"{slicer_agent_user}@{XMPP_SERVER}",
        password = password,
        capacity= 150,
        duration= 5,
        operating_cost= 12,
        manager_user= manager_agent_user,
        activity= "SLICER",
        receive_pubsub= STOCK_PUBSUB,
        deliver_pubsub= CONVEYOR_BELT_1_PUBSUB
    )
    await slicer_agent.start()

    fryer_agent = ProductionAgent(
        jid = f"{fryer_agent_user}@{XMPP_SERVER}",
        password = password,
        capacity= 200,
        duration= 8,
        operating_cost= 21,
        manager_user= manager_agent_user,
        activity= "FRYER",
        receive_pubsub= CONVEYOR_BELT_1_PUBSUB,
        deliver_pubsub= CONVEYOR_BELT_2_PUBSUB
    )
    await fryer_agent.start()

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
    await truck_agent.stop()
    await slicer_agent.stop()
    await fryer_agent.stop()

if __name__ == "__main__":
    spade.run(main())