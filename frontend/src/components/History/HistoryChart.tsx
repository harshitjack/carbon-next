/**
 * HistoryChart — Line chart showing carbon footprint trend over time.
 *
 * Accessibility features:
 *   - role="img" with aria-label on chart wrapper
 *   - Accessible data table below (sr-only)
 *   - Empty state with role="status"
 *   - Up/down arrows with aria-label for trend indicators in table
 */

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { HistoryEntry } from '../../types';
import { formatDate, formatKg } from '../../utils/formatters';

interface HistoryChartProps {
  history: HistoryEntry[];
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-[8px] px-3 py-2 shadow-xl text-sm">
      <p className="text-slate-400 text-[10px] uppercase tracking-wider mb-1">{label}</p>
      <p className="font-bold text-slate-100 tabular-nums tracking-wide">{formatKg(payload[0].value)} CO₂e</p>
    </div>
  );
};

export const HistoryChart = ({ history }: HistoryChartProps) => {
  if (history.length === 0) {
    return (
      <div className="vercel-card p-10 text-center flex flex-col justify-center min-h-[300px]">
        <div className="text-5xl mb-4 opacity-50" aria-hidden="true">
          📊
        </div>
        <p role="status" className="text-slate-400">
          No telemetry data found. Run a calculation to generate your baseline.
        </p>
      </div>
    );
  }

  // Display oldest → newest for the trend line
  const chartData = [...history].reverse().map(entry => ({
    date: formatDate(entry.timestamp),
    kg: entry.total_kg,
  }));

  return (
    <div className="vercel-card p-6 sm:p-8 space-y-6">
      <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2 tracking-wide uppercase">
        <span aria-hidden="true" className="text-slate-500">📈</span> Footprint Trend
      </h3>

      {/* Recharts line chart */}
      <div
        role="img"
        aria-label="Line chart showing carbon footprint trend over time. A data table with the same information follows."
        className="w-full h-56"
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
            aria-hidden="true"
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#64748b' }}
              axisLine={{ stroke: '#e2e8f0' }}
              tickLine={false}
              dy={10}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#64748b', fontFamily: 'monospace' }}
              axisLine={{ stroke: '#e2e8f0' }}
              tickLine={false}
              tickFormatter={(v: number) => formatKg(v)}
              width={52}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#cbd5e1', strokeWidth: 1, strokeDasharray: '4 4' }} />
            <Line
              type="monotone"
              dataKey="kg"
              stroke="#10b981"
              strokeWidth={2}
              dot={{ fill: '#ffffff', stroke: '#10b981', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, fill: '#10b981', stroke: '#ffffff', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Screen reader accessible data table */}
      <table className="sr-only">
        <caption>Carbon footprint history — date and total CO₂e emissions</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Total CO₂e (kg)</th>
            <th scope="col">Change vs previous</th>
          </tr>
        </thead>
        <tbody>
          {chartData.map((entry, i) => {
            const prev = chartData[i - 1];
            const diff = prev ? entry.kg - prev.kg : null;
            const trendLabel =
              diff === null
                ? 'First entry'
                : diff > 0
                  ? `Up ${formatKg(Math.abs(diff))}`
                  : diff < 0
                    ? `Down ${formatKg(Math.abs(diff))}`
                    : 'No change';
            return (
              <tr key={i}>
                <th scope="row">{entry.date}</th>
                <td>{Math.round(entry.kg)}</td>
                <td>{trendLabel}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
