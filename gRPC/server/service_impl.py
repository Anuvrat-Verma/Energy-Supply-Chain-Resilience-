import os
import sys
import json
import grpc
import subprocess

# Dynamic generated stubs
import energy_pb2
import energy_pb2_grpc

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# --- GRP C SERVICE IMPLEMENTATION ---
class EnergyOrchestratorServicer(energy_pb2_grpc.EnergyOrchestratorServicer):
    def __init__(self):
        self.cpp_binary_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "cpp_engine", "network_engine")
        )
        
        # Store the latest raw data so the FastAPI Gateway can broadcast it
        self.latest_cpp_data = {}
        
        if not os.path.exists(self.cpp_binary_path):
            print(f"[Warning] C++ binary not detected at {self.cpp_binary_path}.")

        try:
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        except Exception:
            print("[Warning] OpenAI API key not set properly. Falling back to rule-based logic.")
            self.llm = None

    def _process_simulation(self, alert):
        chokepoint = alert.detected_chokepoint.strip().upper()
        
        # 1. Execute C++ Engine
        try:
            result = subprocess.run(
                [self.cpp_binary_path, chokepoint],
                capture_output=True,
                text=True,
                check=True
            )
            cpp_data = json.loads(result.stdout.strip())
            
            # Save the parsed JSON to the class instance for the Gateway to read
            self.latest_cpp_data = cpp_data
            
            spr_days_left = cpp_data.get("spr_days_remaining", 90.0)
            total_shortfall = cpp_data.get("total_national_shortfall_bpd", 0.0)
            
            refinery_details = ""
            for ref in cpp_data.get("refineries", []):
                if ref.get("status") != "OPERATIONAL":
                    refinery_details += (
                        f"- {ref['name']}: {ref['status']} | Shortfall: {ref.get('shortfall_bpd', 0)} bpd. "
                        f"Re-routed to {ref.get('alternative_supplier', 'N/A')} (Lag: {ref.get('transit_lag_days', 0)} days)\n"
                    )
        except Exception as e:
            print(f"[Error] Subprocess failure: {e}")
            self.latest_cpp_data = {"error": str(e)}
            spr_days_left, total_shortfall, refinery_details = 90.0, 0.0, "System analysis unavailable."

        # 2. LLM Orchestration
        recommendation = ""
        if self.llm:
            try:
                prompt = ChatPromptTemplate.from_template(
                    "You are the Procurement Orchestrator. Emergency at {chokepoint}.\n"
                    "Shortfall: {shortfall} bpd. SPR Cover: {days} days.\n"
                    "Mitigation:\n{refinery_details}\n"
                    "Provide a 40-word directive for refineries."
                )
                response = self.llm.invoke(prompt.format(
                    chokepoint=chokepoint, shortfall=total_shortfall, 
                    days=spr_days_left, refinery_details=refinery_details
                ))
                recommendation = response.content.strip()
            except:
                recommendation = f"Emergency: Redirect supply at {chokepoint}. SPR at {spr_days_left} days."
        
        return energy_pb2.SimulationResult(
            active_recommendation=recommendation,
            calculated_spr_days_left=float(spr_days_left),
            affected_corridor=chokepoint,
            trigger_alarm_ui=(spr_days_left < 15.0) 
        )

    def StreamResiliencePipeline(self, request_iterator, context):
        for alert in request_iterator:
            yield self._process_simulation(alert)

    def TriggerManualOverride(self, request, context):
        return self._process_simulation(request)