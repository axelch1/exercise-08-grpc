import os

import grpc
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response

import node_registry_pb2 as pb2
import node_registry_pb2_grpc as pb2_grpc

app = FastAPI(title="Node Registry Gateway")

GRPC_SERVER = os.getenv("GRPC_SERVER", "localhost:50051")


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


async def _parse_body(request: Request):
    ct = request.headers.get("content-type", "")
    if "json" in ct:
        try:
            return await request.json()
        except Exception:
            return {}
    try:
        form = await request.form()
        return dict(form)
    except Exception:
        return {}


@app.post("/api/nodes", status_code=201)
async def register(request: Request):
    body = await _parse_body(request)
    name = body.get("name") or request.query_params.get("name")
    address = body.get("address") or request.query_params.get("address")
    try:
        port = int(body.get("port") or request.query_params.get("port") or 0)
    except (ValueError, TypeError):
        port = 0
    stub = get_stub()
    try:
        resp = stub.Register(pb2.RegisterRequest(name=name, address=address, port=port))
    except grpc.RpcError:
        raise HTTPException(status_code=502, detail="gRPC server unavailable")
    return _build_node_response(resp)


@app.get("/api/nodes")
def list_nodes():
    try:
        stub = get_stub()
        resp = stub.List(pb2.Empty())
        return [_build_node_response(n) for n in resp.nodes]
    except grpc.RpcError:
        return []


@app.get("/api/nodes/{node_id}")
def get_node(node_id: int):
    stub = get_stub()
    try:
        resp = stub.Get(pb2.GetRequest(id=node_id))
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        raise HTTPException(status_code=502, detail="gRPC server unavailable")
    return _build_node_response(resp)


def _do_delete(node_id):
    stub = get_stub()
    try:
        stub.Delete(pb2.DeleteRequest(id=int(node_id)))
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        raise HTTPException(status_code=502, detail="gRPC server unavailable")


@app.delete("/api/nodes/{node_id}")
def delete_node(node_id: int):
    _do_delete(node_id)
    return Response(status_code=204)


@app.delete("/api/nodes")
async def delete_node_by_id(request: Request):
    body = await _parse_body(request)
    node_id = body.get("id") or body.get("node_id") or request.query_params.get("id") or request.query_params.get("node_id")
    if node_id is not None:
        _do_delete(node_id)
    return Response(status_code=204)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("GATEWAY_PORT", "8080")))
