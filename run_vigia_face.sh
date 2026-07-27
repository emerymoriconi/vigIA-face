#!/bin/bash

# Cores para o terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==============================${NC}"
echo -e "${BLUE}    INICIANDO VIGIA-FACE      ${NC}"
echo -e "${BLUE}==============================${NC}"

# 0. Verificações de Sanidade
if [ ! -f ".env" ]; then
    echo -e "${RED}Erro: Arquivo .env não encontrado.${NC}"
    echo -e "Rode ${BLUE}./setup.sh${NC} primeiro para gerar as chaves de segurança."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo -e "${RED}Erro: Ambiente virtual .venv não encontrado.${NC}"
    echo -e "Rode ${BLUE}./setup.sh${NC} primeiro."
    exit 1
fi

# 0.1 Limpeza Preventiva
echo -e "${BLUE}Limpando instâncias anteriores...${NC}"
if command -v fuser &> /dev/null; then
    fuser -k 8000/tcp 2>/dev/null
    fuser -k 3000/tcp 2>/dev/null
else
    pkill -f "python -m src.main" 2>/dev/null
    pkill -f "vite" 2>/dev/null
fi
# pkill -f auto_backup_sender.py 2>/dev/null

# 0.2 Iniciar Qdrant se necessário
# Verifica se a raiz (/) responde com HTTP 200
if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 http://localhost:6333/ | grep -q "200"; then
    echo -e "${GREEN}Qdrant já está rodando e acessível.${NC}"
else
    echo -e "${GREEN}Iniciando Qdrant no Docker...${NC}"
    docker compose up -d

    # Aguarda o Qdrant responder (máximo 30 segundos)
    echo -n "Aguardando Qdrant estabilizar..."
    for i in {1..30}; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:6333/ | grep -q "200"; then
            echo -e " ${GREEN}[OK]${NC}"
            break
        fi
        echo -n "."
        sleep 1
        if [ $i -eq 30 ]; then
            echo -e " ${RED}[TIMEOUT]${NC}"
            echo -e "Verifique os logs do Docker: ${BLUE}docker compose logs qdrant${NC}"
        fi
    done
fi

# 0.3 Ativar Ambiente Virtual
source .venv/bin/activate

# 1. Iniciar o Serviço de Auto-Backup Proativo (Rasp -> PC)
echo -e "${GREEN}Iniciando agente de backup proativo...${NC}"
# python scripts/auto_backup_sender.py &
BACKUP_PID=$!

# 2. Iniciar o Backend (FastAPI + Camera + AI)
echo -e "${GREEN}Iniciando backend (FastAPI)...${NC}"
export ORT_LOGGING_LEVEL=3
python -m src.main &
BACKEND_PID=$!

# 3. Iniciar o Frontend (Vite)
echo -e "${GREEN}Iniciando frontend (Vite)...${NC}"
cd app
npm run dev -- --host &
FRONTEND_PID=$!
cd ..

echo -e "${BLUE}==============================${NC}"
echo -e "${BLUE}  SISTEMA RODANDO COM SUCESSO   ${NC}"
echo -e "${BLUE}==============================${NC}"
echo -e "Backend:  ${GREEN}http://$(hostname).local:8000${NC}"
echo -e "Frontend: ${GREEN}http://$(hostname).local:3000${NC}"
echo -e "Logs:     ${BLUE}tail -f logs/app.log${NC}"
echo -e "Pressione ${BLUE}Ctrl+C${NC} para encerrar."

# Função para encerrar os processos ao sair
cleanup() {
    echo -e "\n${BLUE}Encerrando Vigia-Face e limpando processos...${NC}"
    
    # Mata os processos capturados pelos PIDs
    kill $BACKEND_PID $FRONTEND_PID $BACKUP_PID 2>/dev/null
    
    # Limpeza profunda por porta e nome
    if command -v fuser &> /dev/null; then
        fuser -k 8000/tcp 2>/dev/null
        fuser -k 3000/tcp 2>/dev/null
    fi
    pkill -f "python -m src.main" 2>/dev/null
    # pkill -f "auto_backup_sender.py" 2>/dev/null
    
    # Remove lock do Qdrant se sobrar
    rm -f ./database/face_database/.lock 2>/dev/null
    
    echo -e "${GREEN}Todos os serviços locais foram desligados.${NC}"
    exit
}

# Captura o sinal de interrupção (Ctrl+C)
trap cleanup SIGINT SIGTERM

# Mantém o script rodando
wait
