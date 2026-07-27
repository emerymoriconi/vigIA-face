import React, { useState } from 'react';
import { RefreshCw, Clock, MapPin, ChevronUp, ChevronDown } from 'lucide-react';
import { Detection, GroupedHistory } from '../../types';
import { API_URL } from '../../config/env';

interface HistoryViewProps {
  persistentHistory: Detection[];
  fetchHistory: () => void;
  setSelectedDetection: (det: Detection) => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({ persistentHistory, fetchHistory, setSelectedDetection }) => {
  const [expandedHistoryCard, setExpandedHistoryCard] = useState<string | null>(null);

  const groupedHistory = persistentHistory.reduce((acc: GroupedHistory, det) => {
    const key = det.metadata.cpf || det.metadata.nome_completo;
    if (!acc[key]) {
      acc[key] = {
        person: det.metadata,
        detections: [],
        lastTimestamp: det.timestamp,
        lastImage: det.image_url ? `${API_URL}${det.image_url}` : (det.image ? `data:image/jpeg;base64,${det.image}` : '')
      };
    }
    acc[key].detections.push({ 
      id: det.id,
      timestamp: det.timestamp, 
      image_url: det.image_url ? `${API_URL}${det.image_url}` : '', 
      prob: det.metadata.ia_prob 
    });
    if (det.timestamp > acc[key].lastTimestamp) {
        acc[key].lastTimestamp = det.timestamp;
        if (det.image_url) acc[key].lastImage = `${API_URL}${det.image_url}`;
    }
    return acc;
  }, {});

  const sortedGroups = Object.entries(groupedHistory).sort((a: any, b: any) => b[1].lastTimestamp - a[1].lastTimestamp);

  return (
    <div className="flex-1 p-4 lg:p-8 overflow-auto bg-slate-50">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-end mb-8 border-b border-slate-200 pb-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 uppercase tracking-tight">Histórico de Detecções</h2>
          </div>
          <button onClick={fetchHistory} className="p-2 text-slate-400 hover:text-slate-900 transition-all">
            <RefreshCw size={20} />
          </button>
        </div>

        {sortedGroups.length === 0 ? (
          <div className="bg-white border border-dashed border-slate-300 rounded-lg p-20 text-center">
            <Clock size={40} className="mx-auto text-slate-200 mb-4" />
            <p className="text-slate-400 font-bold uppercase tracking-widest text-[10px]">DATABASE_EMPTY</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
            {sortedGroups.map(([cpf, data]: [string, any]) => (
              <div key={cpf} className="bg-white rounded border border-slate-200 shadow-sm overflow-hidden flex flex-col group hover:border-slate-400 transition-all">
                <div className="relative aspect-square overflow-hidden bg-slate-100">
                  <img 
                    src={data.lastImage} 
                    className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500" 
                    alt="Profile" 
                    onClick={() => setSelectedDetection({ 
                      id: data.detections[0].id, 
                      camera_id: data.person.camera_id, 
                      metadata: data.person, 
                      timestamp: data.lastTimestamp, 
                      image_url: data.lastImage.replace(API_URL, '') 
                    })} 
                  />
                </div>
                
                <div className="p-3 flex-1 flex flex-col">
                  <div className="mb-2">
                    <span className="text-[7px] font-black text-emerald-600 uppercase tracking-widest mb-0.5 block line-clamp-1">IDENTIFIED</span>
                    <h4 className="font-bold text-slate-900 text-[11px] leading-tight truncate uppercase">{data.person.nome_completo}</h4>
                  </div>

                  <div className="grid grid-cols-2 gap-1.5 mb-2">
                     <div className="px-2 py-1 bg-slate-50 rounded border border-slate-100">
                        <span className="block text-[6px] font-black text-slate-400 uppercase mb-0.5">Visto</span>
                        <span className="text-[10px] font-bold text-slate-800">{data.detections.length}x</span>
                     </div>
                     <div className="px-2 py-1 bg-slate-50 rounded border border-slate-100">
                        <span className="block text-[6px] font-black text-slate-400 uppercase mb-0.5">Hora</span>
                        <span className="text-[9px] font-bold text-slate-800">{new Date(data.lastTimestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                     </div>
                  </div>

                  <button 
                    onClick={() => setExpandedHistoryCard(expandedHistoryCard === cpf ? null : cpf)} 
                    className="w-full flex items-center justify-center gap-2 py-1.5 text-[7px] font-black text-slate-400 hover:text-slate-900 transition-colors uppercase tracking-widest border-t border-slate-50 mt-auto"
                  >
                    {expandedHistoryCard === cpf ? 'Ocultar' : 'Timeline'}
                  </button>
                  
                  {expandedHistoryCard === cpf && (
                    <div className="mt-2 space-y-1 max-h-24 overflow-y-auto pr-1 custom-scrollbar">
                      {data.detections.map((det: any) => (
                        <div 
                          key={det.id} 
                          className="flex justify-between items-center text-[8px] font-bold p-1 hover:bg-slate-100 rounded border border-transparent cursor-default transition-all"
                        >
                          <span className="text-slate-500">{new Date(det.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</span>
                          <span className="text-emerald-600">{Math.round(det.prob * 100)}%</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
