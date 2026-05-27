FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gateway/ gateway/
COPY proto/ proto/
COPY node_registry_pb2*.py .

RUN python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/node_registry.proto

CMD ["python", "-m", "gateway.app"]
