"use client";

import { useState } from "react";
import { Bot, Sparkles, X, Plus, Image as ImageIcon, Mic } from "lucide-react";

export default function AIAgentIcon() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed bottom-8 right-8 z-[150] flex flex-col items-end">
      {isOpen && (
        <div className="mb-6 w-[360px] rounded-[2.5rem] border border-white/20 dark:border-white/10 bg-white/40 dark:bg-[#1C1C1E]/60 p-5 shadow-[0_32px_64px_rgba(0,0,0,0.3)] backdrop-blur-[40px] animate-in slide-in-from-bottom-8 fade-in duration-500 origin-bottom-right">
          
          <div className="mb-4 flex items-center justify-between px-2">
            <h3 className="flex items-center gap-2 text-lg font-bold text-slate-800 dark:text-white">
              <div className="flex items-center justify-center h-8 w-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 text-white shadow-inner">
                <Sparkles className="h-4 w-4" />
              </div>
              Grok Intelligence
            </h3>
            <button onClick={() => setIsOpen(false)} className="flex h-8 w-8 items-center justify-center rounded-full bg-black/5 dark:bg-white/10 text-slate-600 dark:text-slate-300 hover:bg-black/10 dark:hover:bg-white/20 transition">
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="h-48 text-sm flex flex-col justify-end">
            <div className="space-y-3 mb-4">
              <div className="flex w-fit max-w-[85%] items-end gap-2">
                <div className="rounded-2xl rounded-bl-sm bg-gradient-to-tr from-indigo-500 to-purple-600 px-4 py-3 text-white shadow-md">
                  <p>Agent endpoint initializing... Awaiting secure connection parameters.</p>
                </div>
              </div>
            </div>
          </div>

          {/* iOS-style Input Bar */}
          <div className="flex items-center gap-2 rounded-full bg-white/50 dark:bg-black/40 p-1.5 shadow-inner backdrop-blur-md">
            <button className="flex h-10 w-10 items-center justify-center rounded-full bg-black/5 dark:bg-white/10 text-indigo-500 dark:text-emerald-400 hover:bg-black/10 transition">
              <Plus className="h-5 w-5" />
            </button>
            <input 
              type="text" 
              placeholder="Ask anything..." 
              className="flex-1 bg-transparent px-2 text-[15px] font-medium placeholder-slate-500 outline-none dark:text-white dark:placeholder-slate-400"
              readOnly
            />
            <button className="flex h-10 w-10 items-center justify-center rounded-full text-indigo-500 dark:text-emerald-400 hover:bg-black/5 dark:hover:bg-white/10 transition">
              <Mic className="h-5 w-5" />
            </button>
          </div>

        </div>
      )}
      
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className={`group flex h-16 w-16 items-center justify-center rounded-[1.5rem] bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-[0_16px_32px_rgba(79,70,229,0.4)] transition-all duration-500 hover:scale-105 hover:shadow-[0_24px_48px_rgba(79,70,229,0.6)] focus:outline-none ${isOpen ? "rotate-[360deg] scale-90 opacity-0 pointer-events-none" : ""}`}
      >
        <Bot className="h-7 w-7" />
      </button>
    </div>
  );
}
