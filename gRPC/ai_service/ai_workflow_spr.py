import json
import os
import traceback
import re
import numpy as np
from pydantic import BaseModel, Field
from typing import List, Dict, Union
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
# ADD THIS
from sb3_contrib import RecurrentPPO

class SPRFeatureState(BaseModel):
    # --- 1. LLM ECONOMIC METRICS (Extracted from Tab 2) ---
    gdp_drop_percent: float = Field(default=0.0, description="Percentage drop in GDP (e.g., 3.5).")
    retail_fuel_price_hike_inr: float = Field(default=0.0, description="Fuel price increase in INR (e.g., 12.0).")
    inflation_spike_percent: float = Field(default=0.0, description="Projected inflation rate (e.g., 8.5).")
    omc_under_recoveries_cr: float = Field(default=0.0, description="Under-recoveries in Crores (e.g., 10000.0).")
    gnpa_risk_percent: float = Field(default=0.0, description="Max projected GNPA percentage (e.g., 4.1).")
    
    # --- 2. C++ SYSTEM MATH (Overwritten by Python) ---
    aggregate_shortfall_bpd: float = 0.0
    max_transit_lag_days: float = 0.0
    num_blocked_suppliers: float = 0.0
    total_flow_vs_demand_ratio: float = 0.0
    
    # --- 3. C++ SPATIAL CHOKEPOINTS (Overwritten by Python) ---
    risk_hormuz: float = 0.0
    risk_suez: float = 0.0
    risk_malacca: float = 0.0
    risk_bab_el_mandeb: float = 0.0
    risk_cape_of_good_hope: float = 0.0
    
    # --- 4. C++ TEMPORAL REFINERY RUNWAYS (Overwritten by Python) ---
    days_left_jamnagar: float = 0.0
    days_left_kochi: float = 0.0
    days_left_paradip: float = 0.0
    days_left_mumbai: float = 0.0
    days_left_chennai: float = 0.0
    num_spr_exhausted_refineries: float = 0.0

    def to_vector(self) -> List[float]:
        """Returns features in the exact order required by the LSTM RL Agent."""
        return [
            self.aggregate_shortfall_bpd,
            self.max_transit_lag_days,
            self.num_blocked_suppliers,
            self.total_flow_vs_demand_ratio,
            self.days_left_jamnagar,
            self.days_left_kochi,
            self.days_left_paradip,
            self.days_left_mumbai,
            self.days_left_chennai,
            self.num_spr_exhausted_refineries,
            self.risk_hormuz,
            self.risk_suez,
            self.risk_malacca,
            self.risk_bab_el_mandeb,
            self.risk_cape_of_good_hope,
            self.gdp_drop_percent,
            self.retail_fuel_price_hike_inr,
            self.inflation_spike_percent,
            self.omc_under_recoveries_cr,
            self.gnpa_risk_percent
        ]
llm_json = ChatOpenAI(temperature=0.0, model="gpt-4o-mini")
feature_extractor_llm = llm_json.with_structured_output(SPRFeatureState, method="function_calling")

feature_extraction_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a highly advanced Neuro-Symbolic Feature Engineering System. Your task is to transform raw, noisy JSON payloads into a strict 20-dimensional feature tensor defined by the SPRFeatureState schema.

    CRITICAL EXTRACTION PROTOCOLS:
    1. CHAIN-OF-THOUGHT: Before finalizing, identify the source field in the input JSON for each of the 20 target features.
    2. DATA NORMALIZATION:
       - Extract raw floating points from strings (e.g., '12.5%' -> 12.5).
       - Map categorical statuses to scalar equivalents (e.g., 'SPR_EXHAUSTED' -> 0.0).
       - Ratio Calculation: If 'total_flow' and 'total_demand' are provided, return flow/demand as a float.
    3. SCHEMA ADHERENCE: All 20 fields must be populated. If data is missing for a non-critical field, default to 0.0. 
       Do not include conversational filler or prose.
    
    TARGET FIELD MAPPINGS:
    - ECONOMIC: gdp_drop_percent, retail_fuel_price_hike_inr, inflation_spike_percent, omc_under_recoveries_cr, gnpa_risk_percent
    - SPATIAL RISKS: risk_hormuz, risk_suez, risk_malacca, risk_bab_el_mandeb, risk_cape_of_good_hope
    - C++ MATH/TEMPORAL: aggregate_shortfall_bpd, max_transit_lag_days, num_blocked_suppliers, total_flow_vs_demand_ratio, days_left_[refinery_name], num_spr_exhausted_refineries"""),
    
    ("human", """[INGESTING SYSTEM CONTEXT]
    📥 Tab 1 (Physical Analytics): {tab1_data}
    📥 Tab 2 (Macro-Economic Analytics): {tab2_data}
    📥 Tab 3 (Sourcing Procurement Tactics): {tab3_data}
    
    Execute high-precision 20D feature tensor extraction now.""")
])
feature_pipeline = feature_extraction_prompt | feature_extractor_llm

# =====================================================================
# 2. FINITE-HORIZON DYNAMIC PROGRAMMING REFINEMENT SOLVER
# =====================================================================
def run_finite_horizon_dp(initial_reserves: float, horizon: int, shortfall_bpd: float, stress_index: float) -> list:
    """
    Applies backward induction over a finite time-horizon to resolve the exact
    mathematically smooth drawdown curve, eliminating pure RL exploration jitter.
    """
    T = int(max(horizon, 5))
    max_capacity = 30000000.0
    max_release = 1500000.0
    
    # Initialize DP state grid space
    # State tracking: Day t, Reserve state volume bucket
    state_buckets = 50
    reserve_states = np.linspace(0, max_capacity, state_buckets)
    
    # Initialize Terminal Value Table: V[state_idx]
    V = np.zeros(state_buckets)
    # Give high penalty to terminal states with zero reserves left prematurely
    V[reserve_states == 0] = -5000.0
    
    policy_table = {}
    
    # Backward Induction iteration loops
    for t in range(T - 1, -1, -1):
        new_V = np.zeros(state_buckets)
        for s_idx, s_val in enumerate(reserve_states):
            best_val = -float('inf')
            best_action = 0.0
            
            # Action space discretization sweep
            for release_pct in np.linspace(0.0, 1.0, 20):
                release = release_pct * max_release
                actual_release = min(release, s_val)
                next_s = s_val - actual_release
                
                # Immediate reward evaluation matching environment physics
                shortage = max(0.0, shortfall_bpd - actual_release)
                reward = -(s_val * 0.02 + 50.0 * (shortage ** 2) / 1e10 + (shortage * stress_index * 15.0) / 1e5)
                
                # Value approximation mapping to closest next state bucket index
                next_s_idx = np.abs(reserve_states - next_s).argmin()
                total_expected_val = reward + 0.99 * V[next_s_idx]
                
                if total_expected_val > best_val:
                    best_val = total_expected_val
                    best_action = actual_release
                    
            new_V[s_idx] = best_val
            policy_table[(t, s_idx)] = best_action
        V = new_V

    # Forward simulation generation loop using derived optimal policies
    dp_curve = []
    curr_res = initial_reserves
    for t in range(T):
        s_idx = np.abs(reserve_states - curr_res).argmin()
        optimal_release = policy_table.get((t, s_idx), shortfall_bpd * 0.5)
        optimal_release = min(optimal_release, curr_res)
        curr_res -= optimal_release
        
        dp_curve.append({
            "day": t + 1,
            "release_bpd": int(optimal_release),
            "reserves_remaining": int(curr_res)
        })
        
    return dp_curve

# =====================================================================
# 3. FAULT-TOLERANT ALGORITHMIC FALLBACK PARSER
# =====================================================================
def execute_spr_ml_pipeline(tab1_dict, tab2_dict, tab3_dict, mode="live"):
    print(f"\n[MCP Engine] Initializing Tab 4 Neuro-Symbolic LSTM Hybrid | Env: {mode.upper()}...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, '..', '..')) 
    model_path = os.path.join(root_dir, 'rl_engine', 'lstm_advanced_spr_agent')
    
    rl_model = None
    try:
        # Load RecurrentPPO instead of standard PPO
        rl_model = RecurrentPPO.load(model_path)
        print(f"[Tab 4] Successfully loaded LSTM brain from: {model_path}.zip")
    except Exception as e:
        print(f"⚠️ LSTM Model load failure at {model_path}.zip. Ensure it exists. Error: {e}")

    try:
        extracted_features = feature_pipeline.invoke({
            "tab1_data": json.dumps(tab1_dict), 
            "tab2_data": json.dumps(tab2_dict),
            "tab3_data": json.dumps(tab3_dict)
        })
        feature_dict = extracted_features.model_dump()
        
        print("\n[Tab 4] Enforcing 20-Dimensional Symbolic Constraints...")
        
        # --- 1. BULLETPROOF C++ MATH & REFINERY RUNWAYS ---
        sim_data = None
        sim_str = tab1_dict.get("triggered_simulation_json")
        if isinstance(sim_str, str):
            try: sim_data = json.loads(sim_str)
            except: pass
        elif isinstance(sim_str, dict):
            sim_data = sim_str

        if sim_data and "refineries" in sim_data:
            feature_dict["max_transit_lag_days"] = float(sim_data.get("network_stabilization_days", 10.0))
            feature_dict["num_blocked_suppliers"] = float(len(sim_data.get("blocked", [])))
            
            demand = float(sim_data.get("total_demand", 1))
            flow = float(sim_data.get("total_flow", 0))
            feature_dict["total_flow_vs_demand_ratio"] = round(flow / demand if demand > 0 else 0.0, 2)
            
            # Extract individual temporal runways
            exhausted_count = 0.0
            for r in sim_data.get("refineries", []):
                if isinstance(r, dict):
                    name = str(r.get("name", "")).upper()
                    days_remaining = float(r.get("spr_days_remaining", 0.0))
                    
                    if days_remaining <= 0 or str(r.get("status", "")) == "SPR_EXHAUSTED":
                        exhausted_count += 1.0
                        
                    if "JAMNAGAR" in name: feature_dict["days_left_jamnagar"] = days_remaining
                    elif "KOCHI" in name: feature_dict["days_left_kochi"] = days_remaining
                    elif "PARADIP" in name: feature_dict["days_left_paradip"] = days_remaining
                    elif "MUMBAI" in name: feature_dict["days_left_mumbai"] = days_remaining
                    elif "CHENNAI" in name: feature_dict["days_left_chennai"] = days_remaining
            feature_dict["num_spr_exhausted_refineries"] = exhausted_count
        else:
            print("⚠️ CRITICAL: Could not parse triggered_simulation_json.")

        # --- 2. BULLETPROOF SPATIAL CHOKEPOINT RISKS ---
        risks = tab1_dict.get("risks", [])
        if isinstance(risks, str):
            try: risks = json.loads(risks)
            except: risks = []
            
        if risks and isinstance(risks, list):
            for r in risks:
                if isinstance(r, dict):
                    name = str(r.get("chokepoint_name", "")).upper()
                    prob = float(r.get("disruption_probability", 0.0))
                    if "HORMUZ" in name: feature_dict["risk_hormuz"] = prob
                    elif "SUEZ" in name: feature_dict["risk_suez"] = prob
                    elif "MALACCA" in name: feature_dict["risk_malacca"] = prob
                    elif "BAB" in name: feature_dict["risk_bab_el_mandeb"] = prob
                    elif "CAPE" in name: feature_dict["risk_cape_of_good_hope"] = prob

        # --- 3. BULLETPROOF TAB 3 SHORTFALL ---
        shortfall_val = tab3_dict.get("shortfall_bpd")
        if shortfall_val is not None:
            feature_dict["aggregate_shortfall_bpd"] = float(shortfall_val)

        print(f"\n[Tab 4] ✅ NEURO-SYMBOLIC 20D FUSION COMPLETE:")
        print(json.dumps(feature_dict, indent=2))
        print("\n")

    except Exception as err:
        print(f"[AI Workflow 4 Extraction Alert] Glitch: {err}")
        feature_dict = run_safe_fallback_extraction(tab1_dict)

    # Step 2: Run LSTM Monte Carlo Rollouts
    mc_initial_rates = []
    simulated_horizon = int(feature_dict.get("max_transit_lag_days", 20))
    shortfall_val = feature_dict.get("aggregate_shortfall_bpd", 150000.0)
    
    if rl_model is not None:
        print(f"[Monte Carlo Engine] Sampling 50 LSTM trajectory rollouts...")
        for _ in range(50):
            # Double brackets required for LSTM (batch_size=1, features=20)
            noise_obs = np.array([[
                shortfall_val + np.random.normal(0, 20000),
                simulated_horizon,
                feature_dict.get("num_blocked_suppliers", 0.0),
                feature_dict.get("total_flow_vs_demand_ratio", 1.0),
                feature_dict.get("days_left_jamnagar", 0.0),
                feature_dict.get("days_left_kochi", 0.0),
                feature_dict.get("days_left_paradip", 0.0),
                feature_dict.get("days_left_mumbai", 0.0),
                feature_dict.get("days_left_chennai", 0.0),
                feature_dict.get("num_spr_exhausted_refineries", 0.0),
                feature_dict.get("risk_hormuz", 0.0),
                feature_dict.get("risk_suez", 0.0),
                feature_dict.get("risk_malacca", 0.0),
                feature_dict.get("risk_bab_el_mandeb", 0.0),
                feature_dict.get("risk_cape_of_good_hope", 0.0),
                feature_dict.get("gdp_drop_percent", 0.0),
                feature_dict.get("retail_fuel_price_hike_inr", 0.0),
                feature_dict.get("inflation_spike_percent", 0.0),
                feature_dict.get("omc_under_recoveries_cr", 0.0),
                feature_dict.get("gnpa_risk_percent", 0.0)
            ]], dtype=np.float32)
            
            # Reset LSTM internal states for each distinct rollout sample
            lstm_states = None
            episode_starts = np.ones((1,), dtype=bool)
            
            act, _ = rl_model.predict(noise_obs, state=lstm_states, episode_start=episode_starts, deterministic=False)
            mc_initial_rates.append(float(act.flatten()[0] * 1500000.0))
    else:
        mc_initial_rates = [shortfall_val * 0.8]

    mean_rate = float(np.mean(mc_initial_rates))
    std_rate = float(np.std(mc_initial_rates))

    dp_drawdown_curve = run_finite_horizon_dp(
        initial_reserves=30000000.0,
        horizon=simulated_horizon,
        shortfall_bpd=shortfall_val,
        stress_index=feature_dict.get("gdp_drop_percent", 1.5)
    )

    shocked_dp_curve = run_finite_horizon_dp(
        initial_reserves=30000000.0,
        horizon=simulated_horizon + 5,
        shortfall_bpd=shortfall_val,
        stress_index=feature_dict.get("gdp_drop_percent", 1.5)
    )

    prose_directive = (
        f"EXECUTIVE ACTION DIRECTIVE: Ingested 20-dimensional macroeconomic crisis vector matrix. "
        f"Upstream models signal an aggregate processing gap threshold of {int(shortfall_val):,} BPD with "
        f"a projected transit blockade horizon of {simulated_horizon} days. The hybrid dynamic programming "
        f"solver has mapped the optimal inventory preservation trajectory, authorizing a Day 1 strategic release "
        f"rate of {int(dp_drawdown_curve[0]['release_bpd']):,} BPD. Monte Carlo LSTM iterations project system confidence limits "
        f"within a standard deviation variance threshold of +/- {int(std_rate):,} BPD. Under a critical +5 day shipping "
        f"extension shock scenario, the depletion safety margins adapt by shifting the baseline curve profile."
    )

    return {
        "features_used": feature_dict,
        "policy_directive_prose": prose_directive,
        "optimal_initial_rate": int(dp_drawdown_curve[0]["release_bpd"]),
        "runway_extension_days": float(simulated_horizon),
        "confidence_variance_std": round(std_rate, 2),
        "daily_drawdown_curve": dp_drawdown_curve,
        "sensitivity_shock_curve": shocked_dp_curve,
        "feature_vector": extracted_features.to_vector(),  # New: Maps to 'repeated float feature_vector'
    }  