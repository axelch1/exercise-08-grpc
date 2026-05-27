proto:
	python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/node_registry.proto

run-grpc-server:
	python -m grpc_server.server

run-gateway:
	python -m gateway.app

.PHONY: proto run-grpc-server run-gateway
