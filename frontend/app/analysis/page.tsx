"use client";

import { useState } from "react";
import { ShieldAlert, Crosshair, Radar, Target, Wifi, Activity, Share, Plane } from "lucide-react";
import TimeSeriesChart from "../../components/TimeSeriesChart";

const MOCK_ANALYSIS_DATA = {
  totalAlerts: 145,
  totalInterceptions: 120,
  lostObjects: 25,
  avgDuration: "45 mins",
  threatDemographics: [
    { type: "Shahed-136", count: 85, intercepted: 78, color: "bg-emerald-500" },
    { type: "Kh-101 (Cruise)", count: 40, intercepted: 35, color: "bg-blue-500" },
    { type: "Kinzhal", count: 20, intercepted: 7, color: "bg-rose-500" },
  ],
};

export default function AnalysisPage() {
  const [toggles, setToggles] = useState({
    active: true,
    alerts: true,
    radar: false,
    network: true
  });

  return (
    <div className="space-y-6 pt-16 md:pt-20 animate-in fade-in duration-500 max-w-6xl mx-auto">
      
      {/* iOS 26 Control Center Style Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
        
        {/* Square Toggle Buttons (Top-Left Corner Request) */}
        <div className="grid grid-cols-2 gap-3 col-span-2 sm:col-span-1 lg:col-span-1 h-[140px] md:h-auto">
          <button 
            onClick={() => setToggles({...toggles, active: !toggles.active})}
            className={`flex flex-col items-center justify-center gap-2 rounded-3xl transition-all duration-500 backdrop-blur-2xl shadow-[0_8px_32px_rgba(0,0,0,0.12)] border border-white/20 dark:border-white/10 ${
              toggles.active ? "bg-indigo-500 text-white" : "bg-white/40 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300"
            }`}
          >
            <Plane className="h-6 w-6" />
            <span className="text-xs font-semibold">Active</span>
          </button>
          
          <button 
            onClick={() => setToggles({...toggles, radar: !toggles.radar})}
            className={`flex flex-col items-center justify-center gap-2 rounded-3xl transition-all duration-500 backdrop-blur-2xl shadow-[0_8px_32px_rgba(0,0,0,0.12)] border border-white/20 dark:border-white/10 ${
              toggles.radar ? "bg-emerald-500 text-white" : "bg-white/40 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300"
            }`}
          >
            <Radar className="h-6 w-6" />
            <span className="text-xs font-semibold">Radar</span>
          </button>
          
          <button 
            onClick={() => setToggles({...toggles, network: !toggles.network})}
            className={`flex flex-col items-center justify-center gap-2 rounded-3xl transition-all duration-500 backdrop-blur-2xl shadow-[0_8px_32px_rgba(0,0,0,0.12)] border border-white/20 dark:border-white/10 ${
              toggles.network ? "bg-blue-500 text-white" : "bg-white/40 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300"
            }`}
          >
            <Wifi className="h-6 w-6" />
            <span className="text-xs font-semibold">Network</span>
          </button>
          
          <button 
            onClick={() => setToggles({...toggles, alerts: !toggles.alerts})}
            className={`flex flex-col items-center justify-center gap-2 rounded-3xl transition-all duration-500 backdrop-blur-2xl shadow-[0_8px_32px_rgba(0,0,0,0.12)] border border-white/20 dark:border-white/10 ${
              toggles.alerts ? "bg-rose-500 text-white" : "bg-white/40 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300"
            }`}
          >
            <ShieldAlert className="h-6 w-6" />
            <span className="text-xs font-semibold">Alerts</span>
          </button>
        </div>

        {/* Large Analytics Block */}
        <div className="col-span-2 md:col-span-3 lg:col-span-3 rounded-[2rem] border border-white/20 dark:border-white/10 bg-white/40 dark:bg-slate-900/40 p-6 shadow-[0_8px_32px_rgba(0,0,0,0.12)] backdrop-blur-2xl flex flex-col justify-center">
          <div className="flex items-center gap-3 mb-4">
            <Activity className="h-6 w-6 text-indigo-500 dark:text-emerald-400" />
            <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">Interception Overview</h2>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Total Targets</p>
              <p className="text-3xl font-bold text-slate-800 dark:text-slate-100">{MOCK_ANALYSIS_DATA.totalAlerts}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Shot Down</p>
              <p className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">{MOCK_ANALYSIS_DATA.totalInterceptions}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Lost / Impact</p>
              <p className="text-3xl font-bold text-rose-600 dark:text-rose-400">{MOCK_ANALYSIS_DATA.lostObjects}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Avg Duration</p>
              <p className="text-3xl font-bold text-slate-800 dark:text-slate-100">{MOCK_ANALYSIS_DATA.avgDuration}</p>
            </div>
          </div>
        </div>

        {/* Quick Share / Action Block */}
        <div className="hidden lg:flex flex-col col-span-1 rounded-[2rem] border border-white/20 dark:border-white/10 bg-white/40 dark:bg-slate-900/40 p-4 shadow-[0_8px_32px_rgba(0,0,0,0.12)] backdrop-blur-2xl items-center justify-center hover:bg-white/60 dark:hover:bg-slate-800/60 cursor-pointer transition">
          <Share className="h-8 w-8 text-indigo-500 dark:text-indigo-400 mb-2" />
          <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">Share Report</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Threat Demographics Progress Stack */}
        <div className="col-span-1 rounded-[2rem] border border-white/20 dark:border-white/10 bg-white/40 dark:bg-slate-900/40 p-6 shadow-[0_8px_32px_rgba(0,0,0,0.12)] backdrop-blur-2xl">
          <h2 className="mb-6 text-lg font-bold text-slate-800 dark:text-slate-100">Demographics</h2>
          <div className="space-y-6">
            {MOCK_ANALYSIS_DATA.threatDemographics.map((threat) => {
              const interceptRate = Math.round((threat.intercepted / threat.count) * 100);
              return (
                <div key={threat.type}>
                  <div className="mb-2 flex justify-between text-sm">
                    <span className="font-semibold text-slate-700 dark:text-slate-200">{threat.type}</span>
                    <span className="text-slate-500">{threat.intercepted} / {threat.count} ({interceptRate}%)</span>
                  </div>
                  <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800 shadow-inner">
                    <div 
                      className={`h-full ${threat.color} transition-all duration-1000 shadow-lg`} 
                      style={{ width: `${interceptRate}%` }} 
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* TimeSeries Chart Wide Block */}
        <div className="col-span-1 lg:col-span-2 rounded-[2rem] border border-white/20 dark:border-white/10 bg-white/40 dark:bg-slate-900/40 p-6 shadow-[0_8px_32px_rgba(0,0,0,0.12)] backdrop-blur-2xl overflow-hidden relative">
          <div className="absolute inset-0 z-0">
             <TimeSeriesChart />
          </div>
          <div className="relative z-10 pointer-events-none">
            {/* Overlay any info if necessary, TimeSeries chart handles itself */}
          </div>
        </div>
      </div>
    </div>
  );
}
