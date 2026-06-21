/**
 * ResultsDisplay — Carbon calculation results with comparisons and chart.
 *
 * Accessibility features:
 *   - <section aria-labelledby="results-heading">
 *   - aria-live="polite" so screen readers announce new results
 *   - Progress bars have aria-label with percentage and comparison target
 *   - "Get Personalized Insights" button triggers AI insights flow
 */

import { useCarbonStore } from '../../store/carbonStore';
import type { CarbonResult } from '../../types';
import { formatKg, getFootprintLabel } from '../../utils/formatters';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { CategoryChart } from './CategoryChart';

interface ResultsDisplayProps {
  result: CarbonResult;
}

const ComparisonBar = ({
  id,
  label,
  pct,
  benchmark,
  benchmarkKg,
}: {
  id: string;
  label: string;
  pct: number;
  benchmark: string;
  benchmarkKg: number;
}) => {
  const clampedPct = Math.min(pct, 200);
  const barWidth = Math.min(clampedPct / 2, 100); // 200% maps to full bar width
  const color = pct <= 100 ? 'bg-primary-500' : pct <= 150 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm">
        <span className="font-medium text-slate-300">{label}</span>
        <span className="font-bold text-slate-50 tabular-nums">
          {pct.toFixed(0)}%{' '}
          <span className="font-normal text-slate-500">of {formatKg(benchmarkKg)}</span>
        </span>
      </div>
      <div
        className="relative w-full h-2 bg-slate-800 rounded-full overflow-hidden shadow-inner"
        role="progressbar"
        aria-valuenow={Math.round(pct)}
        aria-valuemin={0}
        aria-valuemax={200}
        aria-label={`${label}: your footprint is ${pct.toFixed(0)}% of the ${benchmark} (${formatKg(benchmarkKg)}/year)`}
        id={id}
      >
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${barWidth}%` }}
        />
        {/* 100% marker */}
        <div
          className="absolute top-0 h-full w-px bg-slate-400 opacity-60 shadow-[0_0_4px_rgba(255,255,255,0.5)]"
          style={{ left: '50%' }}
          aria-hidden="true"
        />
      </div>
      <p className="text-xs text-slate-400">
        {pct <= 100
          ? `✅ You are below the ${benchmark}`
          : `⚠️ You are ${(pct - 100).toFixed(0)}% above the ${benchmark}`}
      </p>
    </div>
  );
};

export const ResultsDisplay = ({ result }: ResultsDisplayProps) => {
  const fetchInsights = useCarbonStore(s => s.fetchInsights);
  const isLoadingInsights = useCarbonStore(s => s.isLoadingInsights);
  const insights = useCarbonStore(s => s.insights);

  const { label } = getFootprintLabel(result.vs_global_average_pct);

  return (
    <section
      aria-labelledby="results-heading"
      aria-live="polite"
      aria-atomic="true"
      className="space-y-4 animate-slide-up"
    >
      {/* Bento Grid Wrapper */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Total Footprint Hero */}
        <div className="vercel-card lg:col-span-3 p-10 text-center relative overflow-hidden flex flex-col items-center justify-center min-h-[280px]">
          {/* Subtle Inner Glow */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-primary-500/5 rounded-full blur-[80px] pointer-events-none" />
          
          <div className="relative z-10">
            <h2 id="results-heading" className="text-sm font-semibold text-slate-400 mb-4 tracking-[0.2em] uppercase">
              Your Annual Carbon Footprint
            </h2>
            <div className="flex flex-col items-center justify-center gap-1 mb-6">
              <span className="text-7xl sm:text-8xl font-black tabular-nums text-slate-50 tracking-tight">
                {formatKg(result.total_kg)}
              </span>
              <span className="text-lg font-medium text-slate-500 mt-2 tracking-widest uppercase">CO₂e</span>
            </div>
          </div>
          <span
            className={`inline-flex items-center px-4 py-1.5 rounded-md text-xs font-semibold uppercase tracking-wider ${
              result.vs_global_average_pct <= 100 
                ? 'bg-primary-500/10 text-primary-400 border border-primary-500/20'
                : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
            }`}
          >
            {label}
          </span>
        </div>

        {/* Benchmark Comparisons */}
        <div className="vercel-card p-6 sm:p-8 space-y-8 flex flex-col justify-center">
          <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2 tracking-wide uppercase">
            <span aria-hidden="true" className="text-slate-500">📊</span> Benchmarks
          </h3>
          <ComparisonBar
            id="global-average-bar"
            label="vs Global Average"
            pct={result.vs_global_average_pct}
            benchmark="global average"
            benchmarkKg={4000}
          />
          <ComparisonBar
            id="paris-target-bar"
            label="vs Paris 1.5°C Target"
            pct={result.vs_paris_target_pct}
            benchmark="Paris climate target"
            benchmarkKg={2000}
          />
          <p className="text-[10px] text-slate-500 pt-4 border-t border-slate-800/60 uppercase tracking-widest">
            Data: Our World in Data · IPCC SR1.5
          </p>
        </div>

        {/* Category Chart */}
        <div className="vercel-card lg:col-span-2 p-6 sm:p-8 flex flex-col">
          <h3 className="text-sm font-semibold text-slate-300 mb-6 flex items-center gap-2 tracking-wide uppercase">
            <span aria-hidden="true" className="text-slate-500">🔍</span> Breakdown by Category
          </h3>
          <div className="flex-1 min-h-[200px]">
            <CategoryChart breakdown={result.breakdown} ranked_categories={result.ranked_categories} />
          </div>
        </div>
      </div>

      {/* Get Insights CTA */}
      {!insights && (
        <div className="flex justify-center pt-4">
          <button
            onClick={fetchInsights}
            disabled={isLoadingInsights}
            aria-busy={isLoadingInsights}
            aria-label={
              isLoadingInsights
                ? 'Loading your personalised reduction plan...'
                : 'Get personalised carbon reduction insights powered by Google Gemini AI'
            }
            className="
              flex items-center gap-3 bg-primary-600 text-slate-50
              px-8 py-3 rounded-[10px] text-sm font-semibold tracking-wide
              hover:bg-primary-500 hover:shadow-[0_0_16px_rgba(16,185,129,0.3)] active:scale-95
              focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-slate-950
              disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none disabled:active:scale-100
              transition-all duration-200 border border-primary-500/30 min-w-[280px] justify-center
            "
          >
            {isLoadingInsights ? (
              <LoadingSpinner label="Running Inference..." size="sm" />
            ) : (
              <>
                <span aria-hidden="true" className="text-primary-300">⚡</span>
                Generate AI Insights
                <span className="text-[10px] bg-slate-900/50 border border-slate-700/50 px-2 py-0.5 rounded-md text-primary-200">Gemini</span>
              </>
            )}
          </button>
        </div>
      )}
    </section>
  );
};
