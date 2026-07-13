#!/bin/bash

# Exit instantly if any sequential command stumbles
set -e

echo "=== 1. Setting up Python Virtual Environment & Requirements ==="
python3 -m venv venv
source venv/bin/activate

# Install essential packages needed for the workflow
pip install --upgrade pip
pip install grpcio grpcio-tools langchain-core langchain-openai

echo "=== 2. Compiling Protocol Buffers via grpcio-tools ==="
# Generates files inside proto directory to avoid import mismatches
python3 -m grpc_tools.protoc \
    -I./gRPC/proto \
    --python_out=./gRPC/proto \
    --grpc_python_out=./gRPC/proto \
    ./gRPC/proto/energy.proto

echo "=== 3. Starting gRPC AI-Orchestrator Server Context ==="
# Spin up server background process
python3 gRPC/server/index.py &
SERVER_PID=$!

# Give the server a brief window to bind to socket port 50051
sleep 2

echo "=== 4. Launching Mock Ingestion Stream Client ==="
# Fire up client routine
python3 gRPC/client/index.py

# Cleanup backgrounds components upon manual exit termination
echo "Halting operational stack processes..."
kill $SERVER_PID