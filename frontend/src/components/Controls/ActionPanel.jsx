const ActionPanel = ({ selectedChokepoints, onExecute }) => {
  if (selectedChokepoints.length === 0) return null;

  return (
    <button 
      onClick={onExecute}
      style={{
        position: 'absolute', bottom: 40, left: '50%', transform: 'translateX(-50%)',
        padding: '15px 30px', fontSize: '18px', fontWeight: 'bold', cursor: 'pointer',
        backgroundColor: '#ff4444', color: 'white', border: 'none', borderRadius: '8px',
        boxShadow: '0 4px 15px rgba(255,0,0,0.4)', textTransform: 'uppercase'
      }}
    >
      Execute Crisis Scenario ({selectedChokepoints.length} Blocked)
    </button>
  );
};

export default ActionPanel;