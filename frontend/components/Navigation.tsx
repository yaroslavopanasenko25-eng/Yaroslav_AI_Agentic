"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Map, BarChart3, ShieldAlert } from "lucide-react";

export default function Navigation() {
  const pathname = usePathname();

  const navLinks = [
    { title: "Live Map", href: "/", icon: Map },
    { title: "Analysis", href: "/analysis", icon: BarChart3 }
  ];

  return (
    <nav className="fixed top-6 left-1/2 -translate-x-1/2 z-[100] rounded-full border border-white/20 dark:border-white/10 bg-white/40 dark:bg-slate-900/60 shadow-[0_8px_32px_rgba(0,0,0,0.12)] backdrop-blur-2xl px-2 py-2 w-auto animate-in fade-in slide-in-from-top-4 duration-700">
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2 px-4 pr-6 shrink-0">
          <ShieldAlert className="h-6 w-6 text-emerald-500" />
          <span className="font-bold text-slate-800 dark:text-slate-100 hidden sm:block">GuardianEye</span>
        </div>
        <div className="w-px h-6 bg-slate-300 dark:bg-slate-700" />
        {navLinks.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold transition-all duration-300 ${
                isActive 
                  ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-emerald-400 shadow-md scale-105" 
                  : "text-slate-600 hover:bg-white/50 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              <Icon className="h-4 w-4" />
              {link.title}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
