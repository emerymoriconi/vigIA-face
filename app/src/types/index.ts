export interface PersonData {
  nome_completo: string;
  cpf: string;
  nome_mae: string;
  data_nascimento: string;
  idade: number;
}

export interface Metrics {
  ia_prob: number;
  euclidian_score: number;
  camera_id: string;
}

export interface Detection {
  id: string;
  timestamp: number;
  camera_id: string;
  image?: string; // Base64 para live
  image_url?: string; // URL para histórico
  metadata: PersonData & Metrics;
}

export interface LiveFace {
  box: number[]; // [x, y, w, h] em percentual
  name: string;
  prob: number;
}

export interface GroupedHistory {
  [cpf: string]: {
    person: PersonData & Metrics;
    detections: { timestamp: number; image_url: string; prob: number; id: string }[];
    lastTimestamp: number;
    lastImage: string;
  }
}

export interface CameraDevice {
  index: number;
  name: string;
  type: string;
}

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';
export type ApiHealth = 'online' | 'offline' | 'checking';
