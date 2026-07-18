const ImpactDashboard = ({ data, onReset }) => {
  return (
    <div style={{ 
      position: 'absolute', top: 20, left: 20, 
      background: 'rgba(15, 15, 15, 0.95)', color: '#fff', 
      padding: '20px', borderRadius: '8px', border: '1px solid #444',
      fontFamily: 'monospace', minWidth: '320px'
    }}>
      
      <button 
        onClick={onReset}
        style={{
          position: 'absolute', top: '10px', right: '15px',
          background: 'transparent', border: 'none', color: '#aaa',
          fontSize: '18px', cursor: 'pointer', padding: '5px'
        }}
        onMouseEnter={(e) => e.target.style.color = '#fff'}
        onMouseLeave={(e) => e.target.style.color = '#aaa'}
      >
        ✖
      </button>

      <h3 style={{ margin: '0 0 15px 0', color: '#ff4444' }}>GLOBAL SUPPLY CHAIN IMPACT</h3>
      <div style={{ marginBottom: '15px', paddingBottom: '10px', borderBottom: '1px solid #333' }}>
        <p style={{ margin: '5px 0' }}>
          <strong>Network Flow:</strong> {data.total_flow?.toLocaleString()} / {data.total_demand?.toLocaleString()} BPD
        </p>
      </div>

      <h4 style={{ margin: '0 0 10px 0', color: '#aaa' }}>REFINERY TRANSIT LAGS & SOURCING</h4>
      {data.refineries?.map((ref, idx) => (
        <div key={idx} style={{ marginBottom: '12px', fontSize: '13px' }}>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
            <strong style={{ color: ref.status === 'SHORTFALL' ? '#ff4444' : '#00ff00' }}>{ref.name}</strong>
            <span>{ref.transit_lag_days?.toFixed(1)} Days</span>
          </div>
          
          <div style={{ color: '#888', display: 'flex', flexDirection: 'column', gap: '3px' }}>
            <span>Received: {ref.received_bpd?.toLocaleString()} BPD</span>
            
            {/* THIS LINE NOW READS YOUR C++ OUTPUT */}
            <span style={{ color: '#44ccff', fontSize: '11.5px' }}>
              ⮑ Source: {ref.suppliers && ref.suppliers.length > 0 
                ? ref.suppliers.join(', ') 
                : 'Awaiting Routing Data...'}
            </span>
          </div>
          
        </div>
      ))}
    </div>
  );
};

export default ImpactDashboard;