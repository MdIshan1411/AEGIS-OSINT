import { AuditRecord } from "../types/api";
import { ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Line } from "recharts";

interface TrendChartProps {
  audits: AuditRecord[];
}

export function TrendChart({ audits }: TrendChartProps) {
  const data = audits.map((audit) => ({
    date: new Date(audit.created_at || audit.started_at).toLocaleDateString(),
    critical: audit.summary_json.critical || 0,
    high: audit.summary_json.high || 0,
    medium: audit.summary_json.medium || 0,
    low: audit.summary_json.low || 0,
    total:
      (audit.summary_json.critical || 0) +
      (audit.summary_json.high || 0) +
      (audit.summary_json.medium || 0) +
      (audit.summary_json.low || 0),
  })).reverse(); // Reverse to show oldest first on the left

  return (
    <div className="bg-slate-800 rounded border border-slate-700 p-6 shadow-xl">
      <h3 className="text-lg font-semibold text-white mb-4">Vulnerability Trends</h3>
      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
            <XAxis dataKey="date" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Legend />
            <Line type="monotone" dataKey="critical" stroke="#ef4444" strokeWidth={2} />
            <Line type="monotone" dataKey="high" stroke="#f59e0b" strokeWidth={2} />
            <Line type="monotone" dataKey="medium" stroke="#eab308" strokeWidth={2} />
            <Line type="monotone" dataKey="low" stroke="#3b82f6" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
