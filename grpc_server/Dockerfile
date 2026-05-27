FROM python:3.12-slim

WORKDIR /app

COPY grpc_server/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY grpc_server/ grpc_server/
COPY node_registry_pb2*.py .

CMD ["python", "-m", "grpc_server.server"]
