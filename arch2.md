graph TD
    %% STYLE DEFINITIONS
    classDef native fill:#7f1d1d,stroke:#f87171,stroke-width:2px,color:#fff
    classDef ai fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
    classDef ui fill:#1e293b,stroke:#94a3b8,stroke-width:2px,color:#fff
    classDef data fill:#171717,stroke:#ec4899,stroke-width:2px,color:#fff

    %% INGESTION & UI
    NEWS[Live RSS Geopolitical Feed]:::data
    UI([React Executive Dashboard]):::ui
    RAG[(Chroma Vector DB: Macro & Maritime)]:::data

    %% AI WORKFLOW 1 (PHYSICAL)
    subgraph W1 [Phase 1: Kinetic Intel]
        LLM_RISK[LLM: Threat Scoring Agent]:::ai
        MCMF[[C++ Min-Cost-Max-Flow Engine]]:::native
        NEWS --> LLM_RISK --> MCMF
    end

    %% PARALLEL EXECUTION (ECON & PROCUREMENT)
    subgraph Parallel [Phase 2: Parallel Strategy Generation]
        direction LR
        
        subgraph W2 [Econ Workflow]
            ECON_LCEL[LCEL: 4-Persona Economic Cascade]:::ai
        end
        
        subgraph W3 [Procurement Workflow]
            PROC_RAG[Dynamic RAG + Strategy Agent]:::ai
        end
    end

    %% AI WORKFLOW 4 (SPR)
    subgraph W4 [Phase 3: Mathematical Convergence]
        FEAT[20-D Neuro-Symbolic Feature Extractor]:::ai
        RL_LSTM[[Monte Carlo RL + LSTM Policy]]:::native
        DP[[Dynamic Programming Solver]]:::native
        
        FEAT --> RL_LSTM
        FEAT --> DP
    end

    %% DATA FLOW WIRING
    MCMF --> W2 & W3
    RAG -.-> W2 & W3
    W2 & W3 --> FEAT
    RL_LSTM & DP -->|"gRPC Protobuf Payload"| UI