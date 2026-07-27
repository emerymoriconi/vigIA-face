import { useState, useEffect, useRef, useCallback } from 'react';
import { ConnectionStatus, CameraDevice, Detection } from '../types';
import { WS_URL, API_KEY } from '../config/env';

export const useWebSocket = (
  isSystemRunning: boolean,
  isCaptureMode: boolean,
  selectedCam: string,
  setAvailableCameras: (cameras: CameraDevice[]) => void,
  setSelectedCam: (cam: string) => void,
  setDetections: React.Dispatch<React.SetStateAction<Detection[]>>,
  setPersistentHistory: React.Dispatch<React.SetStateAction<Detection[]>>
) => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [mainStream, setMainStream] = useState<string | null>(null);
  const [fps, setFps] = useState<number>(0);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isRunningRef = useRef(false);

  useEffect(() => {
    isRunningRef.current = isSystemRunning;
  }, [isSystemRunning]);

  const connectWebSocket = useCallback(() => {
    if (!isRunningRef.current) return;
    if (socketRef.current?.readyState === WebSocket.OPEN || socketRef.current?.readyState === WebSocket.CONNECTING) return;
    
    setConnectionStatus('connecting');
    const ws = new WebSocket(`${WS_URL}?token=${API_KEY}`);
    socketRef.current = ws;

    ws.onopen = () => {
      setConnectionStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "SETTINGS_SYNC") {
            setAvailableCameras(data.payload.cameras || []);
            if (data.payload.cameras?.length > 0 && selectedCam === '0') {
                setSelectedCam(data.payload.cameras[0].index.toString());
            }
        } else if (data.type === "VIDEO_FRAME") {
          setMainStream(data.payload.image);
          if (data.payload.fps !== undefined) setFps(data.payload.fps);
        } else if (data.type === "NEW_DETECTION") {
          try {
            if (!data.payload || !data.payload.metadata) {
              console.warn("WS: Payload de detecção inválido ignorado");
              return;
            }

            const newDet: Detection = {
              id: data.payload.history_id || `temp-${Math.random().toString(36).substring(2, 9)}`,
              timestamp: Date.now(),
              camera_id: data.payload.metadata.camera_id || "CAM-UNKNOWN",
              image: data.payload.image,
              metadata: {
                ...data.payload.metadata,
                ia_prob: data.payload.metadata.ia_prob || 0,
                nome_completo: data.payload.metadata.nome_completo || "Desconhecido",
                cpf: data.payload.metadata.cpf || ""
              }
            };
            
            setDetections(prev => {
              const personKey = (newDet.metadata.cpf && newDet.metadata.cpf !== "N/A") 
                ? newDet.metadata.cpf 
                : newDet.metadata.nome_completo;
                
              const filtered = prev.filter(d => {
                const dKey = (d.metadata.cpf && d.metadata.cpf !== "N/A") 
                  ? d.metadata.cpf 
                  : d.metadata.nome_completo;
                return dKey !== personKey;
              });
              
              return [newDet, ...filtered].slice(0, 20);
            });

            if (data.payload.history_id) {
               setPersistentHistory(prev => [newDet, ...prev]);
            }
          } catch (err) {
            console.error("Erro ao processar nova detecção:", err);
          }
        }
      } catch (err) {
        console.error("WS error:", err);
      }
    };

    ws.onclose = () => {
      setConnectionStatus('disconnected');
      setMainStream(null);
      setFps(0);
      if (isRunningRef.current) reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
    };
  }, [selectedCam, setAvailableCameras, setDetections, setPersistentHistory, setSelectedCam]);

  useEffect(() => {
    if (isSystemRunning) connectWebSocket();
    else {
      if (socketRef.current) {
        socketRef.current.onclose = null;
        socketRef.current.close();
        socketRef.current = null;
      }
      setConnectionStatus('disconnected');
      setMainStream(null);
      setFps(0);
    }
  }, [isSystemRunning, connectWebSocket]);

  useEffect(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: "SET_INFERENCE",
        payload: { enabled: !isCaptureMode }
      }));
    }
  }, [isCaptureMode]);

  const sendSettings = useCallback((cam: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: "CONFIG_CHANGE",
        payload: { selected_camera: cam }
      }));
    }
  }, []);

  return { connectionStatus, mainStream, fps, sendSettings, setMainStream };
};
