import gymnasium as gym
from gymnasium import spaces
import numpy as np

class SPROptimizationEnv(gym.Env):
    """
    20-Dimensional Macroeconomic & Spatial Energy Crisis Environment.
    Optimized for RecurrentPPO (LSTM) deep sequential learning.
    
    State Vector Index Mapping (Fully Normalized):
    [0]  - Normalized Shortfall (Current deficit / Max Pipeline Capacity)
    [1]  - Temporal Horizon Progress (Current Step / Max Crisis Days)
    [2]  - Reserves Remaining Ratio (Current SPR / Max Initial SPR)
    [3]  - Previous Action Velocity (Throttling history for LSTM continuity)
    [4]  - Jamnagar Refinery Runway Days Remaining (Normalized to max 30 days)
    [5]  - Kochi Refinery Runway Days Remaining
    [6]  - Paradip Refinery Runway Days Remaining
    [7]  - Mumbai Refinery Runway Days Remaining
    [8]  - Chennai Refinery Runway Days Remaining
    [9]  - Exhausted Refinery Ratio (Count of collapsed nodes / Total nodes)
    [10] - Financial Friction Index (Scaled fiscal stress penalty)
    [11] - Confidence Variance Score (Model's calculated environmental volatility)
    [12] - Spatial Risk: Strait of Hormuz Blockage Factor [0.0 - 1.0]
    [13] - Spatial Risk: Malacca Strait Blockage Factor [0.0 - 1.0]
    [14] - Spatial Risk: Bab el-Mandeb Blockage Factor [0.0 - 1.0]
    [15] - Spatial Risk: Cape of Good Hope Routing Overhead [0.0 - 1.0]
    [16-19] - Network Stabilization Lag Metrics (Temporal propagation vectors)
    """
    def __init__(self):
        super(SPROptimizationEnv, self).__init__()
        
        self.MAX_CAPACITY_BPD = 1500000.0
        self.INITIAL_RESERVES = 30000000.0
        self.MAX_RUNWAY_DAYS = 30.0
        
        # Action Space: Continuous value [0.0, 1.0] representing % of max drawdown capacity
        self.action_space = spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)
        
        # Observation Space: 20 dimensions strictly bounded to safeguard neural tracking
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(20,), dtype=np.float32)
        
        # Node capacity weights matching physical infrastructure distribution
        self.capacity_weights = {
            4: 1.37,  # Jamnagar
            5: 0.31,  # Kochi
            6: 0.30,  # Paradip
            7: 0.19,  # Mumbai
            8: 0.21   # Chennai
        }
        self.reset()

    def reset(self, seed=None, options=None):
        super(SPROptimizationEnv, self).reset(seed=seed)
        # Seed for reproducibility if needed
        if seed is not None:
            np.random.seed(seed)
            
        self.reserves_remaining = self.INITIAL_RESERVES
        self.current_step = 0
        self.horizon_days = 20.0
        self.prev_action = 0.0
        
        self.state = np.zeros(20, dtype=np.float32)
        
        # DOMAIN RANDOMIZATION: +/- 15% variance so the model generalizes
        base_shortfall = 150000.0
        randomized_shortfall = base_shortfall * np.random.uniform(0.85, 1.15)
        
        self.state[0] = randomized_shortfall / self.MAX_CAPACITY_BPD 
        self.state[1] = 0.0                               
        self.state[2] = 1.0                               
        self.state[3] = 0.0                               
        
        # Randomize starting runway buffers between 8 to 12 days
        for idx in range(4, 9):
            starting_runway = np.random.uniform(8.0, 12.0)
            self.state[idx] = starting_runway / self.MAX_RUNWAY_DAYS
            
        # Add slight noise to Spatial Risks so it adapts to different geopolitical maps
        self.state[12] = np.clip(np.random.normal(0.90, 0.05), 0.0, 1.0)  # Hormuz
        self.state[13] = np.clip(np.random.normal(0.10, 0.02), 0.0, 1.0)  # Malacca
        self.state[14] = np.clip(np.random.normal(0.40, 0.05), 0.0, 1.0)  # Bab el-Mandeb
        self.state[15] = np.clip(np.random.normal(0.65, 0.05), 0.0, 1.0)  # Cape
        
        return self.state, {}

    def step(self, action):
        self.current_step += 1
        action_val = np.clip(action[0], 0.0, 1.0)
        
        # 1. Action Execution & Reserve Depletion
        release_bpd = float(action_val * self.MAX_CAPACITY_BPD)
        self.reserves_remaining = max(self.reserves_remaining - release_bpd, 0.0)
        
        # De-normalize shortfall for structural physical computations
        raw_shortfall = self.state[0] * self.MAX_CAPACITY_BPD
        
       # 2. Physics & Temporal Degradation Math (Capacity-Weighted)
        mitigation_ratio = release_bpd / max(raw_shortfall, 1.0)
        base_depletion = 1.0 - (mitigation_ratio * 0.9) 
        
        for idx in range(4, 9):
            # NEW: Bigger refineries burn through runway faster if starved
            node_specific_depletion = base_depletion * (self.capacity_weights[idx] / 0.5) 
            current_runway_days = (self.state[idx] * self.MAX_RUNWAY_DAYS) - node_specific_depletion
            self.state[idx] = np.clip(current_runway_days / self.MAX_RUNWAY_DAYS, 0.0, 1.0)
        
        # Update and clamp individual refinery runways dynamically
        for idx in range(4, 9):
            current_runway_days = (self.state[idx] * self.MAX_RUNWAY_DAYS) - node_specific_depletion
            self.state[idx] = np.clip(current_runway_days / self.MAX_RUNWAY_DAYS, 0.0, 1.0)
            
        # 3. Microeconomic Loss & Compounding Failure Tracking
        exhausted_refineries = 0.0
        node_penalties = 0.0
        
        for idx in range(4, 9):
            if self.state[idx] <= 0.0:
                exhausted_refineries += 1.0
                node_penalties += 5.0 * self.capacity_weights[idx]
        
        # Calculate dynamic Financial Friction based on unmet supply and collapsed networks
        unmet_shortfall = max(raw_shortfall - release_bpd, 0.0)
        financial_friction = (unmet_shortfall / self.MAX_CAPACITY_BPD) * 10.0 + (node_penalties * 2.0)
        
        # Compute structural Confidence Variance (increases with volatility and asset failures)
        volatility_delta = abs(action_val - self.prev_action)
        confidence_variance = (volatility_delta * 0.3) + (exhausted_refineries / 5.0) * 0.7
        
        # 4. Synchronize Telemetry Back into the Normalized Observation State Space
        self.state[0] = np.clip(unmet_shortfall / self.MAX_CAPACITY_BPD, 0.0, 1.0)
        self.state[1] = np.clip(self.current_step / self.horizon_days, 0.0, 1.0)
        self.state[2] = np.clip(self.reserves_remaining / self.INITIAL_RESERVES, 0.0, 1.0)
        self.state[3] = action_val
        self.state[9] = exhausted_refineries / 5.0
        self.state[10] = np.clip(financial_friction / 50.0, 0.0, 1.0) 
        self.state[11] = np.clip(confidence_variance, 0.0, 1.0)
        
        # 5. Reward Optimization Strategy (Smoothed)
        reward = 0.0
        
        # [POSITIVE] Incremental Efficiency Bonus (Drip-fed per step instead of all at the end)
        efficiency_ratio = self.reserves_remaining / self.INITIAL_RESERVES
        reward += 2.5 * efficiency_ratio  # Encourages keeping reserves high at every single step
        
        for idx in range(4, 9):
            if self.state[idx] > 0.0:
                reward += 0.2 * self.capacity_weights[idx]
        
        # [POSITIVE] Terminal Success Flag (Much smaller now since it was drip-fed)
        if self.current_step >= int(self.horizon_days) and self.reserves_remaining > 0:
            reward += 10.0

        # [PENALTY] Non-linear Drawdown friction (curbs rapid pipeline degradation loops)
        reward -= 2.0 * (action_val ** 2)
        
        # [PENALTY] Macro systemic collapse costs
        reward -= 1.5 * financial_friction
        if exhausted_refineries > 0:
            reward -= 5.0 * (exhausted_refineries ** 1.35)
            
        # 6. Lifecycle Management
        terminated = self.reserves_remaining <= 0 or self.current_step >= int(self.horizon_days)
        truncated = False
        
        self.prev_action = action_val
        
        return self.state, float(reward), terminated, truncated, {}