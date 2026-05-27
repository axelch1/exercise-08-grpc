import os
from datetime import datetime, timezone

import grpc
import sqlalchemy as sa
from sqlalchemy.orm import Session, declarative_base

import node_registry_pb2 as pb2
import node_registry_pb2_grpc as pb2_grpc

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://noderegistry:noderegistry@localhost:5432/noderegistry",
)

engine = sa.create_engine(DATABASE_URL)
Base = declarative_base()


class Node(Base):
    __tablename__ = "nodes"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    address = sa.Column(sa.String, nullable=False)
    port = sa.Column(sa.Integer, nullable=False)
    status = sa.Column(sa.String, default="online")
    created_at = sa.Column(sa.DateTime, default=lambda: datetime.now(timezone.utc))


class NodeRegistryServicer(pb2_grpc.NodeRegistryServicer):
    def Register(self, request, context):
        with Session(engine) as session:
            node = Node(
                name=request.name,
                address=request.address,
                port=request.port,
            )
            session.add(node)
            session.commit()
            session.refresh(node)
            return pb2.NodeResponse(
                id=node.id,
                name=node.name,
                address=node.address,
                port=node.port,
                status=node.status,
                created_at=node.created_at.isoformat(),
            )

    def List(self, request, context):
        with Session(engine) as session:
            nodes = session.query(Node).all()
            return pb2.NodeList(
                nodes=[
                    pb2.NodeResponse(
                        id=n.id,
                        name=n.name,
                        address=n.address,
                        port=n.port,
                        status=n.status,
                        created_at=n.created_at.isoformat(),
                    )
                    for n in nodes
                ]
            )

    def Get(self, request, context):
        with Session(engine) as session:
            node = session.get(Node, request.id)
            if node is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Node {request.id} not found")
                return pb2.NodeResponse()
            return pb2.NodeResponse(
                id=node.id,
                name=node.name,
                address=node.address,
                port=node.port,
                status=node.status,
                created_at=node.created_at.isoformat(),
            )

    def Delete(self, request, context):
        with Session(engine) as session:
            node = session.get(Node, request.id)
            if node is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Node {request.id} not found")
                return pb2.Empty()
            session.delete(node)
            session.commit()
            return pb2.Empty()


def serve():
    Base.metadata.create_all(engine)
    server = grpc.server(grpc.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_NodeRegistryServicer_to_server(NodeRegistryServicer(), server)
    port = os.getenv("GRPC_PORT", "50051")
    server.add_insecure_port(f"0.0.0.0:{port}")
    server.start()
    print(f"gRPC server listening on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
