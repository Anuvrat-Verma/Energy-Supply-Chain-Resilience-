const ACCENTS = {
  'accent-blue': 'border-blue-500',
  'accent-orange': 'border-amber-500',
  'accent-purple': 'border-purple-500',
  'accent-red': 'border-red-500',
};

const Tab2Economic = ({ data }) => {
  if (!data) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-zinc-950 text-zinc-500 text-sm uppercase tracking-widest">
        Waiting for Economic Impact Analysis...
      </div>
    );
  }

  const { refinery_run_rates, domestic_fuel_prices, power_sector_stress, gdp_trajectory } = data;

  const sections = [
    { key: 'refinery', title: 'Refinery Run Rates', text: refinery_run_rates, icon: '🏭', accent: 'accent-blue' },
    { key: 'fuel', title: 'Domestic Fuel Prices', text: domestic_fuel_prices, icon: '⛽', accent: 'accent-orange' },
    { key: 'power', title: 'Power Sector Stress', text: power_sector_stress, icon: '⚡', accent: 'accent-purple' },
    { key: 'gdp', title: 'GDP Trajectory', text: gdp_trajectory, icon: '📉', accent: 'accent-red' },
  ];

  return (
    <div className="w-full h-full bg-zinc-950 text-zinc-200 p-4 md:p-6 flex flex-col gap-5 overflow-y-auto">
      <header className="w-full border border-blue-500/40 bg-gradient-to-r from-blue-500/10 via-zinc-900 to-zinc-900 rounded-lg p-5 shadow-[0_0_25px_-5px_rgba(59,130,246,0.35)]">
        <p className="text-2xl md:text-3xl font-extrabold uppercase tracking-wide text-blue-400 mb-2">
          Tab 2 &middot; Cascading Economic Impact
        </p>
        <p className="text-sm leading-relaxed text-zinc-300/90 max-w-4xl">
          Macroeconomic ripple effects modeled from the current physical supply disruption —
          refinery output, retail pricing, grid stress, and national growth trajectory.
        </p>
      </header>

      <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-4">
        {sections.map((section) => (
          <div
            key={section.key}
            className={`border-l-4 ${ACCENTS[section.accent]} bg-zinc-900 rounded-md p-4`}
          >
            <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-zinc-300 mb-3">
              <span className="text-base">{section.icon}</span>
              {section.title}
            </h3>
            <p className="text-sm leading-relaxed text-zinc-400">
              {section.text || 'No data available.'}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Tab2Economic;
