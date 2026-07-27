import React from 'react';
import { Monitor, Activity, CircleAlert, ChevronRight, Check } from 'lucide-react';
import { Detection } from '../../types';

interface LiveViewProps {
  isSystemRunning: boolean;
  mainStream: string | null;
  selectedCam: string;
  fps: number;
  detections: Detection[];
  setSelectedDetection: (det: Detection) => void;
}

export const LiveView: React.FC<LiveViewProps> = ({
  isSystemRunning, mainStream, selectedCam, fps, detections, setSelectedDetection
}) => {
  return (
    <div className="flex-1 flex flex-col lg:flex-row h-full overflow-hidden bg-slate-50">
      {/* Área do Monitor Central */}
      <div className="flex-1 flex items-center justify-center p-2 lg:p-4 bg-slate-50">
        <div className="w-full h-full max-w-6xl bg-slate-200 rounded-lg overflow-hidden shadow-sm border border-slate-200 relative flex items-center justify-center group">
          {isSystemRunning && mainStream ? (
            <img src={`data:image/jpeg;base64,${mainStream}`} className="w-full h-full object-contain" alt="Live Feed" />
          ) : (
            <div className="flex flex-col items-center justify-center text-center p-6">
              <Monitor size={48} className="text-slate-800 mb-4 animate-pulse" />
              <span className="font-bold text-[10px] text-slate-600 uppercase tracking-[0.2em]">{isSystemRunning ? "SINCRO_DATA..." : "NO_SIGNAL"}</span>
            </div>
          )}
          
          {/* Overlay OSD (On-Screen Display) */}
          {isSystemRunning && mainStream && (
            <>
              <div className="absolute top-4 left-4 flex items-center gap-2 px-2 py-1 bg-black/40 backdrop-blur-md border border-white/10 rounded text-[9px] font-mono text-white/80 uppercase">
                <div className="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse" />
                REC • CAM_{selectedCam} • {fps} FPS
              </div>
              <div className="absolute bottom-4 right-4 text-[9px] font-mono text-white/40 uppercase">
                {new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Painel de Eventos (Sidebar) */}
      <aside className="w-full lg:w-80 bg-slate-50 border-t lg:border-t-0 lg:border-l border-slate-200 flex flex-col h-[45%] lg:h-full shadow-sm">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-white">
          <h3 className="font-bold text-slate-500 text-[10px] uppercase tracking-widest flex items-center gap-2">
            <Activity size={14} className="text-emerald-500" /> Atividade Recente
          </h3>
          <span className="text-[9px] font-mono text-slate-400 font-bold">{detections.length} DET</span>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
          {detections.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-300 gap-3 opacity-50">
              <CircleAlert size={32} />
              <p className="text-[9px] font-bold uppercase tracking-widest">SCANNING...</p>
            </div>
          ) : (
            detections.map(det => (
              <div 
                key={det.id} 
                onClick={() => setSelectedDetection(det)} 
                className="flex items-center gap-3 p-2 bg-white hover:bg-slate-100 border border-slate-200 hover:border-slate-300 rounded shadow-sm transition-all cursor-pointer group"
              >
                <div className="relative shrink-0">
                  <img src={`data:image/jpeg;base64,${det.image}`} className="w-10 h-10 rounded-sm object-cover grayscale group-hover:grayscale-0 transition-all border border-slate-100" alt="Face" />
                  <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-emerald-600 rounded-full border-2 border-white flex items-center justify-center shadow-sm">
                    <Check size={6} className="text-white" />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-slate-800 text-[11px] truncate uppercase tracking-tight">{det.metadata.nome_completo}</p>
                  <div className="flex items-center justify-between mt-0.5">
                    <span className="text-[9px] font-mono text-slate-400 font-bold">{new Date(det.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}</span>
                    <span className="px-1 py-0.5 bg-emerald-50 text-emerald-600 text-[8px] font-mono rounded border border-emerald-100">
                      {Math.round(det.metadata.ia_prob * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </aside>
    </div>
  );
};
