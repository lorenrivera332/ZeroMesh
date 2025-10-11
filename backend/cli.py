"""
CLI интерфейс для управления локальным узлом ZeroMesh.
Позволяет запускать, останавливать и просматривать статус узла.
"""

import argparse
import asyncio
from node.relay_manager import RelayManager
from node.routing_table import RoutingTable

async def start_node(node_id: str):
    node = RelayManager(node_id)
    RoutingTable.register(node)
    print(f"[+] Узел {node_id} запущен.")
    await node.run_forever()

async def stop_node(node_id: str):
    RoutingTable.unregister(node_id)
    print(f"[-] Узел {node_id} остановлен.")

async def show_status():
    nodes = RoutingTable.list_nodes()
    if not nodes:
        print("Нет активных узлов.")
        return
    print("Активные узлы:")
    for n in nodes:
        print(f"  • {n.node_id} — соединений: {len(n.peers)}")

def main():
    parser = argparse.ArgumentParser(description="ZeroMesh CLI")
    parser.add_argument("command", choices=["start", "stop", "status"])
    parser.add_argument("--id", help="Идентификатор узла")

    args = parser.parse_args()

    if args.command == "start" and args.id:
        asyncio.run(start_node(args.id))
    elif args.command == "stop" and args.id:
        asyncio.run(stop_node(args.id))
    elif args.command == "status":
        asyncio.run(show_status())
    else:
        print("Ошибка: требуется указать --id для start/stop.")

if __name__ == "__main__":
    main()
