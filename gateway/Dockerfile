FROM python:3.12-slim

WORKDIR /app

COPY gateway/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY gateway/ gateway/
COPY node_registry_pb2*.py .

CMD ["python", "-m", "gateway.app"]
