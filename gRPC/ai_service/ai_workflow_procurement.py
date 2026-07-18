import json
import os
import traceback
from dotenv import load_dotenv

load_dotenv()
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from rag import retrieve_context

# 🎯 INCLUDES THE UNION IMPORT
from pydantic import BaseModel, Field
from typing import List, Dict, Union

# =====================================================================
# 1. PYDANTIC SCHEMA (Strict Type Contracts)
# =====================================================================
# =====================================================================
# 1. PYDANTIC SCHEMA (Strict Type Contracts)
# =====================================================================
# 🎯 FIX: Create a strict nested schema to force exact snake_case dictionary keys
class RegionalSplitSchema(BaseModel):
    # 🎯 FIX: Force these to be strings and explicitly ask for the '%' sign
    west_africa: str = Field(description="Percentage allocation for West Africa (e.g., '50%').")
    usgc: str = Field(description="Percentage allocation for US Gulf Coast (e.g., '30%').")
    latin_america: str = Field(description="Percentage allocation for Latin America (e.g., '20%').")

class ProcurementSchema(BaseModel):
    procurement_strategy_prose: str = Field(description="Concise 1-paragraph summary.")
    recommended_action: str = Field(description="The primary action, e.g., DIVERT + SPOT PROCURE.")
    shortfall_bpd: int = Field(description="Raw integer BPD shortfall calculated from the C++ math gaps.")
    
    # 🎯 FIX: Map the nested schema directly into your main response
    recommended_split: RegionalSplitSchema = Field(description="Strict allocation percentages.")
    
    estimated_additional_cost: str = Field(description="Cost estimate in USD.")
    key_risks: List[str] = Field(description="List of identified risks.")
    escalation_triggers: Dict[str, str] = Field(description="Specific geopolitical or market thresholds that require immediate strategic pivots. Keys should be 'critical_threshold' and 'fallback_protocol'.")
    vessel_specific_actions: List[Dict[str, str]] = Field(description="List of objects with 'vessel' and 'action' keys.")

# Initialize LLMs
llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini")
llm_json = ChatOpenAI(temperature=0.2, model="gpt-4o-mini")

# 🎯 FIX: Forces function calling to avoid OpenAI's strict-mode dictionary crashes
structured_llm = llm_json.with_structured_output(ProcurementSchema, method="function_calling")

# =====================================================================
# 2. LIVE AIS DATA SIMULATOR
# =====================================================================
def get_simulated_ais_data(news_summary: str) -> dict:
    return {
        "timestamp": "2026-07-16T22:00:00Z",
        "tracked_vessels": [
            {
                "vessel_name": "MT Swarna Kamal",
                "imo": 9240316,
                "type": "VLCC",
                "current_coordinates": "26.2084, 56.4952",
                "location_context": "Approaching Strait of Hormuz inbound",
                "status": "ANCHORED / AWAITING CLEARANCE",
                "cargo": "2,000,000 barrels Crude",
                "destination": "Jamnagar_RIL"
            },
            {
                "vessel_name": "MT Desh Vishal",
                "imo": 9387413,
                "type": "VLCC",
                "current_coordinates": "12.3522, 43.5148",
                "location_context": "Southern Red Sea / Bab-el-Mandeb outer limit",
                "status": "MAINTAINING COURSE",
                "speed_knots": 14.2,
                "destination": "Kochi_BPCL"
            }
        ]
    }

# =====================================================================
# 3. UPGRADED CHAT PROMPT TEMPLATES & CHAINS
# =====================================================================
procurement_query_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an expert semantic search engineer specializing in Indian sovereign maritime logistics. "
        "Output ONLY the raw query string with no quotes, commentary, or introduction. "
        "Do not include variable names like '{news}' in the output string."
    )),
    ("human", """Threat Context: {news}
    
    Generate a single-sentence semantic query optimized for a vector database to search for:
    1. Directorate General of Shipping (DGS) or Shipping Corporation of India (SCI) emergency vessel routing protocols.
    2. Indian port constraints, Single Point Mooring (SPM) bottlenecks, draft limits, or mid-ocean lighterage at Kandla/Paradip.
    3. Emergency feedstock spot procurement splits (West Africa vs USGC) and refinery Nelson Complexity Index (NCI) API gravity mismatches.""")
])
procurement_query_chain = procurement_query_prompt | llm | StrOutputParser()

def fetch_maritime_rag(state):
    query = state.get("procurement_query", "")
    mode = state.get("mode", "live")
    print(f"\n[Tab 3 RAG] Querying Isolated 'maritime_logistics' Collection ({mode.upper()} Mode):\n -> '{query}'")
    try:
        return retrieve_context(query, collection_name="maritime_logistics", mode=mode)
    except Exception as e:
        print(f"[Tab 3 RAG Fail-Safe] Collection inaccessible: {e}")
        return "Fallback: standard global chartering and Cape of Good Hope rerouting operational protocols apply."

procurement_strategy_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are the Global Head of Supply Chain and Maritime Procurement for Indian oil infrastructure. Your core objective is to synthesize an immediate corporate sourcing redirection plan addressing current naval bottlenecks.
    
    CRITICAL ANALYTICAL DIRECTIVES:
    - Calculate the exact replacement volume required based on the C++ math payload.
    - Determine a primary strategic action (e.g., DIVERT + SPOT PROCURE).
    - You MUST allocate 100% of the replacement volume across the three regions (e.g., West Africa: 50%, USGC: 30%, Latin America: 20%). Do not return 0%.
    - Estimate the financial damage/additional cost over a 30-day window.
    - key_risks: Generate an array of 2 highly specific operational risks. These risks MUST dynamically reflect the exact geographic constraints, active chokepoints, and alternative supply routes dictated by the current incident data. Do NOT use generic boilerplate (like basic insurance or grade compatibility) unless explicitly tied to the current geopolitical event.    
    - escalation_triggers: Define a critical_threshold (e.g., "If Bab el-Mandeb closure exceeds 15 days or VLCC freight rates exceed $12M") and a subsequent fallback_protocol (e.g., "Pivot 100% of missing volume to USGC SPR releases")
    - Generate specific, tactical routing orders for EVERY vessel listed in the AIS tracking array."""),
    ("human", """Geopolitical Crisis Intel: {news}
Live AIS Ship Positions Payload: {ais_payload}
C++ Operational Math (Shortfalls): {math}
Maritime Logistics Vector Context: {maritime_kb}

Formulate the comprehensive tactical directive now.""")
])
procurement_strategy_chain = procurement_strategy_prompt | llm | StrOutputParser()

json_pack_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a precision data extraction engine. Parse the provided strategic procurement analysis into the exact structured schema. 
    Ensure 'shortfall_bpd' is calculated as a raw integer from the upstream math."""),
    ("human", "Transform this analysis into the required schema:\n\n{strategy}")
])
json_pack_chain = json_pack_prompt | structured_llm

# =====================================================================
# 4. RUNNABLE LCEL ASSEMBLY LINE
# =====================================================================
tab3_pipeline = (
    RunnablePassthrough.assign(ais_payload=lambda x: json.dumps(get_simulated_ais_data(x["news"])))
    .assign(procurement_query=procurement_query_chain)
    .assign(maritime_kb=fetch_maritime_rag)
    .assign(strategy=procurement_strategy_chain)
    | json_pack_chain
)

# =====================================================================
# 5. MAIN ORCHESTRATOR EXECUTION
# =====================================================================
def execute_procurement_modeller(geopolitical_summary, cpp_simulation_json, mode="live"):
    print(f"\n[LCEL] Initializing Tab 3 Procurement Pipeline (Pydantic Mode) | Env: {mode.upper()}...")
    try:
        pydantic_output = tab3_pipeline.invoke({
            "news": geopolitical_summary,
            "math": cpp_simulation_json,
            "mode": mode
        })
        
        if hasattr(pydantic_output, "model_dump"):
            clean_dict = pydantic_output.model_dump()
        else:
            clean_dict = pydantic_output.dict()
            
        print(f"[DEBUG Tab 3] Structured Payload Generated. Shortfall: {clean_dict.get('shortfall_bpd')} BPD")
        return clean_dict
        
    except Exception as e:
        print(f"[AI Workflow 3 Error] Pipeline failure: {e}")
        traceback.print_exc() 
        return {
            "procurement_strategy_prose": f"System breakdown in Tab 3 logistics processing layer. Error: {str(e)}",
            "shortfall_bpd": 0
        }