import os
import sys
import uvicorn
import json
import grpc
import asyncio
import feedparser
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from google.protobuf.json_format import MessageToDict
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated')))
import energy_pb2
import energy_pb2_grpc

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# GLOBAL SYSTEM STATE (The Mode Toggle)
# ==========================================
SYSTEM_MODE = "LIVE"  # Boots up in real-world RSS mode by default

class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()
        # Cache the most recent broadcast for each tab to re-push to new connections
        self.latest_state = {
            "TAB_1_DATA": None,
            "TAB_2_DATA": None,
            "TAB_3_DATA": None,
            "TAB_4_DATA": None
        }

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        # Push all latest data to the newly connected client
        for type, payload in self.latest_state.items():
            if payload:
                await websocket.send_text(json.dumps({"type": type, "payload": payload}))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # Update cache
        try:
            msg_dict = json.loads(message)
            if msg_dict.get("type") in self.latest_state:
                self.latest_state[msg_dict["type"]] = msg_dict["payload"]
        except Exception:
            pass

        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.active_connections.discard(connection)

manager = ConnectionManager()

# --- PIPELINE AUTOMATION LOGIC ---
WATCH_LIST = [
    "HORMUZ", "SUEZ", "MALACCA", "BAB EL-MANDEB", "CAPE OF GOOD HOPE", 
    "BASRA", "RAS TANURA", "FUJAIRAH", "KOZMINO", "CORPUS CHRISTI", "BONNY ISLAND"
]

PROCESSED_ARTICLES = set()

async def pipeline_worker(incoming_news: str):
    """Unified pipeline core orchestrating the multi-agent asynchronous architecture."""
    global SYSTEM_MODE
    async with grpc.aio.insecure_channel('localhost:50052') as channel:
        stub = energy_pb2_grpc.EnergyOrchestratorStub(channel)
        
        try:
            # Setup gRPC metadata to pass environment state system-wide
            metadata = [('system_mode', SYSTEM_MODE.lower())]

            # STEP 1: EXECUTE TAB 1 (Threat Intel + C++)
            print(f"\n[Pipeline Worker] 🚀 Triggering Tab 1 Engine ({SYSTEM_MODE} Mode)...")
            tab1_request = energy_pb2.ChokepointAlert(
                detected_chokepoints=[], 
                affected_supplier=["Multiple"],
                news_feed=incoming_news       
            )
            
            tab1_response = await stub.TriggerManualOverride(tab1_request, metadata=metadata)            
            
            # Broadcast partial data immediately so refineries/map update
            # We must pass the raw C++ JSON string as triggered_simulation_json
            await manager.broadcast(json.dumps({
                "type": "TAB_1_DATA", 
                "payload": {
                    "risks": [],
                    "overall_summary": "Syncing with C++ Engine...",
                    "triggered_simulation_json": tab1_response.raw_cpp_json
                }
            }))
            print("[Pipeline Worker] ✅ Broadcasted initial Tab 1 to UI.")


            # STEP 2 & 3: EXECUTE PARALLEL LCEL AGENTS (Econ & Procurement)
            print(f"\n[Pipeline Worker] 🧠 Triggering Tab 2 & 3 Parallel Engines ({SYSTEM_MODE} Mode)...")

            # 🎯 FIX: Keep news_feed completely flat so the backend doesn't throw a KeyError
            tab2_request = energy_pb2.ChokepointAlert(
                detected_chokepoints=[],
                affected_supplier=["Multiple"],
                news_feed=tab1_response.raw_cpp_json  # Pass the raw C++ JSON string directly
            )

            # The gRPC metadata header handles the mode toggle system-wide perfectly on its own
            tab2_response = await stub.AnalyzeGeopoliticalRisk(tab2_request, metadata=metadata)
            
            # --- Broadcast Enriched Tab 1 (Risks + Summary) ---
            tab1_enriched_payload = {
                "risks": [MessageToDict(r, preserving_proto_field_name=True) for r in tab2_response.risks],
                "overall_summary": tab2_response.overall_summary,
                "triggered_simulation_json": tab2_response.triggered_simulation_json
            }
            if not tab1_enriched_payload["triggered_simulation_json"]:
                tab1_enriched_payload["triggered_simulation_json"] = tab1_response.raw_cpp_json

            await manager.broadcast(json.dumps({"type": "TAB_1_DATA", "payload": tab1_enriched_payload}))
            print("[Pipeline Worker] ✅ Broadcasted enriched Tab 1 to UI.")

            # --- Extract and Broadcast Tab 2 (Economic) ---
            tab2_payload = MessageToDict(tab2_response.economic_impact, preserving_proto_field_name=True, always_print_fields_with_no_presence=True)
            await manager.broadcast(json.dumps({"type": "TAB_2_DATA", "payload": tab2_payload}))
            print("[Pipeline Worker] ✅ Broadcasted Tab 2 to UI.")

            # --- Extract and Broadcast Tab 3 (Procurement) ---
            tab3_payload = MessageToDict(tab2_response.procurement_strategy, preserving_proto_field_name=True, always_print_fields_with_no_presence=True)
            await manager.broadcast(json.dumps({"type": "TAB_3_DATA", "payload": tab3_payload}))
            print("[Pipeline Worker] ✅ Broadcasted Tab 3 to UI.")

    
            tab4_payload = MessageToDict(tab2_response.spr_optimization, preserving_proto_field_name=True, always_print_fields_with_no_presence=True)
            await manager.broadcast(json.dumps({"type": "TAB_4_DATA", "payload": tab4_payload}))
            print("[Pipeline Worker] ✅ Broadcasted Tab 4 to UI.")

            return {
                "environment_mode": SYSTEM_MODE.lower(),
                "tab1_physical_routing": tab1_enriched_payload,
                "tab2_economic_impact": tab2_payload,
                "tab3_procurement_strategy": tab3_payload,
                "tab4_spr_optimization": tab4_payload  # Include this in the return payload
            }
            
        except grpc.RpcError as e:
            print(f"\n[Pipeline Worker Error] gRPC Call failed: {e.details()}")
            return None

async def poll_rss_feeds_loop():
    """Background loop that respects the SYSTEM_MODE toggle."""
    global SYSTEM_MODE
    RSS_FEEDS = [
        "https://gcaptain.com/feed/",
        "https://oilprice.com/rss/main",
        "https://www.hellenicshippingnews.com/feed/",
        "https://maritime-executive.com/api/rss/latest",
        "https://energy.economictimes.indiatimes.com/rss/topstories",
        "https://news.usni.org/feed",
        "https://channel16.dryadglobal.com/rss.xml",
        "https://splash247.com/feed/",
        "https://www.defensenews.com/rss",
        "https://www.rigzone.com/news/rss/rigzone_latest.aspx",       
        "https://www.marinelink.com/rss",                             
        "https://shipandbunker.com/rss"                                
    ]
    
    await asyncio.sleep(5) 
    print("[RSS Poller] Background loop initialized.")
    
    while True:
        # STRICT ISOLATION: Only parse real news if in LIVE mode
        if SYSTEM_MODE == "LIVE":
            try:
                new_intel_indicators = []
                for url in RSS_FEEDS:
                    feed = feedparser.parse(url)
                    for entry in feed.entries[:5]:  
                        article_uid = entry.get("link", entry.get("title", ""))
                        if article_uid in PROCESSED_ARTICLES:
                            continue
                        
                        title = entry.get("title", "")
                        summary = entry.get("summary", "")
                        corpus = f"{title} {summary}".lower()
                        
                        if any(keyword.lower() in corpus for keyword in WATCH_LIST):
                            print(f"[RSS Poller] Match detected: \"{title}\"")
                            new_intel_indicators.append(f"HEADLINE: {title}\nSUMMARY: {summary}")
                            PROCESSED_ARTICLES.add(article_uid)
                
                if new_intel_indicators:
                    unified_news_feed = "\n---\n".join(new_intel_indicators)
                    await pipeline_worker(unified_news_feed)
                    
            except Exception as e:
                print(f"[RSS Poller Error] Scanning exception encountered: {e}")
        else:
            pass # Silently sleep without hitting external URLs when in SANDBOX mode
            
        await asyncio.sleep(300) # Check every 5 mins

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(poll_rss_feeds_loop())

# --- ENDPOINTS ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ----------------------------------------------------
# TAB 5 API CONTROLS (Mode Switching & Manual Trigger)
# ----------------------------------------------------

@app.post("/set-mode")
async def set_mode(request: Request):
    """Allows the frontend UI to toggle between LIVE and SANDBOX modes."""
    global SYSTEM_MODE
    try:
        data = await request.json()
        new_mode = data.get("mode", "LIVE").upper()
        
        if new_mode in ["LIVE", "SANDBOX"]:
            SYSTEM_MODE = new_mode
            print(f"\n==================================================")
            print(f"⚙️ SYSTEM MODE SWITCHED TO: {SYSTEM_MODE}")
            print(f"==================================================")
            return {"status": "success", "current_mode": SYSTEM_MODE}
            
        return {"status": "error", "message": "Mode must be 'LIVE' or 'SANDBOX'."}
    except Exception:
        return {"status": "error", "message": "Invalid payload."}

@app.post("/trigger-simulation")
async def handle_trigger(request: Request):
    """Accepts manual simulation inputs ONLY if the system is in SANDBOX mode."""
    global SYSTEM_MODE
    
    # STRICT ISOLATION: Reject manual payloads if real-world mode is active
    if SYSTEM_MODE == "LIVE":
        return {
            "status": "error", 
            "message": "System is currently in LIVE mode. Switch to SANDBOX mode to inject user simulations."
        }
        
    try:
        body = await request.body()
        data = await request.json() if body else {}
    except Exception:
        data = {}
    
    incoming_news = data.get("news_feed", "Manual System Override Event Triggered")
    
    print(f"\n==================================================")
    print(f"🛠️ HTTP TRIGGER RECEIVED (SANDBOX MODE)")
    print(f"   Payload: {incoming_news}")
    print(f"==================================================")
    
    payload = await pipeline_worker(incoming_news)
    
    if payload is None:
        return {"status": "error", "message": "AI Orchestrator (Port 50052) is offline"}
        
    return {"status": "success", "ai_data": payload}

if __name__ == "__main__":
    print("--------------------------------------------------")
    print(f"Gateway started on port 8000. Default Mode: {SYSTEM_MODE}")
    print("--------------------------------------------------")
    uvicorn.run(app, host="0.0.0.0", port=8000)