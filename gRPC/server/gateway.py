import os
import sys
import uvicorn
import json
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Keep your path setup so it can find your stubs
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated')))

from service_impl import EnergyOrchestratorServicer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

servicer = EnergyOrchestratorServicer()

# Store active connected browsers
active_connections = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.post("/trigger-simulation")
async def handle_trigger(request: Request):
    data = await request.json()
    chokepoint = data.get("chokepoint", "UNKNOWN")
    print(f"\n==================================================")
    print(f"1. HTTP CLICK RECEIVED: Triggering {chokepoint}")
    
    class MockAlert:
        def __init__(self, chokepoint):
            self.detected_chokepoint = chokepoint
            self.source_headline = "Manual UI Override"
            
    # 1. Trigger your simulation logic
    print("2. Firing C++ Engine via service_impl.py...")
    grpc_result = servicer._process_simulation(MockAlert(chokepoint))
    
    # 2. Fetch the real C++ data from the servicer instance
    simulation_payload = servicer.latest_cpp_data.copy() if hasattr(servicer, 'latest_cpp_data') else {}
    simulation_payload["blocked_node"] = chokepoint
    print(f"3. C++ OUTPUT INTERCEPTED: {simulation_payload}")
    
    # 3. Broadcast the REAL results to the frontend HUD
    print(f"4. ACTIVE WEBSOCKET CONNECTIONS FOUND: {len(active_connections)}")
    for i, connection in enumerate(active_connections):
        try:
            await connection.send_text(json.dumps(simulation_payload))
            print(f"   -> [SUCCESS] Payload sent to React UI (Client {i+1})")
        except Exception as e:
            print(f"   -> [FAILED] Could not send to React UI: {e}")
            
    print(f"==================================================\n")
    
    return {
        "status": "success", 
        "message": f"Simulation triggered for {chokepoint}"
    }

# THIS IS THE CRUCIAL PART THAT STARTS THE SERVER
if __name__ == "__main__":
    print("--------------------------------------------------")
    print("Starting FastAPI Gateway & WebSocket on port 8000...")
    print("--------------------------------------------------")
    uvicorn.run(app, host="0.0.0.0", port=8000)