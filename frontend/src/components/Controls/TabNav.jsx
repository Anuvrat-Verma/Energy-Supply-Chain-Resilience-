const TABS = [
  { id: 1, label: 'Tab 1: Maritime Operations & Risk' },
  { id: 2, label: 'Tab 2: Economic' },
  { id: 3, label: 'Tab 3: Procurement' },
  { id: 4, label: 'Tab 4: SPR' },
];

const TabNav = ({ activeTab, setActiveTab, systemMode, onToggleMode }) => {
  return (
    <nav className="tab-nav">
      <div className="tab-nav-buttons">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab-nav-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="mode-toggle">
        <span className={`mode-label ${systemMode === 'LIVE' ? 'active' : ''}`}>LIVE</span>
        <button
          type="button"
          className={`mode-switch ${systemMode === 'SANDBOX' ? 'sandbox' : 'live'}`}
          onClick={onToggleMode}
          aria-label="Toggle system mode between LIVE and SANDBOX"
        >
          <span className="mode-switch-knob" />
        </button>
        <span className={`mode-label ${systemMode === 'SANDBOX' ? 'active' : ''}`}>SANDBOX</span>
      </div>
    </nav>
  );
};

export default TabNav;
