all: registry scheduler

registry:
	python -m grpc_tools.protoc -Iprotos=./protos --python_out=./protos --grpc_python_out=./protos ./protos/registry.proto

scheduler:
	python -m grpc_tools.protoc -Iprotos=./protos --python_out=./protos --grpc_python_out=./protos ./protos/scheduler.proto
