#!/bin/bash

# Exit instantly if any sequential command stumbles
set -e

# Always operate relative to this script's own directory (project root)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "=== 1. Setting up Python Virtual Environment & Requirements ==="
if [ ! -d venv ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install essential packages needed for the workflow
pip install --upgrade pip
pip install \
    grpcio grpcio-tools protobuf \
    fastapi uvicorn python-dotenv feedparser \
    langchain langchain-core langchain-openai langchain-community langchain-ollama langchain-text-splitters \
    chromadb pydantic numpy \
    sb3-contrib stable-baselines3

echo "=== 2. Compiling Protocol Buffers via grpcio-tools ==="
# Generates files inside the shared generated/ directory used by every service
python3 -m grpc_tools.protoc \
    -I gRPC/proto \
    --python_out=gRPC/generated \
    --grpc_python_out=gRPC/generated \
    gRPC/proto/energy.proto

echo "=== 3. Building C++ Network Engine ==="
g++ -O2 -std=c++17 -o cpp_engine/network_engine cpp_engine/network_engine.cpp

echo "=== 4. Verifying C++ Simulation Engine Binary ==="
# network_engine is a one-shot CLI binary invoked per-request by sim_server.py
# (no persistent process to keep alive) — run a quick smoke test to confirm it works.
if ./cpp_engine/network_engine NONE > /dev/null 2>&1; then
    echo "C++ Network Engine binary verified OK."
else
    echo "[Warning] C++ Network Engine smoke test failed. sim_server.py may error on requests."
fi

echo "=== 5. Verifying RL SPR Optimization Agent ==="
# The trained RecurrentPPO (LSTM) model is loaded in-process by ai_workflow_spr.py,
# so there's no separate server to run — just confirm the trained model is present.
if [ -f rl_engine/lstm_advanced_spr_agent.zip ]; then
    echo "RL SPR Agent model found: rl_engine/lstm_advanced_spr_agent.zip"
else
    echo "[Warning] rl_engine/lstm_advanced_spr_agent.zip not found. Train it first with:"
    echo "          (cd rl_engine && python3 train_rl.py)"
fi

echo "=== 6. Installing Frontend Dependencies ==="
(cd frontend && npm install)

# Track PIDs so we can clean up every process on exit
PIDS=()
cleanup() {
    echo ""
    echo "Halting operational stack processes..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
}
trap cleanup EXIT INT TERM

echo "=== 7. Starting gRPC Simulation Engine (port 50051) ==="
python3 gRPC/simulation_service/sim_server.py &
PIDS+=($!)
sleep 2

echo "=== 8. Starting gRPC AI Orchestrator (port 50052) ==="
python3 gRPC/ai_service/orchestrator_server.py &
PIDS+=($!)
sleep 2

echo "=== 9. Starting FastAPI API Gateway (port 8000) ==="
python3 gRPC/api_gateway/gateway.py &
PIDS+=($!)
sleep 2

echo "=== 10. Starting Frontend Dev Server (port 5173) ==="
(cd frontend && npm run dev -- --host 0.0.0.0) &
PIDS+=($!)

echo ""
echo "All services are running. Press Ctrl+C to stop everything."
wait