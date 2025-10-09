# tests/test_mesh_topology.py
import asyncio
import pytest

from node.relay_manager import RelayManager
from node.routing_table import RoutingTable
from node.peer_discovery import PeerDiscovery
from protocols.gossip import GossipProtocol
from protocols.file_transfer import FileTransferProtocol


@pytest.mark.asyncio
async def test_mesh_topology_basic():
    """Проверяем, что три узла образуют сеть и могут пересылать сообщения через ретрансляцию."""

    # создаём три узла
    node_a = RelayManager(node_id="A")
    node_b = RelayManager(node_id="B")
    node_c = RelayManager(node_id="C")

    # симулируем соединения
    node_a.connect(node_b)
    node_b.connect(node_c)

    # таблицы маршрутизации
    RoutingTable.register(node_a)
    RoutingTable.register(node_b)
    RoutingTable.register(node_c)

    # убеждаемся, что через B можно доставить сообщение из A → C
    message = {"type": "ping", "payload": "hello"}
    result = await node_a.send_message("C", message)

    assert result["status"] == "delivered"
    assert result["hops"] == 2


@pytest.mark.asyncio
async def test_dynamic_peer_discovery():
    """Проверяем, что новый узел автоматически находится соседями."""
    discovery = PeerDiscovery()

    existing_nodes = [
        {"id": "A", "addr": "192.168.0.2"},
        {"id": "B", "addr": "192.168.0.3"},
    ]
    new_node = {"id": "C", "addr": "192.168.0.4"}

    peers = await discovery.scan_network(existing_nodes + [new_node])
    ids = [p["id"] for p in peers]

    assert "C" in ids
    assert len(ids) == 3


@pytest.mark.asyncio
async def test_gossip_broadcast():
    """Проверяем распространение сообщения по протоколу Gossip."""
    gossip = GossipProtocol()

    messages = []
    async def handler(node_id, msg):
        messages.append((node_id, msg))

    # Регистрируем 3 узла и общий callback
    gossip.register_node("A", handler)
    gossip.register_node("B", handler)
    gossip.register_node("C", handler)

    await gossip.broadcast("A", {"type": "status", "data": "OK"})

    # Проверяем, что сообщение получили все
    assert len(messages) == 2  # кроме отправителя
    ids = [m[0] for m in messages]
    assert "B" in ids and "C" in ids


@pytest.mark.asyncio
async def test_file_transfer_integrity(tmp_path):
    """Проверяем передачу файла между двумя узлами."""
    ft = FileTransferProtocol()
    src_file = tmp_path / "source.txt"
    dst_file = tmp_path / "received.txt"

    # создаём тестовый файл
    src_file.write_text("hello mesh network")

    # передаём
    success = await ft.transfer("A", "B", src_file, dst_file)
    assert success
    assert dst_file.read_text() == "hello mesh network"


@pytest.mark.asyncio
async def test_node_failure_recovery():
    """Проверяем устойчивость при падении узла."""
    node_a = RelayManager("A")
    node_b = RelayManager("B")
    node_c = RelayManager("C")

    node_a.connect(node_b)
    node_b.connect(node_c)

    RoutingTable.register(node_a)
    RoutingTable.register(node_b)
    RoutingTable.register(node_c)

    # отключаем B
    node_b.alive = False

    # сообщение A→C должно не доставиться
    result = await node_a.send_message("C", {"type": "ping"})
    assert result["status"] == "failed"
