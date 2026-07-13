import sys
import os
from concurrent import futures
import grpc
import time

# Ensure the proto directory is in path for imports
_gen_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated'))

# Append it
sys.path.append(_gen_path)
import energy_pb2_grpc
from service_impl import EnergyOrchestratorServicer

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    energy_pb2_grpc.add_EnergyOrchestratorServicer_to_server(
        EnergyOrchestratorServicer(), server
    )
    
    port = "[::]:50051"
    server.add_insecure_port(port)
    print(f"[gRPC Server] Orchestration service actively running on port {port}...")
    server.start()
    
    print("---------------------------------------------------------")
    print("Server is active. Press [CTRL + C] in this terminal to stop.")
    print("---------------------------------------------------------")
    
    try:
        # Keep the main thread alive waiting for termination
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[gRPC Server] Intercepted Ctrl+C! Shutting down server gracefully...")
        # Stops accepting new requests immediately and flushes ongoing ones within 2 seconds
        server.stop(grace=2)
        print("[gRPC Server] Server stopped cleanly. Exiting.")

if __name__ == '__main__':
    serve()