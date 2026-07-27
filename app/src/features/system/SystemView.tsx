import React from 'react';
import { Activity, Monitor, Globe, User, RefreshCw, Thermometer } from 'lucide-react';

interface SystemViewProps {
  hardware: {cpu: number, ram_percent: number, ram_available_mb: number, temperature?: number} | null;
  dbStats: {total: number};
  logs: string;
  fetchLogs: () => void;
}

export const SystemView: React.FC<SystemViewProps> = ({
  hardware, dbStats, logs, fetchLogs
}) => {
  return (
    <div className="flex-1 p-3 md:p-6 lg:p-8 overflow-auto bg-slate-50/50">
      <div className="max-w-7xl mx-auto space-y-4 md:space-y-6">
         
         {/* Cabeçalho Técnico */}
         <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-200 pb-4 md:pb-6">
           <div>
             <h2 className="text-lg md:text-xl font-bold text-slate-900 uppercase tracking-tight">SISTEMA</h2>
             <p className="text-slate-500 text-[9px] md:text-[10px] font-bold uppercase tracking-widest mt-1">
               Monitoramento em tempo real de hardware e logs
             </p>
           </div>
         </div>

         {/* Grid de Hardware Adaptativa */}
         <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 md:gap-4">
            {[
              { label: 'CPU-LOAD', val: `${hardware?.cpu ?? '0'}%`, icon: Activity },
              { label: 'MEM-USWD', val: `${hardware?.ram_percent ?? '0'}%`, icon: Monitor },
              { label: 'MEM-FREE', val: `${hardware?.ram_available_mb ?? '0'}MB`, icon: Globe },
              { label: 'CORE-TEMP', val: `${hardware?.temperature ? hardware.temperature.toFixed(1) : 'N/A'}°C`, icon: Thermometer },
              { label: 'DB-TOTAL', val: `${dbStats?.total ?? '0'} VETORES`, icon: User }
            ].map((stat, i) => (
              <div key={i} className="bg-white p-3 md:p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col justify-center">
                <div className="flex items-center gap-2 mb-1 md:mb-2 opacity-40">
                  <stat.icon size={12} className="text-slate-900 md:size-4"/>
                  <span className="text-[7px] md:text-[8px] font-black uppercase tracking-widest">{stat.label}</span>
                </div>
                <div className="text-base md:text-xl font-bold text-slate-900 truncate">{stat.val}</div>
              </div>
            ))}
         </div>

         {/* Área de Operações (Logs) */}
         <div className="grid grid-cols-1 gap-4">
            {/* Terminal de Logs - Adaptativo */}
            <div className="bg-slate-950 rounded-xl border border-slate-800 p-3 md:p-5 shadow-2xl flex flex-col min-h-[400px] lg:h-[650px]">
               <div className="flex justify-between items-center mb-4 px-1 md:px-2">
                 <div className="flex items-center gap-2 md:gap-3">
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                    <span className="text-[9px] md:text-[11px] font-bold text-slate-400 uppercase tracking-[0.2em]">Real_Time_Log_Stream</span>
                 </div>
                 <button 
                  onClick={fetchLogs} 
                  className="p-2 text-slate-500 hover:text-white hover:bg-white/5 rounded-full transition-all active:scale-95"
                  title="Atualizar Logs"
                 >
                  <RefreshCw size={16}/>
                 </button>
               </div>
               
               <div className="flex-1 overflow-auto bg-black rounded-lg border border-white/5 p-3 md:p-5 custom-scrollbar">
                  <pre className="text-[11px] md:text-[13px] font-mono text-slate-200 whitespace-pre-wrap selection:bg-slate-800 leading-relaxed">
                    {logs || "> SYSLOG_WAITING_FOR_DATA..."}
                  </pre>
               </div>
            </div>
         </div>
      </div>
    </div>
  );
};
