import os

import grpc
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import node_registry_pb2 as pb2
import node_registry_pb2_grpc as pb2_grpc

app = FastAPI(title="Node Registry Gateway")

GRPC_SERVER = os.getenv("GRPC_SERVER", "localhost:50051")


class RegisterNodeRequest(BaseModel):
    name: str
    address: str
    port: int


def get_stub():
    channel = grpc.insecure_channel(GRPC_SERVER)
    return pb2_grpc.NodeRegistryStub(channel)


def _build_node_response(resp):
    return {
        "id": resp.id,
        "name": resp.name,
        "address": resp.address,
        "port": resp.port,
        "status": resp.status,
        "created_at": resp.created_at,
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/nodes", status_code=201)
def register(body: RegisterNodeRequest):
    stub = get_stub()
    resp = stub.Register(
        pb2.RegisterRequest(name=body.name, address=body.address, port=body.port)
    )
    return _build_node_response(resp)


@app.get("/api/nodes")
def list_nodes():
    stub = get_stub()
    resp = stub.List(pb2.Empty())
    return [_build_node_response(n) for n in resp.nodes]


@app.get("/api/nodes/{node_id}")
def get_node(node_id: int):
    stub = get_stub()
    try:
        resp = stub.Get(pb2.GetRequest(id=node_id))
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        raise
    return _build_node_response(resp)


@app.delete("/api/nodes/{node_id}")
def delete_node(node_id: int):
    stub = get_stub()
    try:
        stub.Delete(pb2.DeleteRequest(id=node_id))
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        raise
    return {"message": "Node deleted"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("GATEWAY_PORT", "8080")))
