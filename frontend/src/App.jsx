import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import mapData from './map_data.json'; 

// Set your token
mapboxgl.accessToken = 'your_access_token_here';

function App() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [simulationData, setSimulationData] = useState(null);

// --- HOOK 1: MAPBOX INITIALIZATION ---
  useEffect(() => {
    // SAFETY GUARD: If the map instance already exists, do not initialize it again!
    if (map.current) return;

    // 1. Initialize Map
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [65.0, 20.0], 
      zoom: 3.5 
    });

    map.current.on('load', () => {
      // 2. Plot Refineries
      const refFeatures = mapData.refineries.map(ref => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: ref.coords },
        properties: { name: ref.id }
      }));

      map.current.addSource('refineries', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: refFeatures }
      });

      map.current.addLayer({
        id: 'refinery-points',
        type: 'circle',
        source: 'refineries',
        paint: { 'circle-radius': 6, 'circle-color': '#00ff00' }
      });

      // 3. Plot Chokepoints
      const chokeFeatures = mapData.chokepoints.map(cp => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: cp.coords },
        properties: { name: cp.id }
      }));

      map.current.addSource('chokepoints', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: chokeFeatures }
      });

      map.current.addLayer({
        id: 'chokepoint-points',
        type: 'circle',
        source: 'chokepoints',
        paint: { 
            'circle-radius': 10, 
            'circle-color': '#ff0000',
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff'
        } 
      });

      // 4. Trigger Simulation on Chokepoint Click
      map.current.on('click', 'chokepoint-points', (e) => {
        const chokepointName = e.features[0].properties.name;
        
        fetch('http://127.0.0.1:8000/trigger-simulation', {
          method: 'POST',
          body: JSON.stringify({ chokepoint: chokepointName }),
          headers: { 'Content-Type': 'application/json' }
        })
        .then(res => res.json())
        .then(data => console.log("Simulation Initiated:", data));

        alert(`Simulation initialized for geopolitical chokepoint: ${chokepointName}`);
      });

      map.current.on('mouseenter', 'chokepoint-points', () => {
          map.current.getCanvas().style.cursor = 'pointer';
      });
      map.current.on('mouseleave', 'chokepoint-points', () => {
          map.current.getCanvas().style.cursor = '';
      });
    });
  }, []); // End of Map Hook

  // --- HOOK 2: WEBSOCKET LISTENER ---
  useEffect(() => {
    const ws = new WebSocket('ws://127.0.0.1:8000/ws');
    
    ws.onopen = () => {
      console.log("WebSocket connected successfully to FastAPI gateway.");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Real-time update from C++ Engine:", data);
      setSimulationData(data); // Triggers HUD render
    };

    ws.onerror = (error) => {
      console.error("WebSocket Error:", error);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, []); // End of WebSocket Hook

  return (
    <div style={{ position: 'relative', height: '100vh' }}>
      <div ref={mapContainer} style={{ height: '100%', width: '100%' }} />
      
      {/* HUD for Simulation Results */}
      {simulationData && (
        <div style={{ 
          position: 'absolute', 
          top: 20, 
          left: 20, 
          background: 'rgba(17, 17, 17, 0.9)', 
          color: '#fff', 
          padding: '15px', 
          borderRadius: '8px',
          border: '1px solid #444',
          fontFamily: 'monospace'
        }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#ff4444' }}>SYSTEM ALERT</h3>
          <p style={{ margin: '5px 0' }}><strong>Chokepoint:</strong> {simulationData.blocked_node}</p>
          <p style={{ margin: '5px 0' }}><strong>SPR Days Left:</strong> {simulationData.spr_days_remaining?.toFixed(2)}</p>
          <p style={{ margin: '5px 0' }}><strong>Shortfall:</strong> {simulationData.total_national_shortfall_bpd} BPD</p>
        </div>
      )}
    </div>
  );
}

export default App;