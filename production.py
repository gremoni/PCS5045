import asyncio
import spade
import json
import random

from datetime import datetime
from spade_artifact import Artifact, ArtifactMixin
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour, TimeoutBehaviour, FSMBehaviour, State
from spade_pubsub import PubSubMixin
from spade.agent import Agent

XMPP_SERVER = "nave"
PUBSUB_JID = "pubsub.nave"

SCALE_PUBSUB = "scale"

class OperationAgent(Agent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.operating_cost = operating_cost
        self.capacity = capacity
        self.duration = duration
        self.start_time = datetime.now()


class TransportAgent(ArtifactMixin, OperationAgent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, artifact_jid, pubsub_server=None, *args, **kwargs):
        super.__init__(self=self,
                        jid=jid,
                        password= password,
                        operating_cost= operating_cost,
                        capacity= capacity,
                        duration= duration, pubsub_server=pubsub_server, *args, **kwargs)


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

# class ProductionAgent(OperationAgent):



# class PackingAgent(ArtifactMixin, OperationAgent):
#     def __init__(self, *args, artifact_jid: str = None, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.artifact_jid = artifact_jid

#     def scale_callback(self, artifact, payload):
#         print(f"Received: [{artifact}] -> {payload}")

#     async def setup(self):
#         self.presence.approve_all = True
#         self.presence.subscribe(self.artifact_jid)
#         self.presence.set_available()
#         await self.artifacts.focus(self.artifact_jid, self.scale_callback)


# class BoxingAgent(OperationAgent):


# class InspectionAgent(PubSubMixin, OperationAgent):
#     def __init__(self, jid: str, password: str, operating_cost, verify_security: bool = False):
#         super().__init__(jid, password, operating_cost, verify_security)

#     class WriteToScaleBehav(OneShotBehaviour):
#         async def on_start(self):


#         async def run(self):
#             amount = 100
#             await self.agent.pubsub.publish(PUBSUB_JID, SCALE_PUBSUB, amount)


#     async def setup(self):
#         await self.pubsub.subscribe(PUBSUB_JID, SCALE_PUBSUB)


# class ManagerAgent(PubSubMixin, Agent):
#     def __init__(self, jid: str, password: str, verify_security: bool = False):
#         super().__init__(jid, password, verify_security)


#     async def setup(self):
#         await self.pubsub.create(PUBSUB_JID, SCALE_PUBSUB)




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
            if len(self.presence.get_contacts()) >= 1:
                random_num = random.randint(0, 100)
                await self.publish(f"{random_num}")
                print(f"Publishing {random_num}")
            await asyncio.sleep(30)



# class ScaleArtifact(Artifact):
#     def on_available(self, jid, stanza):
#        print(
#             "[{}] Agent {} is available.".format(self.name, jid.split("@")[0])
#         )

#     def on_subscribed(self, jid):
#        print(
#             "[{}] Agent {} has accepted the subscription.".format(
#                 self.name, jid.split("@")[0]
#             )
#         )
#        print(
#             "[{}] Contacts List: {}".format(self.name, self.presence.get_contacts())
#         )

#     def on_subscribe(self, jid):
#        print(
#             "[{}] Agent {} asked for subscription. Let's aprove it.".format(
#                 self.name, jid.split("@")[0]
#             )
#         )
#         self.presence.approve(jid)
#         self.presence.subscribe(jid)

#     async def setup(self):
#         # Approve all contact requests
#         self.presence.set_available()
#         self.presence.on_subscribe = self.on_subscribe
#         self.presence.on_subscribed = self.on_subscribed
#         self.presence.on_available = self.on_available

#     async def run(self):


async def main():
    truck_artifact_user = "agente1"
    transport_agent_user = "agente2"
    password = "senhadoagente"

    truck_artifact = TruckArtifact(
        jid = f"{truck_artifact_user}@{XMPP_SERVER}",
        password = password
    )

    future = truck_artifact.start()
    future.result()

    truck_artifact.join()

    transport_agent = TransportAgent(
        jid = f"{transport_agent_user}@{XMPP_SERVER}",
        password = password,
        capacity= 10,
        duration= 10,
        operating_cost= 10,
        artifact_jid = f"{truck_artifact_user}@{XMPP_SERVER}"
    )
    await transport_agent.start()



if __name__ == "__main__":
    spade.run(main())