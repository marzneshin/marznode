__default__:
	@echo "Please specify a target to make"

GEN=python3 -m grpc_tools.protoc -I. --python_out=. --grpclib_python_out=. --pyi_out=.
GENERATED=*{_pb2.py,_grpc.py,.pyi}

clean:
	rm -rf marznode/service/$(GENERATED)

proto: clean
	$(GEN) marznode/service/service.proto

