const safeJsonParse = (value, fallback) => {
  if (value == null) return fallback;
  if (typeof value !== 'string') return value;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
};

const formatNumber = (value, opts = {}) => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (typeof num !== 'number' || Number.isNaN(num)) return 'N/A';
  return num.toLocaleString('en-US', opts);
};

const formatFeatureKey = (key) =>
  key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

const DrawdownTable = ({ rows, accent }) => {
  if (!rows?.length) {
    return <p className="text-sm text-zinc-500">No trajectory data available.</p>;
  }

  return (
    <div className="max-h-72 overflow-y-auto rounded-md border border-zinc-800">
      <table className="w-full text-xs font-mono border-collapse">
        <thead className="sticky top-0 bg-zinc-950 z-10">
          <tr className="text-zinc-500 uppercase tracking-widest">
            <th className="text-left font-semibold px-3 py-2 border-b border-zinc-800">Day</th>
            <th className="text-right font-semibold px-3 py-2 border-b border-zinc-800">Release (BPD)</th>
            <th className="text-right font-semibold px-3 py-2 border-b border-zinc-800">Reserves Remaining</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr
              key={row?.day ?? idx}
              className="odd:bg-zinc-900/40 even:bg-zinc-900/10 hover:bg-zinc-800/60"
            >
              <td className="px-3 py-1.5 text-zinc-400 border-b border-zinc-900">{row?.day ?? idx + 1}</td>
              <td className={`px-3 py-1.5 text-right font-bold border-b border-zinc-900 ${accent}`}>
                {formatNumber(row?.release_bpd)}
              </td>
              <td className="px-3 py-1.5 text-right text-zinc-300 border-b border-zinc-900">
                {formatNumber(row?.reserves_remaining)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const Tab4 = ({ data }) => {
  if (!data) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-zinc-950 text-zinc-500 text-sm uppercase tracking-widest">
        Waiting for SPR Optimization Analysis...
      </div>
    );
  }

  const {
    policy_directive_prose,
    optimal_drawdown_rate_bpd,
    runway_extension_days,
    confidence_variance_std,
    daily_drawdown_curve_json,
    sensitivity_shock_curve_json,
    extracted_features_json,
  } = data;

  const drawdownCurve = safeJsonParse(daily_drawdown_curve_json, []);
  const shockCurve = safeJsonParse(sensitivity_shock_curve_json, []);
  const featureMatrix = safeJsonParse(extracted_features_json, {});
  const featureEntries = featureMatrix && typeof featureMatrix === 'object'
    ? Object.entries(featureMatrix)
    : [];

  return (
    <div className="w-full h-full bg-zinc-950 text-zinc-200 p-4 md:p-6 flex flex-col gap-5 overflow-y-auto">
      {/* Top Strategic Banner */}
      <section className="w-full border border-blue-500/40 bg-gradient-to-r from-blue-500/10 via-zinc-900 to-zinc-900 rounded-lg p-5 shadow-[0_0_25px_-5px_rgba(59,130,246,0.35)]">
        <p className="text-2xl md:text-3xl font-extrabold uppercase tracking-wide text-blue-400 mb-2">
          Tab 4 &middot; Strategic Petroleum Reserve Optimization
        </p>
        <p className="text-sm leading-relaxed text-zinc-300/90 max-w-4xl whitespace-pre-line">
          {policy_directive_prose ?? 'No policy directive available.'}
        </p>
      </section>

      {/* KPI Strip */}
      <section className="w-full grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="border-l-4 border-blue-500 bg-zinc-900 rounded-md p-4">
          <p className="text-[11px] font-semibold uppercase tracking-widest text-zinc-500 mb-1">
            Optimal Drawdown Rate
          </p>
          <p className="text-2xl font-extrabold text-blue-400 tracking-tight">
            {formatNumber(optimal_drawdown_rate_bpd)}{' '}
            <span className="text-sm font-bold text-blue-400/70">BPD</span>
          </p>
        </div>

        <div className="border-l-4 border-emerald-500 bg-zinc-900 rounded-md p-4">
          <p className="text-[11px] font-semibold uppercase tracking-widest text-zinc-500 mb-1">
            Runway Extension
          </p>
          <p className="text-2xl font-extrabold text-emerald-400 tracking-tight">
            {formatNumber(runway_extension_days, { maximumFractionDigits: 1 })}{' '}
            <span className="text-sm font-bold text-emerald-400/70">Days</span>
          </p>
        </div>

        <div className="border-l-4 border-red-500 bg-zinc-900 rounded-md p-4">
          <p className="text-[11px] font-semibold uppercase tracking-widest text-zinc-500 mb-1">
            Confidence Variance
          </p>
          <p className="text-2xl font-extrabold text-red-400 tracking-tight">
            {formatNumber(confidence_variance_std, { maximumFractionDigits: 2, minimumFractionDigits: 2 })}{' '}
            <span className="text-sm font-bold text-red-400/70">BPD &sigma;</span>
          </p>
        </div>
      </section>

      {/* 3-Panel Analytical Grid */}
      <section className="w-full grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Panel A: Baseline Drawdown Trajectory */}
        <div className="border-l-4 border-blue-500 bg-zinc-900 rounded-md p-4">
          <h3 className="text-xs font-bold uppercase tracking-widest text-blue-400 mb-4">
            Baseline Drawdown Trajectory
          </h3>
          <DrawdownTable rows={drawdownCurve} accent="text-blue-400" />
        </div>

        {/* Panel B: +5 Day Shock Scenario */}
        <div className="border-l-4 border-amber-500 bg-zinc-900 rounded-md p-4">
          <h3 className="text-xs font-bold uppercase tracking-widest text-amber-400 mb-4">
            +5 Day Shock Scenario
          </h3>
          <DrawdownTable rows={shockCurve} accent="text-amber-400" />
        </div>

        {/* Panel C: 20D Neuro-Symbolic Feature Matrix */}
        <div className="border-l-4 border-purple-500 bg-zinc-900 rounded-md p-4 lg:col-span-2">
          <h3 className="text-xs font-bold uppercase tracking-widest text-purple-400 mb-4">
            20D Neuro-Symbolic Feature Matrix
          </h3>
          {featureEntries.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-3">
              {featureEntries.map(([key, value]) => (
                <div
                  key={key}
                  className="border border-zinc-800 bg-zinc-950/60 rounded-md p-3"
                >
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500 mb-1 truncate">
                    {formatFeatureKey(key)}
                  </p>
                  <p className="text-sm font-bold text-purple-300 tracking-tight">
                    {typeof value === 'number'
                      ? formatNumber(value, { maximumFractionDigits: 2 })
                      : String(value)}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-zinc-500">No feature vector data available.</p>
          )}
        </div>
      </section>
    </div>
  );
};

export default Tab4;
