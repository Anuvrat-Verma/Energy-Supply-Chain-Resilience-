#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <queue>
#include <algorithm>
#include <iomanip>
#include <sstream>
#include <unordered_set>
#include <set>
using namespace std;

struct Edge {
    int to;
    double capacity, flow, cost, transit_days;
    int rev_index;
};

// UPDATED: Added secondary_chokepoint for fallback routing
struct SupplierData { 
    string name; 
    string primary_chokepoint;
    string secondary_chokepoint;
    double normal_capacity; 
    double alt_capacity; 
};

struct RefineryData { string name; double demand_bpd; };

// UPDATED: RouteParams now holds both Primary and Secondary chokepoints
struct RouteParams {
    string primary_chokepoint;
    string secondary_chokepoint;
    double primary_capacity;
    double base_cost;
    double transit_days;
};

class SupplyChainMCMF {
private:
    int n = 0;
    int source, sink;
    vector<vector<Edge>> adj;
    unordered_map<string, int> node_to_id;

    int get_node_id(const string& name) {
        if (node_to_id.find(name) == node_to_id.end()) {
            node_to_id[name] = n++;
            adj.emplace_back();
        }
        return node_to_id[name];
    }

    void add_edge(const string& from, const string& to, double cap, double cost, double transit = 0.0) {
        int u = get_node_id(from), v = get_node_id(to);
        adj[u].push_back({v, cap, 0.0, cost, transit, (int)adj[v].size()});
        adj[v].push_back({u, 0.0, 0.0, -cost, 0.0, (int)adj[u].size() - 1});
    }

    bool spfa(vector<double>& dist, vector<int>& parent_node, vector<int>& parent_edge) {
        dist.assign(n, 1e18); parent_node.assign(n, -1); parent_edge.assign(n, -1);
        vector<bool> in_queue(n, false);
        queue<int> q;
        dist[source] = 0; q.push(source); in_queue[source] = true;

        while (!q.empty()) {
            int u = q.front(); q.pop(); in_queue[u] = false;
            for (size_t i = 0; i < adj[u].size(); ++i) {
                const Edge& e = adj[u][i];
                if (e.capacity - e.flow > 1e-6 && dist[e.to] > dist[u] + e.cost + 1e-9) {
                    dist[e.to] = dist[u] + e.cost;
                    parent_node[e.to] = u;
                    parent_edge[e.to] = i;
                    if (!in_queue[e.to]) { q.push(e.to); in_queue[e.to] = true; }
                }
            }
        }
        return dist[sink] < 1e18;
    }

public:
    SupplyChainMCMF() { source = get_node_id("SUPER_SOURCE"); sink = get_node_id("SUPER_SINK"); }

    string execute_simulation(const unordered_set<string>& blocked) {
        
        // 1. Configure Suppliers with Multi-Tier Routing
        vector<SupplierData> suppliers = {
            {"BASRA_IRAQ", "HORMUZ", "NONE", 1500000, 150000},
            {"RAS_TANURA_SAUDI", "HORMUZ", "NONE", 2000000, 800000},
            {"FUJAIRAH_UAE", "NONE", "NONE", 1200000, 1200000},
            {"KOZMINO_RUSSIA", "MALACCA", "SUNDA_STRAIT", 900000, 500000},
            {"CORPUS_CHRISTI_USA", "SUEZ_CANAL", "CAPE_OF_GOOD_HOPE", 1800000, 1100000}, 
            {"BONNY_ISLAND_NIGERIA", "SUEZ_CANAL", "CAPE_OF_GOOD_HOPE", 1000000, 700000}
        };

        for (const auto& s : suppliers) {
            bool primary_blocked = blocked.count(s.primary_chokepoint) > 0;
            bool supplier_blocked = blocked.count(s.name) > 0;
            
            // If primary route or supplier itself is blocked, throttle the origin capacity
            bool is_blocked = primary_blocked || supplier_blocked;
            double active_cap = is_blocked ? s.alt_capacity : s.normal_capacity;
            add_edge("SUPER_SOURCE", s.name, active_cap, 0.0);
        }

        // 2. Configure Refineries
        vector<RefineryData> refineries = {
            {"JAMNAGAR_RIL", 1370000}, {"KOCHI_BPCL", 310000}, {"PARADIP_IOCL", 300000},
            {"MUMBAI_HPCL", 190000}, {"CHENNAI_CPCL", 210000}
        };
        
        double total_demand = 0;
        for (const auto& r : refineries) {
            add_edge(r.name, "SUPER_SINK", r.demand_bpd, 0.0);
            total_demand += r.demand_bpd;
        }

        // 3. Configure Route Matrix
        unordered_map<string, unordered_map<string, RouteParams>> matrix = {
            {"BASRA_IRAQ", {
                {"JAMNAGAR_RIL", {"HORMUZ", "NONE", 1500000, 78.50, 4.5}}, 
                {"KOCHI_BPCL", {"HORMUZ", "NONE", 500000, 78.50, 6.5}},
                {"MUMBAI_HPCL", {"HORMUZ", "NONE", 500000, 78.50, 5.0}}, 
                {"PARADIP_IOCL", {"HORMUZ", "NONE", 500000, 78.50, 10.0}},
                {"CHENNAI_CPCL", {"HORMUZ", "NONE", 500000, 78.50, 8.5}}
            }},
            {"RAS_TANURA_SAUDI", {
                {"JAMNAGAR_RIL", {"HORMUZ", "NONE", 1500000, 80.00, 4.2}}, 
                {"KOCHI_BPCL", {"HORMUZ", "NONE", 600000, 80.00, 6.2}},
                {"MUMBAI_HPCL", {"HORMUZ", "NONE", 600000, 80.00, 4.8}}, 
                {"PARADIP_IOCL", {"HORMUZ", "NONE", 500000, 80.00, 9.8}},
                {"CHENNAI_CPCL", {"HORMUZ", "NONE", 500000, 80.00, 8.3}}
            }},
            {"FUJAIRAH_UAE", {
                {"JAMNAGAR_RIL", {"NONE", "NONE", 1500000, 81.00, 3.0}}, 
                {"KOCHI_BPCL", {"NONE", "NONE", 500000, 81.00, 5.0}},
                {"MUMBAI_HPCL", {"NONE", "NONE", 500000, 81.00, 3.5}}, 
                {"PARADIP_IOCL", {"NONE", "NONE", 400000, 81.00, 8.5}},
                {"CHENNAI_CPCL", {"NONE", "NONE", 400000, 81.00, 7.0}}
            }},
            {"KOZMINO_RUSSIA", {
                {"JAMNAGAR_RIL", {"MALACCA", "SUNDA_STRAIT", 600000, 74.00, 18.5}}, 
                {"KOCHI_BPCL", {"MALACCA", "SUNDA_STRAIT", 400000, 74.00, 16.0}},
                {"MUMBAI_HPCL", {"MALACCA", "SUNDA_STRAIT", 400000, 74.00, 17.5}}, 
                {"PARADIP_IOCL", {"MALACCA", "SUNDA_STRAIT", 500000, 74.00, 15.5}},
                {"CHENNAI_CPCL", {"MALACCA", "SUNDA_STRAIT", 500000, 74.00, 14.5}}
            }},
            {"CORPUS_CHRISTI_USA", {
                {"JAMNAGAR_RIL", {"SUEZ_CANAL", "CAPE_OF_GOOD_HOPE", 600000, 82.00, 25.0}}, 
                {"KOCHI_BPCL", {"SUEZ_CANAL", "CAPE_OF_GOOD_HOPE", 400000, 82.00, 23.0}},
                {"MUMBAI_HPCL", {"SUEZ_CANAL", "CAPE_OF_GOOD_HOPE", 400000, 82.00, 24.0}}, 
                {"PARADIP_IOCL", {"SUEZ_CANAL", "CAPE_OF_GOOD_HOPE", 400000, 82.00, 25.0}},
                {"CHENNAI_CPCL", {"SUEZ_CANAL", "CAPE_OF_GOOD_HOPE", 400000, 82.00, 23.5}}
            }},
            {"BONNY_ISLAND_NIGERIA", {
                {"JAMNAGAR_RIL", {"SUEZ_CANAL", "CAPE_OF_GOOD_HOPE", 500000, 84.00, 15.0}}, 
                {"KOCHI_BPCL", {"SUEZ_CANAL", "CAPE_OF_GOOD_HOPE", 400000, 84.00, 13.0}},
                {"MUMBAI_HPCL", {"SUEZ_CANAL", "CAPE_OF_GOOD_HOPE", 400000, 84.00, 14.0}}, 
                {"PARADIP_IOCL", {"SUEZ_CANAL", "CAPE_OF_GOOD_HOPE", 400000, 84.00, 15.0}},
                {"CHENNAI_CPCL", {"SUEZ_CANAL", "CAPE_OF_GOOD_HOPE", 400000, 84.00, 13.5}}
            }}
        };

        for (const auto& s : matrix) {
            for (const auto& r : s.second) {
                const auto& p = r.second;
                
                bool primary_blocked = blocked.count(p.primary_chokepoint) > 0;
                bool secondary_blocked = blocked.count(p.secondary_chokepoint) > 0;
                bool supplier_blocked = blocked.count(s.first) > 0;

                double cap = p.primary_capacity;
                double actual_base_cost = p.base_cost;
                double actual_transit = p.transit_days;

                // MULTI-TIER PENALTY LOGIC
                if (supplier_blocked) {
                    cap *= 0.45;
                    actual_base_cost *= 1.40;
                    actual_transit += 12.0;
                } else if (primary_blocked && secondary_blocked && p.secondary_chokepoint != "NONE") {
                    // CATASTROPHIC BLOCKADE: Both primary and fallback routes are closed
                    cap *= 0.10; 
                    actual_base_cost *= 2.50; 
                    actual_transit += 30.0; 
                } else if (primary_blocked) {
                    // STANDARD REROUTE: Primary closed, ships take the longer fallback route
                    cap *= 0.45;
                    actual_base_cost *= 1.40;
                    actual_transit += 12.0;
                }
                // (Note: If only the secondary route is blocked, ships just safely use the open primary route without penalty)

                double cost = actual_base_cost + (actual_transit * 0.5);
                add_edge(s.first, r.first, cap, cost, actual_transit);
            }
        }

        // 4. Run Min-Cost Max-Flow Optimization
        vector<double> dist; vector<int> pn, pe;
        while (spfa(dist, pn, pe)) {
            double push = 1e18;
            for (int v = sink; v != source; v = pn[v]) push = min(push, adj[pn[v]][pe[v]].capacity - adj[pn[v]][pe[v]].flow);
            for (int v = sink; v != source; v = pn[v]) {
                int u = pn[v], idx = pe[v], rev = adj[u][idx].rev_index;
                adj[u][idx].flow += push;
                adj[v][rev].flow -= push;
            }
        }

       // 5. Generate JSON Output with Temporal SPR Constraints
        stringstream ss;
        ss << "{\"status\":\"PROCESSED\",\"refineries\":[";
        double total_flow = 0.0;
        
        // India's actual strategic reserve buffer (days) before refineries run dry
        double INDIA_SPR_DAYS = 9.5; 

        // NEW: Track the absolute longest transit time for the network to stabilize
        double max_stabilization_days = 0.0;

        for (size_t i = 0; i < refineries.size(); ++i) {
            int rid = get_node_id(refineries[i].name);
            double received = 0.0, lag_sum = 0.0, flow_sum = 0.0;
            
            set<string> active_suppliers;

            for (size_t u = 0; u < adj.size(); ++u) {
                for (const auto& e : adj[u]) {
                    if (e.to == rid && e.flow > 1e-6) {
                        received += e.flow; 
                        lag_sum += e.flow * e.transit_days; 
                        flow_sum += e.flow;
                        
                        // NEW: Update network stabilization time to the absolute longest route
                        max_stabilization_days = max(max_stabilization_days, e.transit_days);
                        
                        string supplier_name = "UNKNOWN";
                        for (const auto& pair : node_to_id) {
                            if (pair.second == u) {
                                supplier_name = pair.first;
                                break;
                            }
                        }
                        
                        if (supplier_name != "SUPER_SOURCE" && supplier_name != "UNKNOWN") {
                            active_suppliers.insert(supplier_name);
                        }
                    }
                }
            }
            
            double avg_lag = flow_sum > 0 ? lag_sum / flow_sum : 0.0;
            total_flow += received;

            string status;
            bool volume_fails = (refineries[i].demand_bpd - received > 15);
            bool time_fails = (avg_lag > INDIA_SPR_DAYS);

            if (volume_fails && time_fails) {
                status = "TOTAL_COLLAPSE"; 
            } else if (volume_fails) {
                status = "VOLUME_SHORTFALL"; 
            } else if (time_fails) {
                status = "SPR_EXHAUSTED"; 
            } else {
                status = "OPERATIONAL"; 
            }

            ss << "{\"name\":\"" << refineries[i].name << "\",\"status\":\"" << status
               << "\",\"received_bpd\":" << fixed << setprecision(0) << received
               << ",\"transit_lag_days\":" << fixed << setprecision(1) << avg_lag 
               << ",\"spr_days_remaining\":" << fixed << setprecision(1) << (INDIA_SPR_DAYS - avg_lag)
               << ",\"suppliers\":[";
               
            int sup_idx = 0;
            for (const string& sup : active_suppliers) {
                ss << "\"" << sup << "\"";
                if (sup_idx < active_suppliers.size() - 1) ss << ",";
                sup_idx++;
            }
            ss << "]}";

            if (i < refineries.size() - 1) ss << ",";
        }
        
        // NEW: Appending network_stabilization_days to the final root JSON
        ss << "],\"total_flow\":" << fixed << setprecision(0) << total_flow 
           << ",\"total_demand\":" << fixed << setprecision(0) << total_demand 
           << ",\"network_stabilization_days\":" << fixed << setprecision(1) << max_stabilization_days 
           << ",\"blocked\":[";
        
        for (auto it = blocked.begin(); it != blocked.end(); ++it) {
            if (it != blocked.begin()) ss << ",";
            ss << "\"" << *it << "\"";
        }
        ss << "]}";

        return ss.str();
    }
};

int main(int argc, char* argv[]) {
    // 1. Define valid IDs for input validation
    const unordered_set<string> valid_chokepoints = {
        "HORMUZ", "MALACCA", "BAB_EL_MANDEB", "CAPE_OF_GOOD_HOPE", "SUEZ_CANAL", "SUNDA_STRAIT"
    };

    const unordered_set<string> valid_suppliers = {
        "BASRA_IRAQ", "RAS_TANURA_SAUDI", "FUJAIRAH_UAE", 
        "KOZMINO_RUSSIA", "CORPUS_CHRISTI_USA", "BONNY_ISLAND_NIGERIA"
    };

    unordered_set<string> blocked;

    // 2. Process and Validate inputs from CLI arguments
    for (int i = 1; i < argc; ++i) {
        string arg = argv[i];
        
        bool is_valid_chokepoint = valid_chokepoints.find(arg) != valid_chokepoints.end();
        bool is_valid_supplier = valid_suppliers.find(arg) != valid_suppliers.end();

        // Only insert into blocked set if it is a known, valid entity
        if (is_valid_chokepoint || is_valid_supplier) {
            blocked.insert(arg);
        } else {
            // Log warnings for debugging unknown IDs passed by Python
            cerr << "[Simulation Warning] Ignoring invalid/unknown ID: " << arg << endl;
        }
    }
    
    // 3. Fallback if no valid items are blocked
    if (blocked.empty()) blocked.insert("NONE");

    SupplyChainMCMF engine;
    cout << engine.execute_simulation(blocked) << endl;
    
    return 0;
}