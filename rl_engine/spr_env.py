import gymnasium as gym
from gymnasium import spaces
import numpy as np

class SPROptimizationEnv(gym.Env):
    """
    20-Dimensional Macroeconomic & Spatial Energy Crisis Environment.
    Optimized for RecurrentPPO (LSTM) deep sequential learning.
    """
    def __init__(self):
        super(SPROptimizationEnv, self).__init__()
        
        # Action Space: Continuous value [0.0, 1.0] representing % of max drawdown capacity
        # Max capacity normalized to 1,500,000 BPD
        self.action_space = spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)
        
        # Observation Space: 20 dimensions (Physical Math, Temporal Runways, Spatial Risks, Fiscal Stress)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(20,), dtype=np.float32)
        
        self.initial_reserves = 30000000.0
        
        # Capacity weights for the reward function (Jamnagar is 1.37M BPD capacity)
        self.capacity_weights = {
            4: 1.37,  # Jamnagar
            5: 0.31,  # Kochi
            6: 0.30,  # Paradip
            7: 0.19,  # Mumbai
            8: 0.21   # Chennai
        }
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.reserves_remaining = self.initial_reserves
        self.current_step = 0
        
        # Initialize state with a standard crisis scenario
        # Index 0: Shortfall, Index 1: Horizon
        self.state = np.zeros(20, dtype=np.float32)
        
        # DEFAULT SCENARIO: 
        # Set a 20-day crisis horizon so the agent doesn't terminate immediately
        self.state[0] = 150000.0  # Initial Shortfall
        self.state[1] = 20.0      # Horizon: 20 Days
        
        # Initialize refinery runway "days left" (e.g., give them 10 days of runway)
        for idx in range(4, 9):
            self.state[idx] = 10.0
            
        return self.state, {}

    def step(self, action):
        self.current_step += 1
        
        # 1. Action Execution
        release_bpd = float(action[0] * 1500000.0)
        self.reserves_remaining -= release_bpd
        
        # 2. Extract telemetry
        shortfall = self.state[0]
        horizon = self.state[1]
        
        # 3. Physics Updates
        mitigation_ratio = release_bpd / max(shortfall, 1.0)
        depletion_gradient = 1.0 - (mitigation_ratio * 0.9) 
        
        for idx in range(4, 9):
            self.state[idx] -= depletion_gradient
            
        # 4. REWARD FUNCTION (Compounding Failure Logic)
        reward = 0.0
        
        # [POSITIVE] Operational Salary: Paid for keeping nodes alive
        for idx in range(4, 9):
            if self.state[idx] > 0:
                reward += 0.1 * self.capacity_weights[idx]
        
        # [POSITIVE] Mission Success Bonus: Final stabilization reward
        if self.current_step >= horizon and self.reserves_remaining > 0:
            # Bonus is now +50 base + 50 * (percentage of reserves saved)
            efficiency_bonus = 50.0 * (self.reserves_remaining / self.initial_reserves)
            reward += (50.0 + efficiency_bonus)

        # [PENALTY] Inventory cost
        reward -= 0.01 * (release_bpd / 1500000.0)
        
        # [PENALTY] Shortfall penalty
        unmet_shortfall = max(shortfall - release_bpd, 0.0)
        reward -= 0.1 * (unmet_shortfall / 6000000.0)
        
        # [PENALTY] COMPOUNDING REFINERY FAILURE
        exhausted_refineries = 0.0
        for idx in range(4, 9):
            if self.state[idx] < 0:
                # Node-specific penalty
                reward -= 5.0 * abs(self.state[idx]) * self.capacity_weights[idx]
                exhausted_refineries += 1.0
        
        # NON-LINEAR MACRO PENALTY: (exhausted_count ^ 1.25) * 10
        # 1 node = 10, 2 nodes = 40, 3 nodes = 90, 4 nodes = 160...
        if exhausted_refineries > 0:
            reward -= 2.0 * (exhausted_refineries ** 1.25)
        
        self.state[9] = exhausted_refineries
        
        terminated = self.reserves_remaining <= 0 or self.current_step >= horizon
        truncated = False
        
        return self.state, float(reward), terminated, truncated, {}