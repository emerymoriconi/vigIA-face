import React from 'react';
import { Maximize2, User, X, CreditCard, Calendar } from 'lucide-react';
import { Detection } from '../types';
import { API_URL } from '../config/env';

interface DetailModalProps {
  detection: Detection | null;
  onClose: () => void;
}

export const DetailModal: React.FC<DetailModalProps> = ({ detection, onClose }) => {
  if (!detection) return null;
  
  const isHistory = !!detection.image_url;
  const imgSource = detection.image 
    ? (detection.image.startsWith('data:') ? detection.image : `data:image/jpeg;base64,${detection.image}`)
    : (detection.image_url ? `${API_URL}${detection.image_url}` : '');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-[2.5rem] shadow-2xl w-full max-w-5xl overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col md:flex-row">
        <div className="md:w-2/3 bg-slate-900 relative group overflow-hidden">
          <img src={imgSource} className="w-full h-full object-contain" alt="Capture" />
          <div className="absolute top-6 left-6 bg-black/50 backdrop-blur-lg px-4 py-2 rounded-2xl border border-white/10 text-white text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
            {isHistory ? <><Maximize2 size={14}/> Visão Ampla</> : <><User size={14}/> Tempo Real</>}
          </div>
        </div>

        <div className="md:w-1/3 p-8 flex flex-col justify-between bg-white border-l border-slate-100">
          <div>
            <div className="flex justify-between items-center mb-8">
              <div className="bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter">Ficha Identificada</div>
              <button onClick={onClose} className="text-slate-300 hover:text-slate-600 transition-colors"><X size={24} /></button>
            </div>

            <div className="space-y-6">
              <div>
                <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Identidade</h3>
                <h2 className="text-2xl font-black text-slate-800 leading-tight uppercase tracking-tighter">{detection.metadata.nome_completo}</h2>
                <div className="flex flex-col gap-2 mt-4 text-sm font-bold text-slate-500">
                  <div className="flex items-center gap-2"><CreditCard size={16} className="text-slate-300"/> CPF: <span className="text-slate-800">{detection.metadata.cpf || 'N/A'}</span></div>
                  <div className="flex items-center gap-2"><Calendar size={16} className="text-slate-300"/> Nasc: <span className="text-slate-800">{detection.metadata.data_nascimento || 'N/A'}</span></div>
                </div>
              </div>

              <div className="pt-6 border-t border-slate-50">
                <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Dados da Captura</h3>
                <div className="space-y-3">
                   <div className="flex items-center justify-between p-3 bg-slate-50 rounded-2xl">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Confiança IA</span>
                      <span className="text-sm font-black text-emerald-600">{Math.round(detection.metadata.ia_prob * 100)}%</span>
                   </div>
                   <div className="flex items-center justify-between p-3 bg-slate-50 rounded-2xl">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Horário</span>
                      <span className="text-sm font-black text-slate-700">{new Date(detection.timestamp).toLocaleString()}</span>
                   </div>
                </div>
              </div>
            </div>
          </div>
          <button onClick={onClose} className="w-full py-4 mt-8 bg-slate-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-slate-800 transition-all shadow-xl shadow-slate-200">Fechar Ficha</button>
        </div>
      </div>
    </div>
  );
};
