import os
import sys
import json
import grpc
from dotenv import load_dotenv

# 🎯 FIX: Remove the opentelemetry context import to avoid namespaces clashes with gRPC's context
load_dotenv()

# Ensure the generated stubs can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated')))

import energy_pb2
import energy_pb2_grpc

from ai_workflow_econ import execute_scenario_modeller
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

# Initialize LLM
llm = ChatOpenAI(temperature=0.1, model="gpt-4o-mini")

# 🎯 FIX: Explicitly pass the gRPC 'context' parameter into the workflow function
def execute_geopolitical_risk(request, context):
    print("\n[AI Workflow 1] Triggered: Geopolitical Risk Intelligence Agent")
    
    # 🎯 FIX: Extract the metadata from the genuine gRPC context object safely
    try:
        metadata_dict = dict(context.invocation_metadata())
        active_mode = metadata_dict.get('system_mode', 'live') 
    except Exception:
        active_mode = 'live' # Safe fallback fallback if called outside an active RPC context
        
    print(f"📡 gRPC Service Context: Inbound request routed to [{active_mode.upper()}] engine.")
    
    # 🎯 FIX: Treat request.news_feed as a raw string directly to avoid JSONDecodeErrors on RSS text
    live_intel_feed = request.news_feed
    
    prompt = PromptTemplate(
        template="""
        You are a highly analytical Geopolitical Risk Intelligence Agent.
        Analyze the following live intelligence feeds and assign a supply chain disruption for India
        probability score (0 to 100) for global chokepoints.
        Ensure maritime chokepoints are centered around india and accurately reflect real-world shipping routes. Oil from the Middle East to India routes through the Strait of Hormuz. Oil from Russia to India routes through the Malacca Strait. Oil from the USA to India routes through the Cape of Good Hope. Oil from Africa to India routes through the Bab el-Mandeb.
        - Use ONLY these chokepoint IDs for 'chokepoint_name': ["HORMUZ", "MALACCA", "BAB_EL_MANDEB", "CAPE_OF_GOOD_HOPE", "SUEZ_CANAL", "SUNDRA_STRAIT"]
        - Use ONLY these supplier IDs for 'affected_supplier': ["BASRA_IRAQ", "RAS_TANURA_SAUDI", "FUJAIRAH_UAE", "KOZMINO_RUSSIA", "CORPUS_CHRISTI_USA", "BONNY_ISLAND_NIGERIA"]

        Live Intel Feed:
        {intel}

        Output your analysis STRICTLY as a valid JSON object:
        {{
            "risks": [
                {{
                    "chokepoint_name": "HORMUZ", 
                    "disruption_probability": 85, 
                    "risk_reasoning": "...", 
                    "affected_supplier": "FUJAIRAH_UAE"
                }}
            ],
            "summary": "Overall assessment..."
        }}
        """,
        input_variables=["intel"]
    )

    print("[AI Workflow 1] Analyzing Intel feeds via LangChain...")
    chain = prompt | llm | StrOutputParser()
    
    try:
        raw_response = chain.invoke({"intel": live_intel_feed})
        clean_json_str = raw_response.replace('```json', '').replace('```', '').strip()
        ai_data = json.loads(clean_json_str)
        
        risks_list = []
        high_risk_chokepoints = []
        
        for risk in ai_data.get("risks", []):
            name = risk["chokepoint_name"]
            prob = risk["disruption_probability"]
            supplier = risk.get("affected_supplier", "BONNY_ISLAND_NIGERIA") 
            
            risks_list.append(energy_pb2.ChokepointRisk(
                chokepoint_name=name,
                disruption_probability=prob,
                risk_reasoning=risk["risk_reasoning"],
                affected_supplier=supplier
            ))
            
            if prob > 60:
                high_risk_chokepoints.append(name)
        
        alert_list = high_risk_chokepoints if high_risk_chokepoints else ["NONE"]
        
        unique_suppliers = set()
        for risk in ai_data.get("risks", []):
            if risk.get("disruption_probability", 0) > 60:
                supplier = risk.get("affected_supplier")
                if supplier and supplier != "Unknown":
                    unique_suppliers.add(supplier)
        
        supplier_list = list(unique_suppliers) if unique_suppliers else ["BONNY_ISLAND_NIGERIA"]
        
        alert_req = energy_pb2.ChokepointAlert(
            detected_chokepoints=alert_list,
            affected_supplier=supplier_list
        )
        
        print(f"[AI Workflow 1] CRITICAL THREATS: {alert_list}. Suppliers: {supplier_list}. Triggering C++ Engine...")
        cpp_json_output = "{}"
        
        try:
            with grpc.insecure_channel('localhost:50051') as channel:
                sim_stub = energy_pb2_grpc.EnergyOrchestratorStub(channel)
                
                # 🎯 FIX: Forward the system_mode metadata context to the downstream C++ simulator
                sim_resp = sim_stub.TriggerManualOverride(alert_req, metadata=[('system_mode', active_mode)])
                cpp_json_output = sim_resp.raw_cpp_json
                print("[AI Workflow 1] Successfully retrieved C++ simulation routing.")
        except grpc.RpcError as e:
            print(f"[AI Workflow 1 Error] Failed to reach Sim Server: {e.details()}")
            cpp_json_output = json.dumps({"error": "Simulation server offline."})

        agent1_summary = ai_data.get("summary", "Analysis complete.")
        print("[AI Workflow 1] Tab 1 Intelligence Gathering Complete. Returning payload.")

        return energy_pb2.RiskAnalysisResponse(
            risks=risks_list,
            overall_summary=agent1_summary,
            triggered_simulation_json=cpp_json_output
        )
        
    except Exception as e:
        print(f"[Error] AI Processing failed: {e}")
        return energy_pb2.RiskAnalysisResponse(overall_summary="Failed to process geopolitical intel.")