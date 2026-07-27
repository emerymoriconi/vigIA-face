export const API_KEY = import.meta.env.VITE_VIGIA_API_KEY;
export const WS_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.hostname}:8000/ws`;
export const API_URL = WS_URL.replace("ws://", "http://").replace("/ws", "");
