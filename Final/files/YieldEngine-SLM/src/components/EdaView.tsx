import React, { useEffect, useState } from 'react';
import { EdaStats } from '../types';
import { api } from '../services/api';

const ChartCard: React.FC<{ title: string; caption: string; children: React.ReactNode }> = ({
  title, caption, children,
}) => (
  <div className="card-container">
    <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">
      {title}
    </h3>
    {children}
    <p className="font-body-sm text-[11px] text-on-surface-variant mt-4 pt-3 border-t border-outline-variant/50">
      {caption}
    </p>
  </div>
);

export const EdaView: React.FC = () => {
  const [stats, setStats] = useState<EdaStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getEdaStats().then(setStats).catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="card-container border-l-4 border-l-error bg-error/5">
        <p className="font-body-sm text-body-sm text-error">Could not load EDA statistics: {error}</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="card-container text-center py-16">
        <span className="font-body-sm text-body-sm text-on-surface-variant">Loading real dataset statistics…</span>
      </div>
    );
  }

  const maxRecordCount = Math.max(...stats.crop_production_by_state_chart.map((s) => s.record_count));
  const maxYieldHistCount = Math.max(...stats.yield_histogram.map((b) => b.count));
  const maxRainfallHistCount = Math.max(...stats.rainfall_histogram.map((b) => b.count));
  const maxAbsCorr = Math.max(...stats.yield_correlations.map((c) => Math.abs(c.correlation)));

  return (
    <div className="space-y-stack-loose">
      <div className="section-header">
        <h2 className="font-headline-md text-headline-md text-primary dark:text-primary-fixed mb-1">
          Exploratory Data Analysis
        </h2>
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          Understanding crop, soil, weather and agricultural input patterns before modeling. Computed from the actual
          cleaned dataset ({stats.n_rows.toLocaleString()} records, {stats.n_crops} crops, {stats.n_states} states) —
          not placeholder figures.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gutter md:gap-stack-loose">
        <ChartCard
          title="Data Coverage Among States"
          caption={`Top 3 states account for ${stats.top3_states_pct_of_total.toFixed(1)}% of all records. Shown as record count, not production volume — this dataset's Production column uses different units for different crops (e.g. Coconut is counted in nuts, not tonnes), so a cross-crop volume total would be misleading.`}
        >
          <div className="space-y-3">
            {stats.crop_production_by_state_chart.map((s) => (
              <div key={s.state}>
                <div className="flex justify-between font-data-mono text-data-mono text-xs mb-1">
                  <span>{s.state}</span>
                  <span className="text-on-surface-variant">{s.record_count.toLocaleString()}</span>
                </div>
                <div className="shap-bar w-full">
                  <div
                    className="shap-bar-positive"
                    style={{ width: `${(s.record_count / maxRecordCount) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard
          title="Top 10 States by Record Count"
          caption="Concentration of data collection is skewed toward a handful of major agricultural states."
        >
          <table className="w-full text-left font-data-mono text-xs">
            <thead>
              <tr className="border-b border-outline-variant text-on-surface-variant uppercase tracking-wider">
                <th className="py-2">State</th>
                <th className="py-2 text-right">Records</th>
                <th className="py-2 text-right">% of Total</th>
              </tr>
            </thead>
            <tbody>
              {stats.top_producing_states.map((s) => (
                <tr key={s.state} className="border-b border-outline-variant/40">
                  <td className="py-2">{s.state}</td>
                  <td className="py-2 text-right">{s.record_count.toLocaleString()}</td>
                  <td className="py-2 text-right">{s.pct_of_total.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </ChartCard>

        <ChartCard
          title={`Area vs Production — ${stats.area_production_scatter_crop} only`}
          caption={`Restricted to a single crop (${stats.area_production_scatter_crop}) so units are consistent — plotting all crops together would mix incompatible Production units on one axis. Pearson correlation for ${stats.area_production_scatter_crop}: r = ${stats.area_production_scatter_correlation.toFixed(3)} (strong positive relationship, as expected: more land, more production, within the same crop).`}
        >
          <div className="h-56 bg-surface-container-lowest border border-outline-variant p-4 relative">
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full">
              {stats.area_production_scatter_sample.map((p, i) => {
                const maxArea = Math.max(...stats.area_production_scatter_sample.map((d) => d.area));
                const maxProd = Math.max(...stats.area_production_scatter_sample.map((d) => d.production));
                const x = (p.area / maxArea) * 96 + 2;
                const y = 98 - (p.production / maxProd) * 96;
                return <circle key={i} cx={x} cy={y} r={0.8} fill="var(--color-primary)" opacity={0.6} />;
              })}
            </svg>
          </div>
        </ChartCard>

        <ChartCard
          title="Yield Correlation Summary"
          caption="Pearson correlation with Yield, pooled across all crops. Correlations here are weak by design — the same cross-crop unit heterogeneity documented in the model evaluation report weakens pooled linear correlation, even though per-crop model accuracy is strong (see Dataset page)."
        >
          <div className="space-y-3">
            {stats.yield_correlations.map((c) => (
              <div key={c.feature}>
                <div className="flex justify-between font-data-mono text-data-mono text-xs mb-1">
                  <span>{c.feature.replace(/_/g, ' ')}</span>
                  <span className={c.correlation >= 0 ? 'text-primary dark:text-primary-fixed' : 'text-error'}>
                    {c.correlation >= 0 ? '+' : ''}{c.correlation.toFixed(3)}
                  </span>
                </div>
                <div className={`w-full h-[8px] bg-surface-container flex ${c.correlation < 0 ? 'justify-end' : ''}`}>
                  <div
                    className={c.correlation >= 0 ? 'h-[8px] bg-primary dark:bg-primary-container' : 'h-[8px] bg-error'}
                    style={{ width: `${maxAbsCorr > 0 ? (Math.abs(c.correlation) / maxAbsCorr) * 100 : 0}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard
          title="Yield Distribution (post-cleaning, 99th percentile capped for readability)"
          caption="Heavily right-skewed even after removing demonstrable data errors — consistent with real agricultural yield distributions, where most fields cluster at modest yields with a long tail of higher-yield crops/conditions."
        >
          <div className="flex items-end h-40 gap-1">
            {stats.yield_histogram.map((bin, idx) => (
              <div
                key={idx}
                className="flex-1 bg-primary dark:bg-primary-container"
                style={{ height: `${(bin.count / maxYieldHistCount) * 100}%` }}
                title={`${bin.bin_start.toFixed(1)}–${bin.bin_end.toFixed(1)} t/ha: ${bin.count.toLocaleString()} records`}
              />
            ))}
          </div>
        </ChartCard>

        <ChartCard
          title="Annual Rainfall Distribution"
          caption="Distribution of the Annual_Rainfall feature across all records — used to sanity-check the climate feature's spread before modeling."
        >
          <div className="flex items-end h-40 gap-1">
            {stats.rainfall_histogram.map((bin, idx) => (
              <div
                key={idx}
                className="flex-1 bg-primary dark:bg-primary-container"
                style={{ height: `${(bin.count / maxRainfallHistCount) * 100}%` }}
                title={`${bin.bin_start.toFixed(0)}–${bin.bin_end.toFixed(0)} mm: ${bin.count.toLocaleString()} records`}
              />
            ))}
          </div>
        </ChartCard>
      </div>
    </div>
  );
};
