/**
 * InsightCard — Single carbon reduction action card.
 *
 * Accessibility features:
 *   - <article> with descriptive aria-label
 *   - Priority badge is visually prominent and screen-reader legible
 *   - Category icon decorative (aria-hidden)
 */

import type { InsightItem } from '../../types';
import { formatKg, getCategoryIcon, formatCategory } from '../../utils/formatters';

interface InsightCardProps {
  insight: InsightItem;
  index: number;
}

const priorityColors = ['bg-primary-600', 'bg-primary-500', 'bg-primary-400'];

export const InsightCard = ({ insight, index }: InsightCardProps) => {
  const icon = getCategoryIcon(insight.category);
  const categoryLabel = formatCategory(insight.category);
  const saving = formatKg(insight.estimated_saving_kg);
  const badgeColor = priorityColors[index] ?? priorityColors[2];

  return (
    <article
      aria-label={`Insight ${index + 1}: ${categoryLabel} — ${insight.action}`}
      className="
        vercel-panel p-5 w-full flex flex-col h-full
        hover:shadow-vercel hover:-translate-y-0.5 hover:border-slate-700 transition-all duration-300
        animate-fade-in group
      "
    >
      <div className="flex items-start gap-4">
        {/* Priority Badge */}
        <div className="flex-shrink-0 flex flex-col items-center gap-1">
          <span
            className={`
              ${badgeColor} text-white text-[10px] font-black tracking-widest
              w-7 h-7 rounded-md flex items-center justify-center
              shadow-[0_0_8px_rgba(16,185,129,0.3)]
            `}
            aria-label={`Priority ${insight.priority}`}
          >
            {insight.priority}
          </span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Category header */}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl opacity-80" aria-hidden="true">
              {icon}
            </span>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.15em]">
              {categoryLabel}
            </span>
          </div>

          {/* Action text */}
          <p className="text-sm text-slate-200 leading-relaxed mb-4 flex-1">{insight.action}</p>

          {/* Metrics row */}
          <div className="flex flex-wrap items-center gap-2 mt-auto pt-4 border-t border-slate-800/50">
            {/* Saving */}
            <div className="flex items-center gap-1.5 bg-primary-500/10 border border-primary-500/20 text-primary-300 rounded-[6px] px-2.5 py-1">
              <span aria-hidden="true" className="text-[10px]">●</span>
              <span className="text-xs font-medium tracking-wide">~{saving} <span className="opacity-70">CO₂e</span></span>
            </div>

            {/* Timeframe */}
            <div className="flex items-center gap-1.5 bg-slate-800/50 border border-slate-700/50 text-slate-400 rounded-[6px] px-2.5 py-1">
              <span aria-hidden="true" className="text-[10px]">⏱</span>
              <span className="text-xs font-medium">{insight.timeframe}</span>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
};
