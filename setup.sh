#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}===> Iniciando Setup Completo do Vigia-Face (Otimizado RPi5) <===${NC}"

# 0. Garantir pastas base e otimização de kernel
echo -e "${BLUE}Preparando ambiente...${NC}"
mkdir -p assets/faces logs database/qdrant_storage weights
REBOOT_REQUIRED=false

if [ -f "scripts/fix_rpi5_docker.sh" ]; then
    chmod +x scripts/fix_rpi5_docker.sh
    ./scripts/fix_rpi5_docker.sh
    if [ $? -eq 10 ]; then
        REBOOT_REQUIRED=true
    fi
fi

# 1. Dependências do Sistema (Drivers de Câmera e Node.js)
echo -e "${BLUE}Verificando dependências de sistema...${NC}"
sudo apt update
sudo apt install -y python3-picamera2 libcamera-apps-lite v4l-utils

# Melhorar instalação do Node.js (NodeSource para garantir v20+)
if ! command -v node &> /dev/null || [ $(node -v | cut -d'v' -f2 | cut -d'.' -f1) -lt 18 ]; then
    echo -e "${BLUE}Instalando/Atualizando Node.js v20 (necessário para Vite)...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
else
    echo -e "${GREEN}Node.js $(node -v) já está instalado.${NC}"
fi

# 1.1 Docker (Instalação oficial recomendada para RPi5/ARM64)
if ! command -v docker &> /dev/null; then
    echo -e "${BLUE}Instalando Docker oficial (método otimizado para RPi5)...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}Docker e Docker Compose instalados. Nota: Pode ser necessário reiniciar a sessão para usar Docker sem sudo.${NC}"
else
    echo -e "${GREEN}Docker já está instalado.${NC}"
fi

# 2. Instalar o uv (Gerenciador de pacotes Python ultra-rápido)
if ! command -v uv &> /dev/null; then
    echo -e "${BLUE}Instalando uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    [ -f "$HOME/.cargo/env" ] && source "$HOME/.cargo/env"
else
    echo -e "${GREEN}uv já está instalado.${NC}"
fi

# 3. Configurar ambiente virtual Python (com pacotes do sistema para Picamera2)
echo -e "${BLUE}Configurando ambiente virtual Python...${NC}"
rm -rf .venv
uv venv --system-site-packages
source .venv/bin/activate

# 4. Instalar dependências Python
echo -e "${BLUE}Instalando requisitos Python via uv...${NC}"
uv pip install -r requirements.txt

# 4.1 Criar .env padrão se não existir
if [ ! -f ".env" ]; then
    echo -e "${BLUE}Criando arquivo .env padrão...${NC}"
    # Tenta gerar a chave usando o python do venv que já tem cryptography
    MASTER_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "CHAVE_TEMPORARIA_GERAR_MANUALMENTE")
    API_KEY=$(openssl rand -hex 16 2>/dev/null || echo "api_key_$(date +%s)")
    
    cat <<EOF > .env
VIGIA_API_KEY=$API_KEY
VIGIA_MASTER_KEY=$MASTER_KEY
VIGIA_DEVICE_ID=RPi5-Vigia-$(hostname)
AI_THRESHOLD=0.45
HISTORY_COOLDOWN=60
VIGIA_ENABLE_DOCS=true
QDRANT_HOST=localhost
QDRANT_PORT=6333
EOF
    echo -e "${GREEN}.env criado com chaves geradas automaticamente.${NC}"
fi

# 5. Configurar Frontend (Instalar pacotes Node)
if [ -d "app" ]; then
    echo -e "${BLUE}Configurando dependências do Frontend (npm)...${NC}"
    cd app
    npm install
    cd ..
fi

# 6. Baixar pesos dos modelos (apenas se necessário)
MODELS_READY=true
for model in weights/det_10g.onnx weights/w600k_mbf.onnx; do
    if [ ! -f "$model" ]; then
        MODELS_READY=false
        break
    fi
done

if [ "$MODELS_READY" = true ]; then
    echo -e "${GREEN}Pesos dos modelos já encontrados. Pulando download.${NC}"
else
    if [ -f "scripts/download.sh" ]; then
        echo -e "${BLUE}Baixando pesos dos modelos ONNX...${NC}"
        chmod +x scripts/download.sh
        ./scripts/download.sh
    fi
fi

echo -e "${GREEN}===> Setup concluído com sucesso! <===${NC}"

if [ "$REBOOT_REQUIRED" = true ]; then
    echo -e "${BLUE}#######################################################${NC}"
    echo -e "${BLUE}#                                                     #${NC}"
    echo -e "${BLUE}#  IMPORTANTE: O Kernel foi otimizado para o RPi5.    #${NC}"
    echo -e "${BLUE}#  Você PRECISA reiniciar o sistema antes de rodar.   #${NC}"
    echo -e "${BLUE}#                                                     #${NC}"
    echo -e "${BLUE}#  Comando: sudo reboot                               #${NC}"
    echo -e "${BLUE}#                                                     #${NC}"
    echo -e "${BLUE}#######################################################${NC}"
else
    echo -e "\nPara iniciar o sistema:"
    echo -e "Use o script principal: ${BLUE}./run_vigia_face.sh${NC}"
fi
