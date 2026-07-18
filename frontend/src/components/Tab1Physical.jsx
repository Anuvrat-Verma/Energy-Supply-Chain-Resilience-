import React from 'react';

const Tab1Physical = ({ data }) => {
  if (!data) {
    return <div className="no-data">Waiting for Physical Intel...</div>;
  }

  const { risks, overall_summary, triggered_simulation_json } = data;

  // Parse triggered_simulation_json if it's a string
  let simData = triggered_simulation_json;
  if (typeof triggered_simulation_json === 'string') {
    try {
      simData = JSON.parse(triggered_simulation_json);
    } catch (e) {
      console.error("Failed to parse simulation JSON", e);
    }
  }

  return (
    <div className="tab1-container">
      <header className="tab1-header">
        <h2>TAB 1: Maritime Operations & Risk</h2>
        <div className="summary-box">
          <p>{overall_summary}</p>
        </div>
      </header>

      <div className="risks-section">
        <h3>Active Chokepoint Risks</h3>
        <div className="risks-scroll">
          {risks && risks.map((risk, idx) => (
            <div key={idx} className="risk-item">
              <div className="risk-item-header">
                <span className="chokepoint-name">{risk.chokepoint_name}</span>
                <span className="prob-value">{risk.disruption_probability}%</span>
              </div>
              <div className="risk-progress-bg">
                <div
                  className="risk-progress-fill"
                  style={{ width: `${risk.disruption_probability}%` }}
                />
              </div>
              <p className="risk-reasoning">{risk.risk_reasoning}</p>
              <div className="supplier-tag">
                Impacts: {risk.affected_supplier}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="refinery-section">
        <h3>Refinery Runways &amp; Resilience</h3>
        {simData && simData.refineries ? (
          <div className="refinery-grid">
            {simData.refineries.map((ref, idx) => {
              const isExhausted = ref.status.toLowerCase() === 'spr_exhausted';
              return (
                <div
                  key={idx}
                  className={`refinery-card ${isExhausted ? 'status-spr_exhausted' : ''}`}
                >
                  <p className="refinary-name">{ref.name.replace(/_/g, ' ')}</p>
                  <div className="runway-stat">
                    <span className="label">SPR Runway</span>
                    <span className={`value ${ref.spr_days_remaining < 2 ? 'critical' : ''}`}>
                      {ref.spr_days_remaining.toFixed(1)} Days
                    </span>
                  </div>
                  <div className="load-stat">
                    <span className="label">Throughput</span>
                    <span className="value">{(ref.received_bpd / 1000).toFixed(0)}k BPD</span>
                  </div>
                  <div className="source-stat">
                    <span className="source-arrow">⮑</span>
                    <span className="source-value">
                      {ref.suppliers && ref.suppliers.length > 0
                        ? ref.suppliers.join(', ').replace(/_/g, ' ')
                        : 'Awaiting Routing Data...'}
                    </span>
                  </div>
                  <div className="refinery-status-badge">{ref.status}</div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="no-data">Waiting for C++ Engine stabilization...</p>
        )}
      </div>

      {simData && (
        <footer className="network-footer">
          <div className="stat-pill">
            <span className="label">Network Stabilization Days:</span>
            <span className="value">{simData.network_stabilization_days} Days</span>
          </div>
          <div className="stat-pill">
            <span className="label">Total System Flow:</span>
            <span className="value">{(simData.total_flow / 1000000).toFixed(2)}M BPD</span>
          </div>
        </footer>
      )}
    </div>
  );
};

export default Tab1Physical;
