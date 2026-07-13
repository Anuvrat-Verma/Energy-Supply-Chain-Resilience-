import sys
import os
import time
import grpc

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated')))
import energy_pb2
import energy_pb2_grpc

def generate_mock_signals():
    signals = [
        energy_pb2.AlertSignal(
            source_headline="Breaking: Drone attacks reported near the Strait of Hormuz.",
            detected_chokepoint="HORMUZ",
            baseline_risk_score=85
        )
    ]
    for sig in signals:
        time.sleep(1)
        yield sig

def run_client():
    print("[gRPC Client] Connecting to orchestration server on port 50051...")
    
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = energy_pb2_grpc.EnergyOrchestratorStub(channel)
            
            # 1. Test the Stream (Simulating n8n)
            print("\n--- Testing n8n Background Stream ---")
            response_stream = stub.StreamResiliencePipeline(generate_mock_signals())
            for response in response_stream:
                print(f"[Stream Output] Recommendation: {response.active_recommendation}")

            time.sleep(1)

            # 2. Test the new UI Override (Simulating a React map click)
            print("\n--- Testing React UI Manual Override ---")
            ui_signal = energy_pb2.AlertSignal(
                source_headline="MANUAL OVERRIDE: User clicked Red Sea polygon.",
                detected_chokepoint="RED_SEA",
                baseline_risk_score=100
            )
            
            # This is a single, instant request-response (Unary)
            ui_response = stub.TriggerManualOverride(ui_signal)
            
            print("============ LIVE UI OVERRIDE RESULT ============")
            print(f"Target Corridor:  {ui_response.affected_corridor}")
            print(f"SPR National Cover Remaining: {ui_response.calculated_spr_days_left} Days")
            print(f"Orchestrator Directive:\n -> {ui_response.active_recommendation}")
            print("=================================================")
                
    except grpc.RpcError as e:
        print(f"\n[gRPC Client] Connection error: {e.details()}")
    except KeyboardInterrupt:
        print("\n[gRPC Client] Exiting cleanly.")

if __name__ == '__main__':
    run_client()