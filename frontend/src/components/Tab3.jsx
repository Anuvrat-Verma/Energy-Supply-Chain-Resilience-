const formatBpd = (value) => {
  if (typeof value !== 'number') return 'N/A';
  return value.toLocaleString('en-US');
};

const parseSplitPercent = (value) => {
  const parsed = parseFloat(String(value).replace('%', ''));
  return Number.isNaN(parsed) ? 0 : parsed;
};

const SPLIT_LABELS = {
  west_africa: 'West Africa',
  usgc: 'USGC',
  latin_america: 'Latin America',
};

const SPLIT_BAR_COLORS = {
  west_africa: 'bg-blue-500',
  usgc: 'bg-amber-500',
  latin_america: 'bg-emerald-500',
};

const RiskItem = ({ risk }) => {
  const hasColon = typeof risk === 'string' && risk.includes(':');
  const title = hasColon ? risk.split(':')[0] : null;
  const body = hasColon ? risk.split(':').slice(1).join(':').trim() : risk;

  return (
    <div className="border border-zinc-800 bg-zinc-900/60 rounded-md p-3">
      {title && (
        <p className="text-[11px] font-bold uppercase tracking-wide text-purple-400 mb-1">
          {title}
        </p>
      )}
      <p className="text-sm text-zinc-400 leading-relaxed">{body}</p>
    </div>
  );
};

const Tab3 = ({ data }) => {
  if (!data) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-zinc-950 text-zinc-500 text-sm uppercase tracking-widest">
        Waiting for Procurement Strategy Analysis...
      </div>
    );
  }

  const {
    procurement_strategy_prose,
    recommended_action,
    shortfall_bpd,
    recommended_split,
    estimated_additional_cost,
    key_risks,
    escalation_triggers,
    vessel_specific_actions,
  } = data;

  const splitEntries = recommended_split
    ? Object.entries(recommended_split)
    : [];

  return (
    <div className="w-full h-full bg-zinc-950 text-zinc-200 p-4 md:p-6 flex flex-col gap-5 overflow-y-auto">
      {/* Top Strategic Banner */}
      <section className="w-full border border-amber-500/40 bg-gradient-to-r from-amber-500/10 via-zinc-900 to-zinc-900 rounded-lg p-5 shadow-[0_0_25px_-5px_rgba(245,158,11,0.35)]">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <p className="text-2xl md:text-3xl font-extrabold uppercase tracking-wide text-amber-400 mb-1">
              Tab 3 &middot; Procurement Strategy
            </p>
            <h2 className="text-sm md:text-base font-bold uppercase tracking-wide text-amber-400/80">
              {recommended_action ?? 'NO DIRECTIVE'}
            </h2>
          </div>
        </div>
        <p className="mt-3 text-sm leading-relaxed text-zinc-300/90 max-w-4xl">
          {procurement_strategy_prose ?? 'No strategic overview available.'}
        </p>
      </section>

      {/* KPI Strip */}
      <section className="w-full grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="border-l-4 border-red-500 bg-zinc-900 rounded-md p-4 flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-widest text-zinc-500">
              Volume Deficit
            </p>
            <p className="text-2xl font-extrabold text-red-500 tracking-tight">
              {formatBpd(shortfall_bpd)}{' '}
              <span className="text-sm font-bold text-red-400/80">BPD</span>
            </p>
          </div>
          <span className="text-red-500/60 text-3xl leading-none">&#9650;</span>
        </div>

        <div className="border-l-4 border-emerald-500 bg-zinc-900 rounded-md p-4 flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-widest text-zinc-500">
              Financial Friction
            </p>
            <p className="text-2xl font-extrabold text-emerald-400 tracking-tight">
              {estimated_additional_cost ?? 'N/A'}
            </p>
          </div>
          <span className="text-emerald-500/60 text-3xl leading-none">$</span>
        </div>
      </section>

      {/* 3-Panel Analytical Grid */}
      <section className="w-full grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Panel A: Global Supply Reallocation */}
        <div className="border-l-4 border-blue-500 bg-zinc-900 rounded-md p-4">
          <h3 className="text-xs font-bold uppercase tracking-widest text-blue-400 mb-4">
            Global Supply Reallocation
          </h3>
          <div className="flex flex-col gap-4">
            {splitEntries.length > 0 ? (
              splitEntries.map(([key, value]) => (
                <div key={key}>
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="text-sm text-zinc-400">
                      {SPLIT_LABELS[key] ?? key}
                    </span>
                    <span className="text-sm font-bold text-zinc-100">
                      {value}
                    </span>
                  </div>
                  <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${SPLIT_BAR_COLORS[key] ?? 'bg-blue-500'}`}
                      style={{ width: `${parseSplitPercent(value)}%` }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-zinc-500">No reallocation data available.</p>
            )}
          </div>
        </div>

        {/* Panel B: Fleet Direction Orders */}
        <div className="border-l-4 border-amber-500 bg-zinc-900 rounded-md p-4">
          <h3 className="text-xs font-bold uppercase tracking-widest text-amber-400 mb-4">
            Fleet Direction Orders
          </h3>
          <div className="flex flex-col gap-2 max-h-64 overflow-y-auto pr-1 font-mono">
            {vessel_specific_actions?.length > 0 ? (
              vessel_specific_actions.map((entry, idx) => (
                <div
                  key={`${entry?.vessel ?? 'vessel'}-${idx}`}
                  className="border border-zinc-800 bg-zinc-950/60 rounded-md p-3"
                >
                  <p className="text-sm font-bold text-zinc-100 flex items-center gap-2">
                    <span>🚢</span>
                    <span>{entry?.vessel ?? 'Unknown Vessel'}</span>
                  </p>
                  <p className="text-xs text-amber-400/90 mt-1 pl-6">
                    &gt; {entry?.action ?? 'No action specified.'}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-zinc-500">No vessel directives available.</p>
            )}
          </div>
        </div>

        {/* Panel C: Strategic Risk & Escalation Triggers */}
        <div className="border-l-4 border-purple-500 bg-zinc-900 rounded-md p-4 lg:col-span-2">
          <h3 className="text-xs font-bold uppercase tracking-widest text-purple-400 mb-4">
            Strategic Risk &amp; Escalation Triggers
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Key Risks */}
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-widest text-zinc-500 mb-2">
                Key Risks
              </p>
              <div className="flex flex-col gap-2">
                {key_risks?.length > 0 ? (
                  key_risks.map((risk, idx) => <RiskItem key={idx} risk={risk} />)
                ) : (
                  <p className="text-sm text-zinc-500">No key risks identified.</p>
                )}
              </div>
            </div>

            {/* Escalation Triggers */}
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-widest text-zinc-500 mb-2">
                Escalation Triggers
              </p>
              <div className="flex flex-col gap-3">
                <div className="border border-amber-500/30 bg-amber-500/5 rounded-md p-3">
                  <p className="text-[11px] font-bold uppercase tracking-wide text-amber-400 mb-1">
                    Critical Threshold
                  </p>
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    {escalation_triggers?.critical_threshold ?? 'No critical threshold defined.'}
                  </p>
                </div>
                <div className="border border-sky-500/30 bg-sky-500/5 rounded-md p-3">
                  <p className="text-[11px] font-bold uppercase tracking-wide text-sky-400 mb-1">
                    Fallback Protocol
                  </p>
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    {escalation_triggers?.fallback_protocol ?? 'No fallback protocol defined.'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Tab3;
