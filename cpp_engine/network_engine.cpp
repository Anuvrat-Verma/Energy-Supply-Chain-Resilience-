#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <iomanip>
#include <sstream>

struct Route {
    std::string route_id;
    std::string origin_supplier;
    std::string destination_port;
    std::string crude_type;          // "SWEET" or "SOUR"
    double base_cost_per_barrel;
    double transit_days;
    std::vector<std::string> chokepoints_crossed;
    bool is_viable = true;
};

struct RefineryAllocation {
    std::string refinery_name;
    std::string status;              // "OPERATIONAL", "MITIGATED", "SHORTFALL"
    double demand_bpd;
    double shortfall_bpd;
    std::string assigned_backup_route;
    std::string alternative_supplier;
    double extra_transit_days;
    double cost_premium_usd;
};

class SupplyChainResilienceEngine {
private:
    std::vector<Route> shipping_network;
    double total_spr_reserves = 39100000.0; // Total Phase 1 SPR capacity (barrels)

public:
    SupplyChainResilienceEngine() {
        // Seed full edge network matching specific crude grades and supply lanes
        shipping_network = {
            {"R_HORMUZ_01", "BASRA_IRAQ", "JAMNAGAR_PORT", "SOUR", 72.50, 4.9, {"HORMUZ"}},
            {"R_HORMUZ_02", "RAS_TANURA_SAUDI", "KOCHI_PORT", "SWEET", 74.00, 6.2, {"HORMUZ"}},
            {"R_REDSEA_01", "SIDI_KERIR_EGYPT", "JAMNAGAR_PORT", "SOUR", 78.20, 10.1, {"BAB_EL_MANDEB", "RED_SEA"}},
            {"R_AFRICA_01", "BONNY_ISLAND_NIGERIA", "KOCHI_PORT", "SWEET", 81.50, 17.2, {"CAPE_OF_GOOD_HOPE"}},
            {"R_LATAM_01",  "SANTOS_BRAZIL", "PARADIP_PORT", "SOUR", 84.00, 24.1, {"ATLANTIC"}}
        };
    }

    std::string execute_simulation(const std::string& blocked_chokepoint) {
        // 1. Evaluate Chokepoint Status across the entire Network Graph
        for (auto& route : shipping_network) {
            auto it = std::find(route.chokepoints_crossed.begin(), route.chokepoints_crossed.end(), blocked_chokepoint);
            if (it != route.chokepoints_crossed.end()) {
                route.is_viable = false;
            }
        }

        // 2. Define India's target industrial nodes
        std::vector<RefineryAllocation> allocations = {
            {"JAMNAGAR_RIL", "OPERATIONAL", 660000.0, 0.0, "PRIMARY_LANE", "BASRA_IRAQ", 0.0, 0.0},
            {"KOCHI_BPCL",   "OPERATIONAL", 310000.0, 0.0, "PRIMARY_LANE", "RAS_TANURA_SAUDI", 0.0, 0.0},
            {"PARADIP_IOCL", "OPERATIONAL", 300000.0, 0.0, "PRIMARY_LANE", "SANTOS_BRAZIL", 0.0, 0.0}
        };

        double total_national_shortfall = 0.0;

        // 3. Process Constraint Matching & Dynamic Procurement Per Refinery
        for (auto& ref : allocations) {
            bool primary_disrupted = false;
            std::string target_crude = "";

            // Determine if this specific refinery's baseline supply lane is severed
            if (ref.refinery_name == "JAMNAGAR_RIL" && !shipping_network[0].is_viable) { primary_disrupted = true; target_crude = "SOUR"; }
            if (ref.refinery_name == "KOCHI_BPCL"   && !shipping_network[1].is_viable) { primary_disrupted = true; target_crude = "SWEET"; }
            // Paradip relies on Latin American routes, not affected by Middle East chokepoints directly

            if (primary_disrupted) {
                ref.status = "SHORTFALL"; // Temporary flag until mitigation loop runs
                double best_premium = 999.0;
                Route optimal_backup;
                bool backup_found = false;

                // Dynamic Re-routing optimization loop: Search for valid alternative supplier matching crude grade
                for (const auto& route : shipping_network) {
                    if (route.is_viable && route.crude_type == target_crude && route.route_id != "R_HORMUZ_01" && route.route_id != "R_HORMUZ_02") {
                        double premium = route.base_cost_per_barrel - 73.00;
                        if (premium < best_premium) {
                            best_premium = premium;
                            optimal_backup = route;
                            backup_found = true;
                        }
                    }
                }

                if (backup_found) {
                    ref.status = "MITIGATED";
                    ref.assigned_backup_route = optimal_backup.route_id;
                    ref.alternative_supplier = optimal_backup.origin_supplier;
                    ref.extra_transit_days = optimal_backup.transit_days;
                    ref.cost_premium_usd = best_premium;
                    
                    // Supply lag calculation creates a transient buffer shortfall while ships are at sea
                    ref.shortfall_bpd = ref.demand_bpd * (optimal_backup.transit_days / 30.0); 
                    total_national_shortfall += ref.shortfall_bpd;
                } else {
                    // Complete structural failure to mitigate
                    ref.status = "CRITICAL_SHUTDOWN";
                    ref.shortfall_bpd = ref.demand_bpd;
                    total_national_shortfall += ref.shortfall_bpd;
                }
            }
        }

        // 4. Calculate realistic national SPR Drawdown Curve based on active total shortfalls
        double spr_days_remaining = 90.0; // Maximum strategic buffer capacity index across all phase assets
        if (total_national_shortfall > 0) {
            spr_days_remaining = total_spr_reserves / total_national_shortfall;
            if (spr_days_remaining > 90.0) spr_days_remaining = 90.0;
        }

        // 5. Construct Structured JSON Stream containing nested refinery breakdown arrays
        std::stringstream json;
        json << "{"
             << "\"status\":\"PROCESSED\","
             << "\"blocked_node\":\"" << blocked_chokepoint << "\","
             << "\"total_national_shortfall_bpd\":" << std::fixed << std::setprecision(0) << total_national_shortfall << ","
             << "\"spr_days_remaining\":" << std::fixed << std::setprecision(2) << spr_days_remaining << ","
             << "\"refineries\":[";
        
        for (size_t i = 0; i < allocations.size(); ++i) {
            const auto& ref = allocations[i];
            json << "{"
                 << "\"name\":\"" << ref.refinery_name << "\","
                 << "\"status\":\"" << ref.status << "\","
                 << "\"demand_bpd\":" << ref.demand_bpd << ","
                 << "\"shortfall_bpd\":" << std::fixed << std::setprecision(0) << ref.shortfall_bpd << ","
                 << "\"backup_route\":\"" << ref.assigned_backup_route << "\","
                 << "\"alternative_supplier\":\"" << ref.alternative_supplier << "\","
                 << "\"transit_lag_days\":" << std::fixed << std::setprecision(1) << ref.extra_transit_days << ","
                 << "\"premium_usd\":" << std::fixed << std::setprecision(2) << ref.cost_premium_usd
                 << "}";
            if (i < allocations.size() - 1) json << ",";
        }
        json << "]}";

        return json.str();
    }
};

int main(int argc, char* argv[]) {
    std::string target_disruption = "NONE";
    if (argc > 1) {
        target_disruption = argv[1];
    }

    SupplyChainResilienceEngine engine;
    std::string result_json = engine.execute_simulation(target_disruption);
    std::cout << result_json << std::endl;
    
    return 0;
}