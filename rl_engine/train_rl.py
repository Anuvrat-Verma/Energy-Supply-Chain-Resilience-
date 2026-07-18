import os
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.utils import set_random_seed
from stable_baselines3.common.callbacks import CheckpointCallback
from spr_env import SPROptimizationEnv

def train_agent():
    # 1. Setup Environment
    set_random_seed(42)
    env = SPROptimizationEnv()
    
    # Ensure model directory exists
    model_dir = "models"
    os.makedirs(model_dir, exist_ok=True)
    
    print("🚀 Initializing Production-Grade LSTM-SPR Training Pipeline...")

    # 2. Recurrent Neural Architecture Configuration
    # We switch to MlpLstmPolicy to enable memory of past refinery depletion rates.
    # The LSTM hidden size (256) allows the agent to track depletion trends over time.
    policy_kwargs = dict(
        lstm_hidden_size=256,
        net_arch=dict(pi=[128, 128], vf=[128, 128])
    )

    model = RecurrentPPO(
        "MlpLstmPolicy",
        env,
        verbose=1,
        learning_rate=1e-4,
        n_steps=128,             # Unrolls sequential timeline fragments
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        policy_kwargs=policy_kwargs
    )

    # 3. Training Loop
    total_timesteps = 200_000
    print(f"🧠 Training LSTM-RL agent for {total_timesteps} timesteps...")
    
    checkpoint_callback = CheckpointCallback(
        save_freq=50000, 
        save_path=model_dir,
        name_prefix="lstm_spr_checkpoint"
    )

    model.learn(
        total_timesteps=total_timesteps, 
        callback=checkpoint_callback,
        progress_bar=True
    )

    # 4. Save Final Brain
    save_path = "lstm_advanced_spr_agent"
    model.save(save_path)
    
    print(f"\n✅ Training Complete!")
    print(f"💾 LSTM Policy saved to: {os.path.abspath(save_path)}.zip")
    print("💡 Tip: Ensure your inference script (ai_workflow_spr.py) is using RecurrentPPO.load().")

if __name__ == "__main__":
    train_agent()