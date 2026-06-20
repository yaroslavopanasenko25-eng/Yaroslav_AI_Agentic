"use client";

import { useEffect, useState } from "react";

const REGIONS = [
  // Simplified stylized polygonal bounds representing zones (mocked paths for visual aesthetics)
  { id: "west", name: "Western Regions", d: "M 100 250 L 250 150 L 300 250 L 250 400 L 100 350 Z", alert: false },
  { id: "north", name: "Northern Regions", d: "M 300 250 L 250 150 L 450 100 L 550 200 L 450 300 Z", alert: true },
  { id: "center", name: "Central Regions", d: "M 300 250 L 450 300 L 450 450 L 250 400 Z", alert: false },
  { id: "south", name: "Southern Regions", d: "M 250 400 L 450 450 L 550 600 L 350 600 Z", alert: true },
  { id: "east", name: "Eastern Regions", d: "M 450 300 L 550 200 L 700 250 L 650 450 L 450 450 Z", alert: true },
  { id: "crimea", name: "Crimea", d: "M 450 600 L 550 600 L 600 700 L 500 700 Z", alert: true },
];

export default function LiveMap(): JSX.Element {
  const [mounted, setMounted] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    setMounted(true);
    const timer = setInterval(() => setCurrentTime(new Date()), 60000); // update every minute
    return () => clearInterval(timer);
  }, []);

  if (!mounted) return <div className="h-full w-full bg-slate-950" />;

  return (
    <div className="relative h-full w-full bg-[#111827] dark:bg-[#0B0F19] flex items-center justify-center overflow-hidden">
      {/* Background grid for tactical feel */}
      <div className="absolute inset-0 z-0 bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:40px_40px] opacity-20 pointer-events-none" />

      {/* Timestamp HUD */}
      <div className="absolute left-8 bottom-8 z-10 pointer-events-none">
        <p className="text-sm text-slate-400 font-mono tracking-widest uppercase">Live Alert System</p>
        <p className="text-2xl font-semibold text-white mt-1">
          {currentTime.toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>

      {/* Stylized Ukraine Map SVG */}
      <div className="relative z-10 w-full max-w-[1200px] aspect-[4/3] drop-shadow-[0_0_30px_rgba(0,0,0,0.5)]">
        <svg viewBox="0 0 800 800" className="w-full h-full preserve-3d">
          <defs>
            <filter id="glow-red">
              <feGaussianBlur stdDeviation="8" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            <filter id="shadow">
              <feDropShadow dx="0" dy="10" stdDeviation="5" floodColor="#000" floodOpacity="0.5"/>
            </filter>
          </defs>
          
          <g transform="translate(0, 50)" filter="url(#shadow)">
            {REGIONS.map((region) => (
              <g key={region.id} className="group transition-all duration-500 hover:scale-[1.01] origin-center cursor-pointer">
                {/* 3D Base */}
                <path 
                  d={region.d} 
                  className={`transition-colors duration-1000 ${
                    region.alert ? "fill-rose-950" : "fill-slate-800"
                  }`}
                  transform="translate(0, 10)"
                />
                {/* Top Surface */}
                <path 
                  d={region.d} 
                  className={`transition-all duration-1000 stroke-2 ${
                    region.alert 
                      ? "fill-rose-600/90 stroke-rose-400 hover:fill-rose-500" 
                      : "fill-slate-700 stroke-slate-500 hover:fill-slate-600"
                  }`}
                  style={region.alert ? { filter: "url(#glow-red)" } : {}}
                />
                
                {/* Region Label */}
                {/* Calculate rough center for label placement based on d bounds */}
                {region.id === "center" && (
                  <text x="350" y="350" className="fill-white font-semibold text-xs tracking-wider opacity-80 pointer-events-none">CENTRAL</text>
                )}
                {region.id === "west" && (
                  <text x="200" y="260" className="fill-white font-semibold text-xs tracking-wider opacity-80 pointer-events-none">WEST</text>
                )}
                {region.id === "east" && (
                  <text x="550" y="320" className="fill-white font-semibold text-xs tracking-wider opacity-90 pointer-events-none">EAST / FRONTLINE</text>
                )}
                
                {region.alert && (
                  <circle cx={region.id === "east" ? "530" : region.id === "south" ? "420" : region.id === "north" ? "380" : "550"} 
                          cy={region.id === "east" ? "315" : region.id === "south" ? "500" : region.id === "north" ? "180" : "650"} 
                          r="6" 
                          className="fill-yellow-400 animate-pulse pointer-events-none" />
                )}
              </g>
            ))}
          </g>
        </svg>
      </div>
    </div>
  );
}
