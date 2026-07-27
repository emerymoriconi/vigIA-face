import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { DetailModal } from './components/DetailModal';
import { LiveView } from './features/live/LiveView';
import { HistoryView } from './features/history/HistoryView';
import { RegisterView } from './features/register/RegisterView';
import { SystemView } from './features/system/SystemView';
import { useWebSocket } from './hooks/useWebSocket';
import { Detection, CameraDevice, ApiHealth } from './types';
import { API_KEY, API_URL } from './config/env';

export const App = () => {
  const [activeTab, setActiveTab] = useState<'live' | 'history' | 'register' | 'system'>('live');
  const [isSystemRunning, setIsSystemRunning] = useState(false);
  const [apiHealth, setApiHealth] = useState<ApiHealth>('checking');
  
  const [hardware, setHardware] = useState<{cpu: number, ram_percent: number, ram_available_mb: number, temperature?: number} | null>(null);
  const [dbStats, setDbStats] = useState<{total: number}>({total: 0});
  const [logs, setLogs] = useState<string>('');
  
  const [availableCameras, setAvailableCameras] = useState<CameraDevice[]>([]);
  const [selectedCam, setSelectedCam] = useState<string>('0');
  
  const [detections, setDetections] = useState<Detection[]>([]);
  const [persistentHistory, setPersistentHistory] = useState<Detection[]>([]);
  const [selectedDetection, setSelectedDetection] = useState<Detection | null>(null);

  const [regForm, setRegForm] = useState({ nome: '', cpf: '', nascimento: '' });
  const [regImage, setRegImage] = useState<File | null>(null);
  const [regPreview, setRegPreview] = useState<string | null>(null);
  const [regStatus, setRegStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [isCaptureMode, setIsCaptureMode] = useState(false);

  const { mainStream, fps, sendSettings } = useWebSocket(
    isSystemRunning, isCaptureMode, selectedCam,
    setAvailableCameras, setSelectedCam, setDetections, setPersistentHistory
  );

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/status`);
      if (res.ok) {
        const data = await res.json();
        setHardware(data.hardware);
        setApiHealth('online');
      } else {
        setApiHealth('offline');
      }
    } catch (err) {
      setApiHealth('offline');
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/history`, {
        headers: { 'X-API-Key': API_KEY }
      });
      if (res.ok) {
        const data = await res.json();
        setPersistentHistory(data);
      }
    } catch (err) {
      console.error("Error fetching history:", err);
    }
  }, []);

  const fetchDbInspect = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/db_inspect`, {
        headers: { 'X-API-Key': API_KEY }
      });
      if (res.ok) {
        const data = await res.json();
        setDbStats(data);
      }
    } catch (err) { console.error(err); }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/logs?lines=100`, {
        headers: { 'X-API-Key': API_KEY }
      });
      if (res.ok) {
        const text = await res.text();
        setLogs(text);
      }
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  useEffect(() => {
    if (activeTab === 'system') {
      fetchDbInspect();
      fetchLogs();
      const t = setInterval(fetchLogs, 5000);
      return () => clearInterval(t);
    }
  }, [activeTab, fetchDbInspect, fetchLogs]);

  const handleApplySettings = (cam?: string) => {
    sendSettings(cam || selectedCam);
  };

  const handleRegister = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!regImage || !regForm.nome || !regForm.cpf) return;
    setRegStatus('loading');
    const formData = new FormData();
    formData.append('file', regImage);
    formData.append('nome', regForm.nome);
    formData.append('cpf', regForm.cpf);
    formData.append('nascimento', regForm.nascimento);
    try {
      const response = await fetch(`${API_URL}/register`, { 
        method: 'POST', 
        body: formData,
        headers: { 'X-API-Key': API_KEY }
      });
      if (response.ok) {
        setRegStatus('success');
        setRegForm({ nome: '', cpf: '', nascimento: '' });
        setRegImage(null);
        setRegPreview(null);
        setIsCaptureMode(false);
        setTimeout(() => setRegStatus('idle'), 5000);
        fetchHistory();
      } else {
        throw new Error("Erro no servidor");
      }
    } catch (err: any) {
      setRegStatus('error');
    }
  };

  const handleCapture = () => {
    if (!mainStream) return;
    const byteCharacters = atob(mainStream);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], {type: 'image/jpeg'});
    const file = new File([blob], "capture.jpg", {type: 'image/jpeg'});
    setRegImage(file);
    setRegPreview(`data:image/jpeg;base64,${mainStream}`);
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setRegImage(file);
      const reader = new FileReader();
      reader.onloadend = () => setRegPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50 font-sans antialiased">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        apiHealth={apiHealth}
        hardware={hardware}
        isSystemRunning={isSystemRunning}
        setIsSystemRunning={setIsSystemRunning}
        availableCameras={availableCameras}
        selectedCam={selectedCam}
        setSelectedCam={setSelectedCam}
        onApplySettings={handleApplySettings}
        setIsCaptureMode={setIsCaptureMode}
      />
      <main className="flex-1 overflow-hidden relative flex">
        {activeTab === 'live' && (
          <LiveView
            isSystemRunning={isSystemRunning}
            mainStream={mainStream}
            selectedCam={selectedCam}
            fps={fps}
            detections={detections}
            setSelectedDetection={setSelectedDetection}
          />
        )}
        {activeTab === 'history' && (
          <HistoryView
            persistentHistory={persistentHistory}
            fetchHistory={fetchHistory}
            setSelectedDetection={setSelectedDetection}
          />
        )}
        {activeTab === 'register' && (
          <RegisterView
            isCaptureMode={isCaptureMode}
            setIsCaptureMode={setIsCaptureMode}
            regPreview={regPreview}
            setRegPreview={setRegPreview}
            regStatus={regStatus}
            setRegStatus={setRegStatus}
            handleRegister={handleRegister}
            apiHealth={apiHealth}
            regImage={regImage}
            mainStream={mainStream}
            handleCapture={handleCapture}
            handleImageChange={handleImageChange}
            regForm={regForm}
            setRegForm={setRegForm}
          />
        )}
        {activeTab === 'system' && (
          <SystemView
            hardware={hardware}
            dbStats={dbStats}
            logs={logs}
            fetchLogs={fetchLogs}
          />
        )}
      </main>
      <DetailModal detection={selectedDetection} onClose={() => setSelectedDetection(null)} />
    </div>
  );
};
