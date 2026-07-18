import { useState } from 'react';
import './App.css';
import GlobalMap from './components/Map/GlobalMap';
import { useSimulation } from './hooks/useSimulation';
import Tab1Physical from './components/Tab1Physical';
import Tab2Economic from './components/Tab2Economic';
import Tab3 from './components/Tab3';
import Tab4 from './components/Tab4';
import TabNav from './components/Controls/TabNav';
import SandboxPromptModal from './components/Controls/SandboxPromptModal';

function App() {
  const [selectedChokepoints, setSelectedChokepoints] = useState([]);
  const [activeTab, setActiveTab] = useState(1);
  const [systemMode, setSystemMode] = useState('LIVE'); // Boots up in LIVE mode by default
  const [showSandboxPrompt, setShowSandboxPrompt] = useState(false);

  // Custom hook manages API and WebSockets
  const { simulationData, setSimulationData, setMode, triggerSandboxSimulation } = useSimulation(selectedChokepoints);

  // Unified reset clears the data card and empties the map selection
  const handleReset = () => {
    setSimulationData(null);
    setSelectedChokepoints([]);
  };

  const handleToggleMode = () => {
    if (systemMode === 'LIVE') {
      // Switching to SANDBOX requires the user to author a custom news feed first
      setShowSandboxPrompt(true);
    } else {
      // Switching back to LIVE is immediate — real RSS feeds take over automatically
      setMode('LIVE');
      setSystemMode('LIVE');
    }
  };

  const handleSandboxSubmit = async (newsFeed) => {
    await setMode('SANDBOX');
    setSystemMode('SANDBOX');
    setShowSandboxPrompt(false);
    triggerSandboxSimulation(newsFeed);
  };

return (
    <div className="dashboard-layout">
      
      {/* Map is only relevant for the physical/geographic tab — hidden for Economic, Procurement & SPR */}
      {activeTab !== 2 && activeTab !== 3 && activeTab !== 4 && (
        <div className="map-view-container">
          <GlobalMap
            selectedChokepoints={selectedChokepoints}
            setSelectedChokepoints={setSelectedChokepoints}
          />
        </div>
      )}

      {/* Tab Data Panel */}
      <div className={`sidebar-data-panel ${activeTab === 2 || activeTab === 3 || activeTab === 4 ? 'full-width' : ''}`}>
        <TabNav
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          systemMode={systemMode}
          onToggleMode={handleToggleMode}
        />

        {activeTab === 1 && <Tab1Physical data={simulationData?.tab1_physical_routing} />}
        {activeTab === 2 && <Tab2Economic data={simulationData?.tab2_economic_impact} />}
        {activeTab === 3 && <Tab3 data={simulationData?.tab3_procurement_strategy} />}
        {activeTab === 4 && <Tab4 data={simulationData?.tab4_spr_optimization} />}
      </div>

      {showSandboxPrompt && (
        <SandboxPromptModal
          onSubmit={handleSandboxSubmit}
          onCancel={() => setShowSandboxPrompt(false)}
        />
      )}

    </div>
  );
}

export default App;