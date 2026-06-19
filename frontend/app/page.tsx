/**
 * Main dashboard page for GuardianEye.
 * Renders live map, time series visualization, and operator settings panel.
 */
import { ShieldAlert } from "lucide-react";

import LiveMap from "../components/LiveMap";
import Settings from "../components/Settings";
import TimeSeriesChart from "../components/TimeSeriesChart";

export default function DashboardPage(): JSX.Element {
  try {
    return (
      <div className="space-y-8">
        <header className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-lg shadow-black/30 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="flex items-center gap-3 text-2xl font-semibold text-slate-100 md:text-3xl">
              <ShieldAlert className="h-8 w-8 text-emerald-400" aria-hidden="true" />
              GuardianEye
            </h1>
            <p className="mt-2 text-sm text-slate-300 md:text-base">
              Ukraine Air Raid Defense Analytics — operational trends, forecasting, and decision support.
            </p>
          </div>
        </header>

        <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <LiveMap />
          </div>
          <div>
            <Settings />
          </div>
        </section>

        <section>
          <TimeSeriesChart />
        </section>
      </div>
    );
  } catch (error) {
    console.error("Dashboard rendering failed", error);
    return (
      <div className="rounded-2xl border border-rose-700/50 bg-rose-900/20 p-6 text-rose-200">
        GuardianEye dashboard failed to render. Please refresh or contact support.
      </div>
    );
  }
}
