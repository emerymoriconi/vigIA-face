import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    // Busca variáveis de ambiente na raiz do projeto (../)
    const env = loadEnv(mode, path.resolve(__dirname, '..'), '');
    
    return {
      server: {
        port: 3000,
        host: '0.0.0.0',
      },
      envDir: '../', // Define explicitamente o diretório dos arquivos .env
      plugins: [react()],
      define: {
        'process.env.VITE_VIGIA_API_KEY': JSON.stringify(env.VITE_VIGIA_API_KEY),
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      }
    };
});
