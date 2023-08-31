import asyncio
import spade
import json
import random

from datetime import datetime
from spade_artifact import Artifact, ArtifactMixin
from spade_pubsub import PubSubMixin
from spade.agent import Agent

XMPP_SERVER = "localhost"
PUBSUB_JID = "pubsub.localhost"

TRUCK_PUBSUB = "truck"

class OperationAgent(Agent):
    def __init__(self, jid: str, password: str, operating_cost, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.operating_cost = operating_cost
        self.start_time = datetime.now()


class TransportAgent(ArtifactMixin, OperationAgent):
    def __init__(self, *args, artifact_jid: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.artifact_jid = artifact_jid

    def truck_callback(self, artifact, payload):
        print(f"Received: [{artifact}] -> {payload}")
    
    async def setup(self):
        self.presence.approve_all = True
        self.presence.subscribe(self.artifact_jid)
        self.presence.set_available()
        await self.artifacts.focus(self.artifact_jid, self.truck_callback)
    
class ProductionAgent(OperationAgent):
    
    
class PackingAgent(ArtifactMixin, OperationAgent):
    def __init__(self, *args, artifact_jid: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.artifact_jid = artifact_jid

    def scale_callback(self, artifact, payload):
        print(f"Received: [{artifact}] -> {payload}")
    
    async def setup(self):
        self.presence.approve_all = True
        self.presence.subscribe(self.artifact_jid)
        self.presence.set_available()
        await self.artifacts.focus(self.artifact_jid, self.scale_callback)
    
    
class BoxingAgent(OperationAgent):
    
    
class InspectionAgent(OperationAgent):
    def __init__(self, jid: str, password: str, operating_cost, scale_node: str = None, verify_security: bool = False):
        super().__init__(jid, password, operating_cost, verify_security)
        self.scale_node = scale_node

    class WriteToScaleBehav(OneShotBehaviour):
        async def on_start(self):
           

        async def run(self):
            amount = 100
            await self.agent.pubsub.publish(PUBSUB_JID, self.agent.scale_node, amount)


    async def setup(self):
        if self.scale_node != None:
            await self.agent.pubsub.subscribe(PUBSUB_JID, self.scale_node)

class ManagerAgent(PubSubMixin, Agent):
    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)

    
    async def setup(self):
        





class TruckArtifact(Artifact):
    def on_available(self, jid, stanza):
       print(
            "[{}] Agent {} is available.".format(self.name, jid.split("@")[0])
        )

    def on_subscribed(self, jid):
       print(
            "[{}] Agent {} has accepted the subscription.".format(
                self.name, jid.split("@")[0]
            )
        )
       print(
            "[{}] Contacts List: {}".format(self.name, self.presence.get_contacts())
        )

    def on_subscribe(self, jid):
       print(
            "[{}] Agent {} asked for subscription. Let's aprove it.".format(
                self.name, jid.split("@")[0]
            )
        )
        self.presence.approve(jid)
        self.presence.subscribe(jid)

    async def setup(self):
        # Approve all contact requests
        self.presence.set_available()
        self.presence.on_subscribe = self.on_subscribe
        self.presence.on_subscribed = self.on_subscribed
        self.presence.on_available = self.on_available

    async def run(self):

        while True:
            # Publish only if my friends are online
            if len(self.presence.get_contacts()) >= 1:
                random_num = random.randint(0, 100)
                await self.publish(f"{random_num}")
                print(f"Publishing {random_num}")
            await asyncio.sleep(1)



class ScaleArtifact(Artifact):
    def on_available(self, jid, stanza):
       print(
            "[{}] Agent {} is available.".format(self.name, jid.split("@")[0])
        )

    def on_subscribed(self, jid):
       print(
            "[{}] Agent {} has accepted the subscription.".format(
                self.name, jid.split("@")[0]
            )
        )
       print(
            "[{}] Contacts List: {}".format(self.name, self.presence.get_contacts())
        )

    def on_subscribe(self, jid):
       print(
            "[{}] Agent {} asked for subscription. Let's aprove it.".format(
                self.name, jid.split("@")[0]
            )
        )
        self.presence.approve(jid)
        self.presence.subscribe(jid)

    async def setup(self):
        # Approve all contact requests
        self.presence.set_available()
        self.presence.on_subscribe = self.on_subscribe
        self.presence.on_subscribed = self.on_subscribed
        self.presence.on_available = self.on_available

    async def run(self):


async def main():
    truck_artifact_user = ""
    transport_agent_user = ""
    password = "senha"

    transport_agent = TransportAgent(
        jid = f"{transport_agent}@{XMPP_SERVER}", 
        password = password, 
        artifact_jid = f"{truck_artifact}@{XMPP_SERVER}"
    )
    transport_agent.start()

    truck_artifact = TruckArtifact(
        jid = f"{truck_artifact}@{XMPP_SERVER}", 
        password = password)

    future = truck_artifact.start()
    future.result()

    truck_artifact.join()

if __name__ == "__main__":
    spade.run(main())