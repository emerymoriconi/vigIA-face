import React from 'react';
import { UserPlus, Upload, Scan, ShieldCheck, CircleCheck, Camera, Loader2, X, RefreshCw, Check } from 'lucide-react';
import { ApiHealth } from '../../types';
import { formatCPF, formatDate } from '../../utils/formatters';

interface RegisterViewProps {
  isCaptureMode: boolean;
  setIsCaptureMode: (mode: boolean) => void;
  regPreview: string | null;
  setRegPreview: (preview: string | null) => void;
  regStatus: 'idle' | 'loading' | 'success' | 'error';
  setRegStatus: (status: 'idle' | 'loading' | 'success' | 'error') => void;
  handleRegister: (e?: React.FormEvent) => void;
  apiHealth: ApiHealth;
  regImage: File | null;
  mainStream: string | null;
  handleCapture: () => void;
  handleImageChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  regForm: { nome: string; cpf: string; nascimento: string };
  setRegForm: (form: { nome: string; cpf: string; nascimento: string }) => void;
}

export const RegisterView: React.FC<RegisterViewProps> = ({
  isCaptureMode, setIsCaptureMode, regPreview, setRegPreview,
  regStatus, setRegStatus, handleRegister, apiHealth, regImage,
  mainStream, handleCapture, handleImageChange, regForm, setRegForm
}) => {
  return (
    <div className="flex-1 p-4 md:p-8 overflow-auto bg-slate-50 flex items-start md:items-center justify-center">
      <div className="max-w-4xl w-full bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden flex flex-col md:flex-row my-4 md:my-0">
        {/* Painel Lateral Industrial */}
        <div className="md:w-2/5 bg-slate-900 p-6 md:p-10 flex flex-col justify-between text-white shrink-0">
          <div>
            <div className="flex items-center gap-4 mb-6 md:block">
              <div className="bg-slate-800 w-10 h-10 md:w-12 md:h-12 rounded border border-slate-700 flex items-center justify-center md:mb-6 shadow-sm">
                <UserPlus size={20} className="md:w-6 md:h-6" />
              </div>
              <h2 className="text-xl md:text-3xl font-bold tracking-tight uppercase">Cadastro Facial</h2>
            </div>
            <p className="hidden md:block text-slate-400 text-[10px] font-bold uppercase tracking-widest leading-relaxed mb-8">System_Registration</p>
            <div className="grid grid-cols-2 md:grid-cols-1 gap-2">
              <button onClick={() => {setIsCaptureMode(false); setRegPreview(null);}} className={`flex items-center justify-center md:justify-start gap-3 px-4 py-3 rounded text-[10px] font-black uppercase transition-all border ${!isCaptureMode ? 'bg-white text-slate-900 border-white' : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'}`}><Upload size={16} /> <span className="hidden sm:inline">Upload_File</span><span className="sm:hidden">Upload</span></button>
              <button onClick={() => {setIsCaptureMode(true); setRegPreview(null);}} className={`flex items-center justify-center md:justify-start gap-3 px-4 py-3 rounded text-[10px] font-black uppercase transition-all border ${isCaptureMode ? 'bg-white text-slate-900 border-white' : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'}`}><Scan size={16} /> <span className="hidden sm:inline">Live_Capture</span><span className="sm:hidden">Live</span></button>
            </div>
          </div>
          <div className="hidden md:block">
            {isCaptureMode && (
              <div className="bg-emerald-500/10 border border-emerald-500/20 p-4 rounded flex items-center gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <p className="text-[9px] font-black text-emerald-500 uppercase tracking-widest">Inference_Paused</p>
              </div>
            )}
          </div>
        </div>

        {/* Área do Formulário */}
        <div className="md:w-3/5 p-10 relative bg-white border-l border-slate-50">
          {regStatus === 'success' && (
            <div className="absolute inset-0 bg-white/95 backdrop-blur-sm z-10 flex flex-col items-center justify-center p-10 text-center animate-in fade-in duration-300">
               <div className="w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center mb-4 border border-emerald-100">
                  <CircleCheck size={32} className="text-emerald-600" />
               </div>
               <h3 className="text-lg font-bold text-slate-900 uppercase mb-4 tracking-tight">Registrado</h3>
               <button onClick={() => setRegStatus('idle')} className="px-6 py-2 bg-slate-900 text-white rounded font-black text-[10px] uppercase tracking-widest shadow-lg">Novo Cadastro</button>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between items-center mb-1">
                 <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-1">{isCaptureMode ? "Input_Capture" : ""}</label>
                 {regPreview && isCaptureMode && <button type="button" onClick={() => setRegPreview(null)} className="text-red-500 text-[8px] font-black uppercase tracking-widest hover:underline">Reset_Camera</button>}
              </div>

              {isCaptureMode && !regPreview ? (
                <div className="relative aspect-video bg-slate-950 rounded border border-slate-800 overflow-hidden shadow-inner flex items-center justify-center group">
                  {mainStream ? (
                    <>
                      <img src={`data:image/jpeg;base64,${mainStream}`} className="w-full h-full object-cover opacity-80" alt="Camera Stream" />
                      <div className="absolute inset-0 pointer-events-none border-2 border-white/5 m-8 rounded-lg flex items-center justify-center">
                         <div className="w-4 h-4 border-t-2 border-l-2 border-emerald-500 absolute top-0 left-0" />
                         <div className="w-4 h-4 border-t-2 border-r-2 border-emerald-500 absolute top-0 right-0" />
                         <div className="w-4 h-4 border-b-2 border-l-2 border-emerald-500 absolute bottom-0 left-0" />
                         <div className="w-4 h-4 border-b-2 border-r-2 border-emerald-500 absolute bottom-0 right-0" />
                      </div>
                      <button type="button" onClick={handleCapture} className="absolute bottom-4 bg-white text-slate-900 px-6 py-2 rounded font-black text-[10px] uppercase tracking-[0.2em] shadow-2xl hover:bg-slate-100 active:scale-95 transition-all">Execute_Capture</button>
                    </>
                  ) : (
                    <div className="flex flex-col items-center justify-center gap-3 text-slate-700">
                      <RefreshCw size={24} className="animate-spin" />
                      <span className="text-[9px] font-bold uppercase tracking-widest">Awaiting_Stream</span>
                    </div>
                  )}
                </div>
              ) : (
                <div onClick={() => !isCaptureMode && document.getElementById('face-upload')?.click()} className={`border-2 border-dashed rounded p-10 flex flex-col items-center justify-center gap-4 cursor-pointer transition-all ${regPreview ? 'border-emerald-500 bg-emerald-50/10' : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'}`}>
                  {regPreview ? (
                    <img src={regPreview} className="w-32 h-32 lg:w-40 lg:h-40 rounded object-cover shadow-md border border-white grayscale hover:grayscale-0 transition-all" alt="Preview" />
                  ) : (
                    <>
                      <div className="p-4 bg-white rounded border border-slate-100 shadow-sm text-slate-400"><Upload size={24} /></div>
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Select_Image_File</p>
                    </>
                  )}
                  {!isCaptureMode && <input id="face-upload" type="file" className="hidden" accept="image/*" onChange={handleImageChange} />}
                </div>
              )}
            </div>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-[9px] font-black text-slate-400 uppercase tracking-[0.1em] ml-1">Nome</label>
                <input type="text" value={regForm.nome} onChange={e => setRegForm({...regForm, nome: e.target.value})} placeholder="ENTRADA_ALFABETICA" className="w-full bg-slate-50 border border-slate-200 rounded px-4 py-2.5 text-[11px] font-bold text-slate-800 outline-none focus:border-slate-900 transition-colors uppercase" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-[9px] font-black text-slate-400 uppercase tracking-[0.1em] ml-1">CPF</label>
                  <input type="text" value={regForm.cpf} onChange={e => setRegForm({...regForm, cpf: formatCPF(e.target.value)})} placeholder="000.000.000-00" className="w-full bg-slate-50 border border-slate-200 rounded px-4 py-2.5 text-[11px] font-bold text-slate-800 outline-none focus:border-slate-900 transition-colors" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-[9px] font-black text-slate-400 uppercase tracking-[0.1em] ml-1">Data de Nascimento</label>
                  <input type="text" value={regForm.nascimento} onChange={e => setRegForm({...regForm, nascimento: formatDate(e.target.value)})} placeholder="DD/MM/AAAA" className="w-full bg-slate-50 border border-slate-200 rounded px-4 py-2.5 text-[11px] font-bold text-slate-800 outline-none focus:border-slate-900 transition-colors" />
                </div>
              </div>
            </div>

            <button type="submit" disabled={regStatus === 'loading' || apiHealth !== 'online' || !regImage} className="w-full py-4 rounded font-black text-xs uppercase tracking-[0.2em] transition-all shadow-md active:scale-95 bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50 flex items-center justify-center gap-3 border-b-4 border-slate-950">
              {regStatus === 'loading' ? <RefreshCw size={16} className="animate-spin" /> : <Check size={16} />}
              REGISTRAR
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};