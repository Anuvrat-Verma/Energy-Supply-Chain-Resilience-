from google.protobuf.json_format import MessageToDict, MessageToJson
import json
import grpc
import os
import sys
import concurrent.futures
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated')))
import energy_pb2
import energy_pb2_grpc

from ai_workflow1 import execute_geopolitical_risk
from ai_workflow_econ import execute_scenario_modeller
from ai_workflow_procurement import execute_procurement_modeller
from ai_workflow_spr import execute_spr_ml_pipeline

class EnergyOrchestratorServicer(energy_pb2_grpc.EnergyOrchestratorServicer):
    
    def TriggerManualOverride(self, request, context):
        """TAB 1 METHOD: Geopolitical Risk (Agent 1) + Physical Simulation (C++ Engine)"""
        try:
            print(f"\n[Orchestrator] TAB 1 Engine Triggered: Threat Intel & C++ Simulation")
            final_output = execute_geopolitical_risk(request, context)

            dynamic_corridor = (
                final_output.risks[0].chokepoint_name 
                if len(final_output.risks) > 0 else "GLOBAL"
            )

            json_payload = MessageToJson(final_output, preserving_proto_field_name=True)

            return energy_pb2.SimulationResult(
                active_recommendation=final_output.overall_summary,
                calculated_spr_days_left=30.0,
                affected_corridor=dynamic_corridor,
                trigger_alarm_ui=len(final_output.risks) > 0,
                raw_cpp_json=json_payload
            )
        except Exception as e:
            print(f"❌ Tab 1 Pipeline Crash Log: {str(e)}")
            context.abort(grpc.StatusCode.INTERNAL, f"Tab 1 Pipeline failed: {str(e)}")

    def AnalyzeGeopoliticalRisk(self, request, context):
        """TAB 2 & 3 METHOD: Runs parallel agents with bulletproof payload extraction"""
        try:
            # 1. Extract environment mode from gRPC metadata headers
            metadata_dict = dict(context.invocation_metadata())
            active_mode = metadata_dict.get('system_mode', 'live')
            
            print(f"🧠 [Orchestrator] Running Tab 2 & 3 Parallel Agents in [{active_mode.upper()}] mode")

            # 2. BULLETPROOF PROTOBUF EXTRACTION 
            # We convert the request to a dictionary to bypass AttributeErrors completely.
            req_dict = MessageToDict(request, preserving_proto_field_name=True)
            
            json_str = "{}"
            # Check the standard known fields first
            if "news_feed" in req_dict:
                json_str = req_dict["news_feed"]
            elif "raw_cpp_json" in req_dict:
                json_str = req_dict["raw_cpp_json"]
            else:
                # Fallback: scan all string fields for the JSON payload
                for key, val in req_dict.items():
                    if isinstance(val, str) and val.strip().startswith("{"):
                        json_str = val
                        break
                        
            # Safety check for empty strings
            if not json_str.strip():
                json_str = "{}"
                
            payload_data = json.loads(json_str)
            
            agent1_summary = payload_data.get("overall_summary", "Analysis complete.")
            cpp_json_output = payload_data.get("triggered_simulation_json", "{}")

            # 3. Fan-out execution across parallel threads with environment signatures
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future_econ = executor.submit(
                    execute_scenario_modeller, 
                    agent1_summary, 
                    cpp_json_output, 
                    mode=active_mode
                )
                future_proc = executor.submit(
                    execute_procurement_modeller, 
                    agent1_summary, 
                    cpp_json_output, 
                    mode=active_mode
                )
                
                # Fan-in: Harvest the output dictionaries safely
                economic_impact_dict = future_econ.result()
                procurement_dict = future_proc.result()
                
            print(f"[Orchestrator] Fan-in complete. Packaging dictionaries into typed Protobuf objects...")

            # 4. EXPLICITLY PACKAGE TAB 2 MESSAGE
            impact_data = economic_impact_dict if isinstance(economic_impact_dict, dict) else {}
            compiled_impact = energy_pb2.CascadingImpact(
                refinery_run_rates=str(impact_data.get("refinery_run_rates", "Stable.")),
                domestic_fuel_prices=str(impact_data.get("domestic_fuel_prices", "Stable.")),
                power_sector_stress=str(impact_data.get("power_sector_stress", "None.")),
                gdp_trajectory=str(impact_data.get("gdp_trajectory", "On target."))
            )

            # 5. EXPLICITLY PACKAGE TAB 3 MESSAGE
            proc_data = procurement_dict if isinstance(procurement_dict, dict) else {}
            split_data = proc_data.get("recommended_split", {})
            escalation_triggers_data = proc_data.get("escalation_triggers", {})
            vessels_data = proc_data.get("vessel_specific_actions", [])
            
            try:
                shortfall_val = int(proc_data.get("shortfall_bpd", 0))
            except (ValueError, TypeError):
                shortfall_val = 0

            compiled_procurement = energy_pb2.ProcurementStrategy(
                procurement_strategy_prose=str(proc_data.get("procurement_strategy_prose", "No strategy generated.")),
                recommended_action=str(proc_data.get("recommended_action", "MAINTAIN COURSE")),
                shortfall_bpd=shortfall_val,
                recommended_split=energy_pb2.RecommendedSplit(
                    west_africa=str(split_data.get("west_africa", "0%")),
                    usgc=str(split_data.get("usgc", "0%")),
                    latin_america=str(split_data.get("latin_america", "0%"))
                ),
                estimated_additional_cost=str(proc_data.get("estimated_additional_cost", "Unknown")),
                key_risks=proc_data.get("key_risks", []),
                escalation_triggers={str(k): str(v) for k, v in escalation_triggers_data.items()},
                vessel_specific_actions=[
                    energy_pb2.VesselAction(
                        vessel=str(v.get("vessel", v.get("vessel_name", "Unknown"))),
                        action=str(v.get("action", v.get("routing_order", "No action specified")))
                    ) for v in vessels_data
                ]
            )

            print(f"[Orchestrator] Initializing Tab 4 Neuro-Symbolic RL Solver...")

            # 6. EXECUTE TAB 4 (Sequential Fan-In)
            # Assuming payload_data (Tab 1) and active_mode are defined earlier in your function
            spr_output_dict = execute_spr_ml_pipeline(
                tab1_dict=payload_data,
                tab2_dict=impact_data,
                tab3_dict=proc_data,
                mode=active_mode
            )

            # 7. EXPLICITLY PACKAGE TAB 4 MESSAGE
            compiled_spr = energy_pb2.SPROptimization(
                policy_directive_prose=str(spr_output_dict.get("policy_directive_prose", "No directive generated.")),
                optimal_drawdown_rate_bpd=int(spr_output_dict.get("optimal_initial_rate", 0)),
                runway_extension_days=float(spr_output_dict.get("runway_extension_days", 0.0)),
                confidence_variance_std=float(spr_output_dict.get("confidence_variance_std", 0.0)),
                daily_drawdown_curve_json=json.dumps(spr_output_dict.get("daily_drawdown_curve", [])),
                sensitivity_shock_curve_json=json.dumps(spr_output_dict.get("sensitivity_shock_curve", [])),
                extracted_features_json=json.dumps(spr_output_dict.get("features_used", {})),
                feature_vector=spr_output_dict.get("feature_vector", [])
            )

            # 8. RETURN COMPILED TYPED RESPONSE
            # Propagate the original Tab 1 risks + cpp simulation JSON so the
            # gateway's "enriched" Tab 1 broadcast has real data instead of blanks.
            try:
                risks_list = [
                    energy_pb2.ChokepointRisk(
                        chokepoint_name=str(r.get("chokepoint_name", "UNKNOWN")),
                        disruption_probability=int(r.get("disruption_probability", 0)),
                        risk_reasoning=str(r.get("risk_reasoning", "")),
                        affected_supplier=str(r.get("affected_supplier", ""))
                    ) for r in payload_data.get("risks", [])
                ]
            except Exception:
                risks_list = []

            return energy_pb2.RiskAnalysisResponse(
                risks=risks_list,
                overall_summary=agent1_summary,
                triggered_simulation_json=cpp_json_output,
                economic_impact=compiled_impact,
                procurement_strategy=compiled_procurement,
                spr_optimization=compiled_spr
            )

        except Exception as e:
            print(f"❌ Pipeline Execution Failed: {str(e)}")
            traceback.print_exc()
            context.abort(grpc.StatusCode.INTERNAL, f"Pipeline processing failed: {str(e)}")

def serve():
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    energy_pb2_grpc.add_EnergyOrchestratorServicer_to_server(EnergyOrchestratorServicer(), server)
    server.add_insecure_port('[::]:50052')
    print("--------------------------------------------------")
    print("AI Orchestrator Server started on port 50052...")
    print("--------------------------------------------------")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()