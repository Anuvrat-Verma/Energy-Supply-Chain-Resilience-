import { useState, useEffect } from 'react';

export const useSimulation = (selectedChokepoints) => {
  const [simulationData, setSimulationData] = useState(null);

  useEffect(() => {
    const ws = new WebSocket('ws://127.0.0.1:8000/ws');
    
    ws.onopen = () => console.log("WebSocket connected successfully.");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("WebSocket Broadcast:", data.type, data.payload);
      
      // The gateway broadcasts objects like { type: "TAB_1_DATA", payload: {...} }
      // We catch the payload if it's the right type
      if (data.type === "TAB_1_DATA") {
        setSimulationData(prev => ({
          ...prev,
          tab1_physical_routing: data.payload
        }));
      } else if (data.type === "TAB_2_DATA") {
        setSimulationData(prev => ({
          ...prev,
          tab2_economic_impact: data.payload
        }));
      } else if (data.type === "TAB_3_DATA") {
        setSimulationData(prev => ({
          ...prev,
          tab3_procurement_strategy: data.payload
        }));
      } else if (data.type === "TAB_4_DATA") {
        setSimulationData(prev => ({
          ...prev,
          tab4_spr_optimization: data.payload
        }));
      } else {
        // Fallback for direct simulation results
        setSimulationData(data);
      }
    };
    ws.onerror = (error) => console.error("WebSocket Error:", error);
    
    return () => ws.close();
  }, []);

  const runSimulation = () => {
    fetch('http://127.0.0.1:8000/trigger-simulation', {
      method: 'POST',
      body: JSON.stringify({ blocked: selectedChokepoints }),
      headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => console.log("Simulation Initiated:", data))
    .catch(err => console.error("API Error:", err));
  };

  // Toggles the backend between LIVE (real RSS feeds) and SANDBOX (manual injection) modes
  const setMode = (mode) => {
    return fetch('http://127.0.0.1:8000/set-mode', {
      method: 'POST',
      body: JSON.stringify({ mode }),
      headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => { console.log("Mode Switched:", data); return data; })
    .catch(err => console.error("API Error:", err));
  };

  // Injects a custom, user-authored news feed while the backend is in SANDBOX mode
  const triggerSandboxSimulation = (newsFeed) => {
    return fetch('http://127.0.0.1:8000/trigger-simulation', {
      method: 'POST',
      body: JSON.stringify({ news_feed: newsFeed }),
      headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => { console.log("Sandbox Simulation Triggered:", data); return data; })
    .catch(err => console.error("API Error:", err));
  };

  return { simulationData, setSimulationData, runSimulation, setMode, triggerSandboxSimulation };
};