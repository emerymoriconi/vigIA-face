import React, { useState } from 'react';
import { Maximize2, LayoutDashboard, History, UserPlus, Monitor, Camera, Play, Square, Check, RefreshCw, Cpu, Activity, Thermometer, Globe } from 'lucide-react';
import { CameraDevice, ApiHealth } from '../types';

interface HeaderProps {
  activeTab: 'live' | 'history' | 'register' | 'system';
  setActiveTab: (tab: 'live' | 'history' | 'register' | 'system') => void;
  apiHealth: ApiHealth;
  hardware: {cpu: number, ram_percent: number, ram_available_mb: number, temperature?: number} | null;
  isSystemRunning: boolean;
  setIsSystemRunning: (running: boolean) => void;
  availableCameras: CameraDevice[];
  selectedCam: string;
  setSelectedCam: (cam: string) => void;
  onApplySettings: (cam?: string) => void;
  setIsCaptureMode: (mode: boolean) => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab, setActiveTab, apiHealth, hardware, isSystemRunning, setIsSystemRunning,
  availableCameras, selectedCam, setSelectedCam, onApplySettings, setIsCaptureMode
}) => {
  const [applyStatus, setApplyStatus] = useState<'idle' | 'saving' | 'done'>('idle');

  const handleCameraChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newCam = e.target.value;
    setSelectedCam(newCam);
    setApplyStatus('saving');
    onApplySettings(newCam);
    setTimeout(() => {
        setApplyStatus('done');
        setTimeout(() => setApplyStatus('idle'), 2000);
    }, 800);
  };

  return (
    <header className="bg-white border-b border-slate-200 shadow-sm z-30">
      <div className="max-w-[1920px] mx-auto px-3 md:px-6 py-2 flex flex-col lg:flex-row items-center justify-between gap-3">
        
        {/* Superior: Logo e Status de Hardware */}
        <div className="flex items-center justify-between w-full lg:w-auto gap-4">
          <div className="flex items-center gap-2 shrink-0">
            <div className="bg-slate-900 text-white p-1.5 md:p-2 rounded-lg"><Maximize2 size={16} className="md:size-[18px]" /></div>
            <div>
              <h1 className="font-black text-sm md:text-base text-slate-900 leading-none uppercase tracking-tighter">Vigia-Face</h1>
              <span className="text-[8px] text-slate-400 font-bold uppercase tracking-widest">v1.1 SLIM</span>
            </div>
          </div>

          {hardware && (
            <div className="flex items-center gap-1 md:gap-1.5 overflow-x-auto no-scrollbar pb-1 lg:pb-0">
              <div className="flex items-center gap-1 px-2 py-1 bg-slate-50 border border-slate-100 rounded-md">
                <Cpu size={10} className="text-slate-400" />
                <span className="text-[10px] font-bold text-slate-700">{hardware.cpu}%</span>
              </div>
              <div className="flex items-center gap-1 px-2 py-1 bg-slate-50 border border-slate-100 rounded-md">
                <Activity size={10} className="text-slate-400" />
                <span className="text-[10px] font-bold text-slate-700">{hardware.ram_percent}%</span>
              </div>
              {hardware.temperature !== undefined && (
                <div className={`flex items-center gap-1 px-2 py-1 border rounded-md ${hardware.temperature > 75 ? 'bg-red-50 border-red-200' : 'bg-slate-50 border-slate-100'}`}>
                  <Thermometer size={10} className={hardware.temperature > 75 ? 'text-red-400' : 'text-slate-400'} />
                  <span className={`text-[10px] font-bold ${hardware.temperature > 75 ? 'text-red-700' : 'text-slate-700'}`}>{hardware.temperature.toFixed(0)}°</span>
                </div>
              )}
              <div className={`flex items-center gap-1 px-2 py-1 border rounded-md ${apiHealth === 'online' ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100'}`}>
                <Globe size={10} className={apiHealth === 'online' ? 'text-emerald-500' : 'text-red-500'} />
                <span className={`text-[10px] font-bold ${apiHealth === 'online' ? 'text-emerald-700' : 'text-red-700'}`}>{apiHealth === 'online' ? 'ON' : 'OFF'}</span>
              </div>
            </div>
          )}
        </div>

        {/* Central: Navegação de Abas */}
        <nav className="flex items-center w-full lg:w-auto justify-center order-3 lg:order-2">
          <div className="flex w-full sm:w-auto bg-slate-100/80 p-1 rounded-xl border border-slate-200/60 justify-between sm:justify-start gap-1">
            {[
              { id: 'live', label: 'Live', icon: LayoutDashboard },
              { id: 'history', label: 'Histórico', icon: History },
              { id: 'register', label: 'Cadastro', icon: UserPlus },
              { id: 'system', label: 'Sistema', icon: Monitor }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => { setActiveTab(tab.id as any); setIsCaptureMode(false); }}
                className={`flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 flex-1 sm:flex-none px-3 sm:px-4 py-1.5 md:py-2 rounded-lg text-[10px] md:text-xs font-bold transition-all ${
                  activeTab === tab.id 
                  ? 'bg-white text-slate-900 shadow-md border border-slate-200 translate-y-[-1px]' 
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50'
                }`}
              >
                <tab.icon size={16} />
                <span className="uppercase tracking-tighter sm:tracking-normal">{tab.label}</span>
              </button>
            ))}
          </div>
        </nav>

        {/* Direita: Controles de Câmera e Sistema */}
        <div className="flex items-center justify-between lg:justify-end w-full lg:w-auto gap-2 md:gap-3 order-2 lg:order-3">
          <div className="flex items-center gap-1.5 bg-slate-50 px-2 py-1.5 rounded-lg border border-slate-200 flex-1 lg:flex-none">
            <div className="text-slate-400">
              {applyStatus === 'saving' ? <RefreshCw size={14} className="animate-spin text-emerald-600" /> : applyStatus === 'done' ? <Check size={14} className="text-emerald-600" /> : <Camera size={14} />}
            </div>
            <select 
              value={selectedCam} 
              onChange={handleCameraChange} 
              className="bg-transparent text-[11px] font-bold text-slate-700 outline-none w-full lg:min-w-[120px] appearance-none cursor-pointer uppercase tracking-tight"
            >
              {availableCameras.length === 0 ? <option value="0">BUSCANDO...</option> : availableCameras.map(c => <option key={c.index} value={c.index}>{c.name}</option>)}
            </select>
          </div>
          
          <button 
            onClick={() => setIsSystemRunning(!isSystemRunning)} 
            disabled={apiHealth !== 'online'} 
            className={`flex items-center justify-center gap-2 px-6 py-2 rounded-lg font-black text-xs transition-all active:scale-95 shadow-lg border-b-4 ${
              isSystemRunning 
              ? 'bg-red-600 text-white border-red-800 hover:bg-red-700 shadow-red-200' 
              : 'bg-slate-900 text-white border-slate-950 hover:bg-slate-800 shadow-slate-200'
            }`}
          >
            {isSystemRunning ? <Square size={12} fill="currentColor" /> : <Play size={12} fill="currentColor" />}
            <span>{isSystemRunning ? "STOP" : "START"}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
