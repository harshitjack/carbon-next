/**
 * HistoryTable — Full accessible sortable table of carbon history entries.
 *
 * Accessibility features:
 *   - <table> with <caption>
 *   - <th scope="col"> for column headers
 *   - <th scope="row"> for date column
 *   - "View Details" button expands insights inline via aria-expanded
 *   - aria-controls links button to the expanded region
 */

import { Fragment, useState } from 'react';
import type { HistoryEntry } from '../../types';
import { formatCategory, formatDate, formatKg, getCategoryIcon } from '../../utils/formatters';

interface HistoryTableProps {
  history: HistoryEntry[];
}

const InsightExpandedRow = ({ entry, id }: { entry: HistoryEntry; id: string }) => (
  <div
    id={id}
    role="region"
    aria-label={`Insights for entry dated ${formatDate(entry.timestamp)}`}
    className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 mt-2 space-y-2"
  >
    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">
      Reduction Insights
    </p>
    {entry.insights.length === 0 ? (
      <p className="text-sm text-slate-500">No insights saved for this entry.</p>
    ) : (
      <ol className="space-y-3 list-none">
        {entry.insights.map((insight, i) => (
          <li key={i} className="flex items-start gap-3 text-sm text-slate-300">
            <span aria-hidden="true" className="opacity-80">{getCategoryIcon(insight.category)}</span>
            <span className="flex-1 leading-relaxed">{insight.action}</span>
            <span className="text-xs text-primary-400 font-medium whitespace-nowrap bg-primary-500/10 px-2 py-0.5 rounded-md border border-primary-500/20">
              ~{formatKg(insight.estimated_saving_kg)}/yr
            </span>
          </li>
        ))}
      </ol>
    )}
  </div>
);

export const HistoryTable = ({ history }: HistoryTableProps) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (history.length === 0) return null;

  const toggleExpand = (id: string) => {
    setExpandedId(prev => (prev === id ? null : id));
  };

  return (
    <div className="vercel-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <caption className="sr-only">
            Carbon footprint history entries, ordered newest first
          </caption>
          <thead>
            <tr className="bg-slate-900 border-b border-slate-800">
              <th
                scope="col"
                className="px-4 py-3 text-left text-[10px] font-bold text-slate-500 uppercase tracking-widest"
              >
                Date
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-right text-[10px] font-bold text-slate-500 uppercase tracking-widest"
              >
                Total CO₂e
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-[10px] font-bold text-slate-500 uppercase tracking-widest hidden sm:table-cell"
              >
                Top Category
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-center text-[10px] font-bold text-slate-500 uppercase tracking-widest"
              >
                Details
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50 bg-slate-900/20">
            {history.map(entry => {
              const topCategory =
                entry.ranked_categories?.[0]?.category ?? Object.keys(entry.breakdown)[0] ?? '—';
              const isExpanded = expandedId === entry.id;
              const expandId = `expand-${entry.id}`;

              return (
                <Fragment key={entry.id}>
                  <tr className="hover:bg-slate-800/30 transition-colors duration-150">
                    <th scope="row" className="px-4 py-3 font-medium text-slate-200 text-left tabular-nums">
                      {formatDate(entry.timestamp)}
                    </th>
                    <td className="px-4 py-3 text-right font-bold text-slate-50 tabular-nums">
                      {formatKg(entry.total_kg)}
                    </td>
                    <td className="px-4 py-3 hidden sm:table-cell">
                      <span className="inline-flex items-center gap-1.5 text-xs bg-slate-800/50 border border-slate-700/50 text-slate-300 px-2.5 py-1 rounded-md">
                        <span aria-hidden="true" className="opacity-80">{getCategoryIcon(topCategory)}</span>
                        {formatCategory(topCategory)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => toggleExpand(entry.id)}
                        aria-expanded={isExpanded}
                        aria-controls={expandId}
                        aria-label={`${isExpanded ? 'Collapse' : 'View'} insights for entry dated ${formatDate(entry.timestamp)}`}
                        className="
                          text-[10px] uppercase tracking-wider text-primary-400 font-bold
                          hover:text-primary-300 focus:outline-none
                          focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-slate-900 rounded px-2 py-1
                          transition-colors duration-150
                        "
                      >
                        {isExpanded ? '▲ Hide' : '▼ View'}
                      </button>
                    </td>
                  </tr>
                  {isExpanded && (
                    <tr>
                      <td colSpan={4} className="px-4 pb-4">
                        <InsightExpandedRow entry={entry} id={expandId} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
