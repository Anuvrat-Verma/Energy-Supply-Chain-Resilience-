import json
import os
from dotenv import load_dotenv

# Automatically load the OPENAI_API_KEY from your .env file into the environment
load_dotenv()
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableBranch, RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from rag import retrieve_context
from pydantic import BaseModel, Field

# Initialize LLMs
llm = ChatOpenAI(temperature=0.2, model="gpt-4o-mini")
llm_json = ChatOpenAI(temperature=0.0, model="gpt-4o-mini") # Stricter for JSON packing

class PeacetimeEconomicSchema(BaseModel):
    refinery_run_rates: str = Field(description="1-paragraph analysis of how current normal demand affects refinery capacities and utilization rates.")
    domestic_fuel_prices: str = Field(description="1-paragraph on retail fuel pricing stability, consumer margins, or routine pricing adjustments based on demand variations.")
    power_sector_stress: str = Field(description="1-paragraph analyzing normal grid reserve margins, peak load management, and standard industrial utility health.")
    gdp_trajectory: str = Field(description="1-paragraph summarizing how this baseline energy performance underpins overall economic growth and fiscal stability.")

# =====================================================================
# 1. THE ROUTER CLASSIFIER & EXTRACTOR
# =====================================================================
def deterministic_classifier(state: dict) -> str:
    """Parses the C++ JSON payload natively to determine pipeline routing."""
    try:
        math_data = json.loads(state.get("math", "{}"))
        
        refineries = math_data.get("refineries", [])
        if not refineries:
            return "CATASTROPHIC" 
            
        spr_values = [float(ref.get("spr_days_remaining", 99)) for ref in refineries]
        min_spr = min(spr_values)
        
        print(f"[LCEL Router] Lowest SPR detected: {min_spr} days.")
        
        if min_spr < 0:
            return "CATASTROPHIC"
        elif min_spr <= 5:
            return "MODERATE"
        else:
            return "BASELINE"
            
    except Exception as e:
        print(f"[LCEL Router Error] Failed to parse math payload natively: {e}")
        return "CATASTROPHIC" 

def extract_crisis_json(state: dict) -> dict:
    """Instantly builds the dict directly from the accumulated LCEL state."""
    return {
        "refinery_run_rates": state.get("refinery", "Stable."),
        "domestic_fuel_prices": state.get("pricing", "Stable."),
        "power_sector_stress": state.get("grid", "None."),
        "gdp_trajectory": state.get("macro", "On target.")
    }

# =====================================================================
# 2. DYNAMIC RAG QUERY GENERATORS
# =====================================================================
refinery_query_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert semantic search engineer specializing in refinery operations. Output ONLY the raw query string with no quotes, formatting, or introduction."),
    ("human", "Intel: {news} | Math: {math}\n\nGenerate a single-sentence semantic query to search the knowledge base for PPAC consumption telemetry, Gross Refining Margins (GRMs), diesel crack spreads, and physical crude slate processing bottlenecks.")
])
refinery_query_chain = refinery_query_prompt | llm | StrOutputParser()

pricing_query_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert semantic search engineer specializing in energy markets and fuel pricing metrics. Output ONLY the raw query string with no quotes, formatting, or introduction."),
    ("human", "Refinery Shock: {refinery} | Intel: {news}\n\nGenerate a single-sentence semantic query to search the knowledge base for OMC marketing margin contractions, EPS sensitivities for IOCL/BPCL/HPCL, retail price freezes, and resulting under-recoveries.")
])
pricing_query_chain = pricing_query_prompt | llm | StrOutputParser()

grid_query_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert semantic search engineer specializing in industrial grid utilities. Output ONLY the raw query string with no quotes, formatting, or introduction."),
    ("human", "Refinery Shock: {refinery} | Price Shock: {pricing}\n\nGenerate a single-sentence semantic query to search the knowledge base for MoPNG Natural Gas rationing orders, City Gas Distribution (CGD) prioritization vs petrochemical hubs, and captive industrial diesel dependency.")
])
grid_query_chain = grid_query_prompt | llm | StrOutputParser()

macro_query_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert semantic search engineer specializing in sovereign macroeconomics. Output ONLY the raw query string with no quotes, formatting, or introduction."),
    ("human", "Price Shock: {pricing} | Grid Shock: {grid}\n\nGenerate a single-sentence semantic query to search the knowledge base for Economic Survey baseline GDP/fiscal deficit targets, RBI Financial Stability Report (FSR) banking NPAs, household debt, and CPI inflation constraints.")
])
macro_query_chain = macro_query_prompt | llm | StrOutputParser()

# =====================================================================
# 3. FAULT-TOLERANT RAG FETCHER BASE
# =====================================================================
def safe_fetch(query: str, domain_name: str, mode: str) -> str:
    print(f"\n[LCEL RAG - {domain_name}] Executing Query (Mode: {mode.upper()}):\n -> '{query}'")
    try:
        context = retrieve_context(query, collection_name="macro_economics", mode=mode)
        print(f"[LCEL RAG - {domain_name}] Context successfully extracted.")
        return context
    except Exception as e:
        print(f"\n[RAG FAIL-SAFE] {domain_name} Vector Store inaccessible: {e}")
        return f"CRITICAL NOTE: Local KB offline. Proceed using standard macroeconomic rules for {domain_name}."

# =====================================================================
# 4. DOMAIN-SPECIFIC AGENT CHAINS
# =====================================================================
refinery_chain = ChatPromptTemplate.from_messages([
    ("system", """You are the Chief Operations Officer reporting to the Indian Prime Minister. Describe the live operational collapse happening right now at Indian refineries (e.g., Reliance Jamnagar, BPCL Kochi).
    CRITICAL CONSTRAINTS:
    - Output exactly ONE continuous paragraph of dense, factual narrative text.
    - Do NOT prepend the paragraph with a label, prefix, header, or tag.
    - CITE the exact 'spr_days_remaining' and 'received_bpd' figures from the math payload.
    - NEVER explain *how* to analyze the situation or propose generic action plans. State the definitive physical reality.
    - NO bullet points, NO lists, NO formulas."""),
    ("human", "Severity Classification: {classification}\nGeopolitical Intel: {news}\nC++ Operational Math: {math}\nRefinery Knowledge Base Rules: {refinery_kb}")
]) | llm | StrOutputParser()

pricing_chain = ChatPromptTemplate.from_messages([
    ("system", """You are the Chief Economist for the Indian Ministry of Petroleum. Definitively state the exact commercial shock hitting domestic retail fuel prices, government subsidy burdens, and Oil Marketing Company (OMC) under-recoveries today.
    CRITICAL CONSTRAINTS:
    - Output exactly ONE continuous paragraph of dense economic narrative text.
    - Do NOT prepend the paragraph with a label, prefix, header, or tag.
    - State concrete estimates for the retail price shock in Indian Rupees (INR/liter) and OMC losses in Crores. Do NOT use generic dollar or gallon examples.
    - NEVER output mathematical formulas. Do the math internally.
    - NO bullet points, NO lists."""),
    ("human", "Severity Classification: {classification}\nRefinery Output Data: {refinery}\nPricing Knowledge Base Rules: {pricing_kb}")
]) | llm | StrOutputParser()

grid_chain = ChatPromptTemplate.from_messages([
    ("system", """You are the Director of India's Power Grid. State the immediate reality of industrial load-shedding and captive diesel generator stress across Indian manufacturing hubs.
    CRITICAL CONSTRAINTS:
    - Output exactly ONE continuous paragraph of dense energy infrastructure narrative text.
    - Do NOT prepend the paragraph with a label, prefix, header, or tag.
    - Do NOT outline a strategy. State exactly what is actively failing on the grid and the immediate cost to industrial hubs.
    - NO bullet points, NO outlines."""),
    ("human", "Severity Classification: {classification}\nRefinery Output Data: {refinery}\nPricing Shock Data: {pricing}\nPower Grid Knowledge Base Rules: {grid_kb}")
]) | llm | StrOutputParser()

macro_chain = ChatPromptTemplate.from_messages([
    ("system", """You are the Governor of the Reserve Bank of India. Synthesize all upstream constraints above into a final, definitive macroeconomic forecast for India.
    CRITICAL CONSTRAINTS:
    - Output exactly ONE continuous paragraph of dense macroeconomic forecasting.
    - Do NOT prepend the paragraph with a label, prefix, header, or tag.
    - You MUST state estimated percentage drops in the GDP growth trajectory, projected CPI inflation spikes, and the expanding fiscal deficit.
    - NO bullet points, NO tables."""),
    ("human", "Severity Classification: {classification}\nRefinery Output Data: {refinery}\nPricing Shock Data: {pricing}\nGrid Stress Data: {grid}\nMacroeconomic Knowledge Base Rules: {macro_kb}")
]) | llm | StrOutputParser()

# =====================================================================
# 5. THE BASELINE CHAIN (Peacetime)
# =====================================================================
peacetime_structured_llm = llm_json.with_structured_output(PeacetimeEconomicSchema)

peacetime_economic_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a senior sovereign energy market economist. Your job is to analyze routine, non-crisis operational data from the C++ simulation engine and evaluate standard economic impacts.
    CRITICAL DIRECTION:
    - The situation is peaceful and safe. Do NOT mention blockades, wars, panic, or emergency drawdowns.
    - Evaluate how normal variations in 'total_demand' and 'total_flow' impact routine refining, consumer fuel rates, grid peak loads, and macro growth.
    - Output strictly continuous narrative paragraphs for each field in the schema. Do NOT use headers or labels inside the text blocks."""),
    ("human", "Review the current baseline operational metrics:\nC++ Telemetry Data: {math}\nGeopolitical Context: {news}\n\nGenerate the dynamic peacetime economic analysis.")
])

dynamic_baseline_chain = peacetime_economic_prompt | peacetime_structured_llm


# =====================================================================
# 6. MAIN ORCHESTRATOR EXECUTION (Dynamically Scoped)
# =====================================================================
def execute_scenario_modeller(geopolitical_summary, cpp_simulation_json, mode="live"):
    print(f"\n[LCEL] Initializing State Router & Assembly Line (Mode: {mode.upper()})...")
    
    # 👇 1. Dynamic Fetchers: These now capture the 'mode' argument
    def fetch_refinery_rag(state): return safe_fetch(state.get("refinery_query", ""), "Refinery", mode=mode)
    def fetch_pricing_rag(state):  return safe_fetch(state.get("pricing_query", ""), "Pricing", mode=mode)
    def fetch_grid_rag(state):     return safe_fetch(state.get("grid_query", ""), "Grid", mode=mode)
    def fetch_macro_rag(state):    return safe_fetch(state.get("macro_query", ""), "Macro", mode=mode)

    # 👇 2. Assembly Line: Built per-request so it uses the mode-aware fetchers
    crisis_sequence = (
        RunnablePassthrough.assign(refinery_query=refinery_query_chain)
        .assign(refinery_kb=fetch_refinery_rag)
        .assign(refinery=refinery_chain)
        
        .assign(pricing_query=pricing_query_chain)
        .assign(pricing_kb=fetch_pricing_rag)
        .assign(pricing=pricing_chain)
        
        .assign(grid_query=grid_query_chain)
        .assign(grid_kb=fetch_grid_rag)
        .assign(grid=grid_chain)
        
        .assign(macro_query=macro_query_chain)
        .assign(macro_kb=fetch_macro_rag)
        .assign(macro=macro_chain)
        | extract_crisis_json 
    )

    # 👇 3. Dynamic Router Branch
    router_branch = RunnableBranch(
        (lambda x: x["classification"] in ["CATASTROPHIC", "MODERATE"], crisis_sequence),
        (dynamic_baseline_chain | (lambda pydantic_obj: pydantic_obj.model_dump()))
    )

    # 👇 4. Master Chain Definition
    master_chain = (
        RunnablePassthrough.assign(classification=deterministic_classifier)
        | router_branch
    )
    
    output = None
    try:
        print(f"[LCEL] Classifying crisis severity and routing execution...")
        
        output = master_chain.invoke({
            "news": geopolitical_summary,
            "math": cpp_simulation_json,
            "mode": mode
        })
        
        if isinstance(output, dict):
            print(f"[DEBUG] Native dictionary received. Skipping string parsing.")
            return output
            
        print(f"[DEBUG] Raw string received. Parsing JSON...")
        clean_json_str = output.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json_str)
        
    except json.JSONDecodeError as je:
        print(f"[AI Workflow 2 JSON Error] Failed parsing LLM response payload: {je}")
        return {
            "refinery_run_rates": "Formatting failure: LLM generated non-parsable JSON architecture.",
            "domestic_fuel_prices": "Formatting failure.",
            "power_sector_stress": "Formatting failure.",
            "gdp_trajectory": "Formatting failure."
        }
    except Exception as e:
        print(f"[AI Workflow 2 Error] Pipeline collapsed completely: {e}")
        return {
            "refinery_run_rates": "System failure in LCEL routing layer.",
            "domestic_fuel_prices": "System failure in LCEL routing layer.",
            "power_sector_stress": "System failure in LCEL routing layer.",
            "gdp_trajectory": "System failure in LCEL routing layer."
        }