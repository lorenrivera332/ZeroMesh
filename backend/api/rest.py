


"""
A simple REST API for managing a ZeroMesh node via HTTP.
Allows you to check status, peer list, and send messages.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from node.routing_table import RoutingTable

app = FastAPI(title="ZeroMesh Node API")

class MessageRequest(BaseModel):
    target_id: str
    payload: dict

@app.get("/status")
def status():
    nodes = [n.node_id for n in RoutingTable.list_nodes()]
    return {"active_nodes": nodes}

@app.get("/peers/{node_id}")
def peers(node_id: str):
    node = RoutingTable.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"node": node_id, "peers": node.peers}

@app.post("/send/{node_id}")
async def send_message(node_id: str, request: MessageRequest):
    node = RoutingTable.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    result = await node.send_message(request.target_id, request.payload)
    return result

@app.delete("/node/{node_id}")
def remove_node(node_id: str):
    RoutingTable.unregister(node_id)
    return {"status": f"Node {node_id} removed"}
