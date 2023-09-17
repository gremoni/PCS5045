import asyncio
import json
import asyncio
from typing import Optional
import spade
import json
import random
import csv

from typing import List
from datetime import datetime, timedelta
from spade_artifact import Artifact, ArtifactMixin
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour, TimeoutBehaviour, FSMBehaviour, State
from spade_pubsub import PubSubMixin
from spade.agent import Agent
from spade.message import Message
from spade.template import Template
from aioxmpp import JID, forms

XMPP_SERVER = "desktop-5tqm7ia.mshome.net"
PUBSUB_JID = f"pubsub.{XMPP_SERVER}"

STOCK_PUBSUB = "stock"
CONVEYOR_BELT_1_PUBSUB = "conveyor_belt_1"
CONVEYOR_BELT_2_PUBSUB = "conveyor_belt_2"
CONVEYOR_BELT_3_PUBSUB = "conveyor_belt_3"
SCALE_PUBSUB = "scale"

# Inicialize uma lista vazia para armazenar os dados de produção em tempo real
realtime_production_data = []


class OperationAgent(Agent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, manager_user,
                 verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.operating_cost = operating_cost
        self.capacity = capacity
        self.duration = duration
        self.manager_user = manager_user
        self.start_time = datetime.now()


class TruckAgent(PubSubMixin, Agent):
    def __init__(self, jid: str, password: str, operating_cost, deliver_period, manager_user,
                 verify_security: bool = False):
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
        def __init__(self, period: float, start_at: datetime, pubsub: PubSubMixin.PubSubComponent):
            self.pubsub = pubsub
            super().__init__(period, start_at)

        async def on_start(self):
            print(f"[{self.agent.name}] Starting Truck Deliver Behav")

        async def run(self):
            deliver_amount = random.choice(self.agent.deliver_amounts)

            while True:
                processed = 0
                if self.stock > 0:

                    try:
                        await self.pubsub.publish(PUBSUB_JID, STOCK_PUBSUB, str(deliver_amount))
                    except Exception:
                        print(f"[{self.agent.name}] {STOCK_PUBSUB} PubSub Error")

                    print(f"[{self.agent.name}] Delivered {deliver_amount}")
                    random_delay_time = random.randrange(0, 20, 2)
                    await asyncio.sleep(random_delay_time)

                    production_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    quantity_produced = processed  # Substitua pela sua variável real de quantidade produzida
                    realtime_production_data.append({"timestamp": production_timestamp, "quantity": quantity_produced})

    async def setup(self):
        self.affiliation_behav = self.SetPublishAffiliationBehav()
        self.add_behaviour(self.affiliation_behav)
        start_at = datetime.now() + timedelta(seconds=self.start_delay)
        deliver_behav = self.TruckDeliverBehav(period=self.deliver_period,
                                               start_at=start_at,
                                               pubsub=self.pubsub)
        self.add_behaviour(deliver_behav)


class ProductionAgent(PubSubMixin, OperationAgent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, manager_user, activity : str, receive_pubsub, deliver_pubsub, verify_security: bool = False):

        self.activity = activity
        self.receive_pubsub = receive_pubsub
        self.deliver_pubsub = deliver_pubsub
        self.stock = 0
        super().__init__(jid, password, operating_cost, capacity, duration, manager_user, verify_security)
        self.csv_file = 'production_data.csv'  # Nome do arquivo CSV


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
        def __init__(self, pubsub: PubSubMixin.PubSubComponent):
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

                # Obtenha a data e hora atual
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Escreva os dados no arquivo CSV
                self.agent.csv_writer.writerow([current_time, processed])
                self.agent.csv_file_handle.flush()  # Força a gravação imediata dos dados no arquivo

                await self.agent.pubsub.publish(PUBSUB_JID, self.agent.deliver_pubsub, str(processed))
                print(f"[{self.agent.name}] {self.agent.activity} Processed  {processed}")
                print(f"[{self.agent.name}] {self.agent.activity} Stock  {self.agent.stock}")
            else:
                await asyncio.sleep(5)

            # Após processar os produtos, salve os dados no arquivo CSV
            self.agent.save_data_to_csv(processed)

    def save_data_to_csv(self, processed):
        # Use o csv_writer para escrever os dados no arquivo CSV
        data = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), processed]
        self.csv_writer.writerow(data)

    async def setup(self):
        self.presence.approve_all = True
        self.presence.set_available()
        await self.pubsub.subscribe(PUBSUB_JID, self.receive_pubsub)
        self.affiliation_behav = self.SetPublishAffiliationBehav()
        self.add_behaviour(self.affiliation_behav)
        self.pubsub.set_on_item_published(self.receive_callback)
        self.add_behaviour(self.ProcessStockBehav(self.pubsub))
        # self.csv_writer = csv.writer(open(self.csv_file, mode='w', newline=''))
        self.csv_file_handle = open(self.csv_file, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file_handle)
        self.csv_writer.writerow(['Data', 'Quantidade Produzida'])  # Escreva o cabeçalho no arquivo CSV


class QualityControlAgent(PubSubMixin, OperationAgent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, manager_user, activity: str,
                 receive_pubsub, deliver_pubsub, return_pubsub, verify_security: bool = False):
        self.activity = activity
        self.receive_pubsub = receive_pubsub
        self.deliver_pubsub = deliver_pubsub
        self.return_pubsub = return_pubsub
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

            msg2 = Message(to=f"{self.agent.manager_user}@{XMPP_SERVER}")
            msg2.set_metadata("performative", "request")
            msg2.set_metadata("action", "affiliation_publish")
            msg2.body = self.agent.return_pubsub
            await self.send(msg2)

    class QualityControlBehav(CyclicBehaviour):
        def __init__(self, pubsub: PubSubMixin.PubSubComponent):
            self.pubsub = pubsub
            super().__init__()

        async def on_start(self):
            print(f"[{self.agent.name}] Starting Process {self.agent.activity} Behav")

        def quality_analysis(self):
            value = random.randint(0, 9)
            if value == 0:
                return None
            elif value == 1:
                return self.agent.return_pubsub
            else:
                return self.agent.deliver_pubsub

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

                print(f"[{self.agent.name}] {self.agent.activity} Processed  {processed}")
                analysis_result = self.quality_analysis()
                if analysis_result is None:
                    print(f"[{self.agent.name}] Quality analysis defective. Dropping product.")
                elif analysis_result == self.agent.return_pubsub:
                    print(f"[{self.agent.name}] Quality analysis not ready. Returning product.")
                    await self.pubsub.publish(PUBSUB_JID, self.agent.return_pubsub, str(processed))
                elif analysis_result == self.agent.deliver_pubsub:
                    print(f"[{self.agent.name}] Quality analysis passed. Delivering product.")
                    await self.pubsub.publish(PUBSUB_JID, self.agent.deliver_pubsub, str(processed))
                else:
                    print(f"[{self.agent.name}] Quality analysis failed!!!!!")

                print(f"[{self.agent.name}] {self.agent.activity} Stock  {self.agent.stock}")
            else:
                await asyncio.sleep(5)

    async def setup(self):
        self.presence.approve_all = True
        self.presence.set_available()
        await self.pubsub.subscribe(PUBSUB_JID, self.receive_pubsub)
        self.add_behaviour(self.SetPublishAffiliationBehav())
        self.pubsub.set_on_item_published(self.receive_callback)
        self.add_behaviour(self.QualityControlBehav(self.pubsub))


class FillingAgent(PubSubMixin, OperationAgent):
    def __init__(self, jid: str, password: str, operating_cost, capacity, duration, manager_user, activity: str,
                 batch_size, receive_pubsub, deliver_pubsub, verify_security: bool = False):
        self.activity = activity
        if capacity % batch_size != 0:
            raise ValueError("capacity must be multiple of batch_size")
        self.batch_size = batch_size
        self.receive_pubsub = receive_pubsub
        self.deliver_pubsub = deliver_pubsub
        self.stock = 0
        super().__init__(jid, password, operating_cost, capacity, duration, manager_user, verify_security)

    def receive_callback(self, jid, node, item, message=None):
        if node == self.receive_pubsub:
            received_amount = int(item.registered_payload.data)
            print(f"[{self.name}] Received: [{node}] -> {str(received_amount)}")
            self.stock += received_amount

    class FillWithStockBehav(CyclicBehaviour):
        def __init__(self, pubsub: PubSubMixin.PubSubComponent):
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
                elif self.agent.stock > self.agent.batch_size:
                    processed = int(self.agent.stock / self.agent.batch_size)
                    self.agent.stock = self.agent.stock % self.agent.batch_size

                await asyncio.sleep(self.agent.duration)
                await self.pubsub.publish(PUBSUB_JID, self.agent.deliver_pubsub, str(processed))
                print(f"[{self.agent.name}] {self.agent.activity} Processed  {processed}")
                print(f"[{self.agent.name}] {self.agent.activity} Stock  {self.agent.stock}")
            else:
                await asyncio.sleep(5)

    class SetPublishAffiliationBehav(OneShotBehaviour):
        async def run(self):
            msg = Message(to=f"{self.agent.manager_user}@{XMPP_SERVER}")
            msg.set_metadata("performative", "request")
            msg.set_metadata("action", "affiliation_publish")
            msg.body = self.agent.deliver_pubsub
            await self.send(msg)

    async def setup(self):
        self.presence.approve_all = True
        self.presence.set_available()
        await self.pubsub.subscribe(PUBSUB_JID, self.receive_pubsub)
        self.affiliation_behav = self.SetPublishAffiliationBehav()
        self.add_behaviour(self.affiliation_behav)
        self.pubsub.set_on_item_published(self.receive_callback)
        self.add_behaviour(self.FillWithStockBehav(self.pubsub))


class ManagerAgent(PubSubMixin, Agent):
    def __init__(self, jid: str, password: str, nodelist: List[str], verify_security: bool = False):
        self.nodelist = nodelist
        super().__init__(jid, password, verify_security)

    class ChangeAffiliationPublishBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            if msg:
                node = msg.body
                requester_jid = msg.sender
                await self.agent.pubsub.change_node_affiliations(PUBSUB_JID, node, [(requester_jid, "publisher")])
                print(
                    f"[{self.agent.name}] Updated Affiliation Agent: {requester_jid.localpart} Node: {node} Affiliation: Publisher")

    async def setup(self):
        for node in self.nodelist:
            try:
                await self.pubsub.create(PUBSUB_JID, node)
                print(f"[{self.name}] Created node {node}")
            except:
                print(f"[{self.name}] Node {node} already exists")

        change_affiliation_template = Template()
        change_affiliation_template.set_metadata("performative", "request")
        change_affiliation_template.set_metadata("action", "affiliation_publish")
        change_affiliation_behav = self.ChangeAffiliationPublishBehav()
        self.add_behaviour(change_affiliation_behav, change_affiliation_template)


async def main():
    manager_agent_user = "agente1"
    truck_agent_user = "agente2"
    slicer_agent_user = "agente3"
    fryer_agent_user = "agente4"
    quality_agent_user = "agente5"
    packing_agent_user = "agente6"
    password = "senhadoagente"

    manager_agent = ManagerAgent(
        jid=f"{manager_agent_user}@{XMPP_SERVER}",
        password=password,
        nodelist=[STOCK_PUBSUB, CONVEYOR_BELT_1_PUBSUB, CONVEYOR_BELT_2_PUBSUB, SCALE_PUBSUB, CONVEYOR_BELT_3_PUBSUB]
    )
    await manager_agent.start()

    truck_agent = TruckAgent(
        jid=f"{truck_agent_user}@{XMPP_SERVER}",
        password=password,
        operating_cost=10,
        deliver_period=100,
        manager_user=manager_agent_user
    )
    await truck_agent.start()

    slicer_agent = ProductionAgent(
        jid=f"{slicer_agent_user}@{XMPP_SERVER}",
        password=password,
        capacity=150,
        duration=5,
        operating_cost=12,
        manager_user=manager_agent_user,
        activity="SLICER",
        receive_pubsub=STOCK_PUBSUB,
        deliver_pubsub=CONVEYOR_BELT_1_PUBSUB
    )
    await slicer_agent.start()

    fryer_agent = ProductionAgent(
        jid=f"{fryer_agent_user}@{XMPP_SERVER}",
        password=password,
        capacity=200,
        duration=8,
        operating_cost=21,
        manager_user=manager_agent_user,
        activity="FRYER",
        receive_pubsub=CONVEYOR_BELT_1_PUBSUB,
        deliver_pubsub=CONVEYOR_BELT_2_PUBSUB
    )
    await fryer_agent.start()

    quality_agent = QualityControlAgent(
        jid=f"{quality_agent_user}@{XMPP_SERVER}",
        password=password,
        capacity=100,
        duration=5,
        operating_cost=17,
        manager_user=manager_agent_user,
        activity="QUALITY",
        receive_pubsub=CONVEYOR_BELT_2_PUBSUB,
        deliver_pubsub=SCALE_PUBSUB,
        return_pubsub=CONVEYOR_BELT_1_PUBSUB
    )
    await quality_agent.start()

    packing_agent = FillingAgent(
        jid=f"{packing_agent_user}@{XMPP_SERVER}",
        password=password,
        capacity=200,
        batch_size=50,
        duration=8,
        operating_cost=21,
        manager_user=manager_agent_user,
        activity="PACKING",
        receive_pubsub=SCALE_PUBSUB,
        deliver_pubsub=CONVEYOR_BELT_3_PUBSUB
    )
    await packing_agent.start()

    while True:
        try:
            await asyncio.sleep(1)
        except KeyboardInterrupt:
            break

    # Após a simulação, salve os dados de produção em um arquivo CSV
    save_production_data_to_csv(realtime_production_data)

    # Pare os agentes
    await manager_agent.stop()
    await truck_agent.stop()
    await slicer_agent.stop()
    await fryer_agent.stop()
    await quality_agent.stop()

    save_production_data_to_csv(realtime_production_data)

def save_production_data_to_csv(data):
    output_csv_file = 'production_data.csv'

    with open(output_csv_file, 'w', newline='') as csv_file:
        fieldnames = ['timestamp', 'quantity']
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        csv_writer.writeheader()

        for entry in data:
            csv_writer.writerow(entry)


if __name__ == "__main__":
    spade.run(main())


# Lê os dados de produção do arquivo CSV (substitua 'production_data.csv' pelo nome do seu arquivo)
with open('production_data.csv', 'r') as csv_file:
    reader = csv.reader(csv_file)
    next(reader)  # Pula o cabeçalho, se houver
    data = list(reader)

# Extrai as colunas de data e quantidade produzida
dates = [row[0] for row in data]
quantities_produced = [int(row[1]) for row in data]

# Chama o production_chart.py com os dados como argumentos
subprocess.run(["python", "production_chart.py", ",".join(dates), ",".join(map(str, quantities_produced))])