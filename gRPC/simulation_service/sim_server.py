import os
import sys
import json
import grpc
import subprocess
from concurrent import futures

# Add the generated folder to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated')))

import energy_pb2
import energy_pb2_grpc

class EnergyOrchestratorServicer(energy_pb2_grpc.EnergyOrchestratorServicer):
    def __init__(self):
        # UPDATED PATH: Jumps up two levels to the root directory, then into cpp_engine
        self.cpp_binary_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "cpp_engine", "network_engine")
        )
        
        # Store the latest raw data so the FastAPI Gateway can broadcast it
        self.latest_cpp_data = {}
        
        if not os.path.exists(self.cpp_binary_path):
            print(f"[Warning] C++ binary not detected at {self.cpp_binary_path}.")

    def _process_simulation(self, alert):
        # 1. Extract BOTH chokepoints and suppliers from the gRPC request
        chokepoints = list(alert.detected_chokepoints)
        suppliers = list(alert.affected_supplier)
        
        # 2. Combine them into a single list of blocked entities
        blocked_entities = chokepoints + suppliers
        if not blocked_entities:
            blocked_entities = ["NONE"]

        # 3. Pass the combined list to the C++ binary
        command = [self.cpp_binary_path] + blocked_entities
        print(f"Executing C++ Engine: {' '.join(command)}")
        
        spr_days_left = 90.0
        cpp_json_string = "{}"
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            cpp_json_string = result.stdout.strip()
            
            # Briefly parse just to safely grab the SPR days for the proto fields
            cpp_data = json.loads(cpp_json_string)
            spr_days_left = cpp_data.get("spr_days_remaining", 90.0)
            
        except subprocess.CalledProcessError as e:
            print(f"[Error] C++ execution crashed: {e.stderr}")
            cpp_json_string = json.dumps({"error": "C++ execution failed"})
        except Exception as e:
            print(f"[Error] Subprocess failure: {e}")
            cpp_json_string = json.dumps({"error": str(e)})

        blocked_str = ", ".join(blocked_entities)
        
        # RETURN TRUE GRPC MESSAGE
        return energy_pb2.SimulationResult(
            active_recommendation=f"System processed closures: {blocked_str}. Awaiting AI.",
            calculated_spr_days_left=float(spr_days_left),
            affected_corridor=blocked_str,
            trigger_alarm_ui=(spr_days_left < 15.0),
            raw_cpp_json=cpp_json_string
        )
    def StreamResiliencePipeline(self, request_iterator, context):
        for alert in request_iterator:
            yield self._process_simulation(alert)

    def TriggerManualOverride(self, request, context):
        return self._process_simulation(request)


def serve():
    # Standard gRPC Server initialization
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    energy_pb2_grpc.add_EnergyOrchestratorServicer_to_server(EnergyOrchestratorServicer(), server)
    
    server.add_insecure_port('[::]:50051')
    print("--------------------------------------------------")
    print("Starting True gRPC Simulation Server on port 50051...")
    print("--------------------------------------------------")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()