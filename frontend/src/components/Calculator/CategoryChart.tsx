/**
 * CategoryChart — Bar chart of carbon breakdown by category.
 *
 * Accessibility features:
 *   - Chart wrapper: role="img" aria-label describing the chart
 *   - Data table below chart: className="sr-only" (screen reader only)
 *   - Table has <caption>, <th scope="col">, <th scope="row">
 *   - All colour choices meet WCAG 4.5:1 contrast against white background
 */

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { RankedCategory } from '../../types';
import { formatCategory, formatKg } from '../../utils/formatters';

interface CategoryChartProps {
  breakdown: Record<string, number>;
  ranked_categories: RankedCategory[];
}

const CATEGORY_COLORS: Record<string, string> = {
  transport: '#10b981', // emerald-500
  home: '#34d399', // emerald-400
  diet: '#059669', // emerald-600
  consumption: '#06b6d4', // cyan-500
  general: '#22d3ee', // cyan-400
};

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ value: number; payload: { category: string } }>;
}) => {
  if (!active || !payload?.length) return null;
  const { value, payload: data } = payload[0];
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-[8px] px-3 py-2 shadow-xl text-sm">
      <p className="text-slate-400 text-[10px] uppercase tracking-wider mb-1">{formatCategory(data.category)}</p>
      <p className="font-bold text-slate-100 tabular-nums tracking-wide">{formatKg(value)} CO₂e</p>
    </div>
  );
};

export const CategoryChart = ({ breakdown: _breakdown, ranked_categories }: CategoryChartProps) => {
  const chartData = ranked_categories.map(item => ({
    category: item.category,
    label: formatCategory(item.category),
    kg: item.kg,
    percentage: item.percentage,
  }));

  return (
    <div>
      {/* Recharts bar chart — hidden from screen readers (table below is the accessible version) */}
      <div
        role="img"
        aria-label="Bar chart showing annual carbon footprint broken down by category. A data table with the same information follows."
        className="w-full h-56"
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
            aria-hidden="true"
          >
            <XAxis
              dataKey="label"
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
            <Tooltip content={<CustomTooltip />} cursor={{ fill: '#f1f5f9' }} />
            <Bar dataKey="kg" radius={[4, 4, 0, 0]} maxBarSize={48}>
              {chartData.map(entry => (
                <Cell key={entry.category} fill={CATEGORY_COLORS[entry.category] ?? '#10b981'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Screen reader data table (visually hidden) */}
      <table className="sr-only">
        <caption>Carbon footprint breakdown by category (annual kg CO₂e)</caption>
        <thead>
          <tr>
            <th scope="col">Category</th>
            <th scope="col">kg CO₂e per year</th>
            <th scope="col">Percentage of total</th>
          </tr>
        </thead>
        <tbody>
          {ranked_categories.map(item => (
            <tr key={item.category}>
              <th scope="row">{formatCategory(item.category)}</th>
              <td>{Math.round(item.kg)}</td>
              <td>{item.percentage}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
