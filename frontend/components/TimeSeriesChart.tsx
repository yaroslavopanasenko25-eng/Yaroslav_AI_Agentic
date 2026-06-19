"use client";

/**
 * Time series chart for alert frequency peaks over days and weeks.
 * Uses Recharts and includes defensive fallback rendering on failure.
 */
import { useMemo } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type AlertFrequencyPoint = {
  period: string;
  alerts: number;
};

const SAMPLE_SERIES: AlertFrequencyPoint[] = [
  { period: "Mon", alerts: 12 },
  { period: "Tue", alerts: 18 },
  { period: "Wed", alerts: 10 },
  { period: "Thu", alerts: 22 },
  { period: "Fri", alerts: 15 },
  { period: "Sat", alerts: 9 },
  { period: "Sun", alerts: 14 },
];

export default function TimeSeriesChart(): JSX.Element {
  const chartData: AlertFrequencyPoint[] = useMemo(() => {
    try {
      return SAMPLE_SERIES;
    } catch (error) {
      console.error("Failed to prepare chart data", error);
      return [];
    }
  }, []);

  try {
    return (
      <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-md shadow-black/30">
        <h2 className="text-xl font-semibold text-slate-100">Alert Frequency Trends</h2>
        <p className="mt-3 text-sm text-slate-300">
          Daily and weekly frequency profile for rapid identification of escalation windows.
        </p>

        <div className="mt-6 h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 12, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="period" stroke="#cbd5e1" />
              <YAxis stroke="#cbd5e1" />
              <Tooltip
                contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #334155" }}
                labelStyle={{ color: "#e2e8f0" }}
              />
              <Line type="monotone" dataKey="alerts" stroke="#34d399" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </article>
    );
  } catch (error) {
    console.error("TimeSeriesChart rendering failed", error);
    return (
      <article className="rounded-2xl border border-rose-700/50 bg-rose-900/20 p-6 text-rose-200">
        Time series visualization is temporarily unavailable.
      </article>
    );
  }
}
