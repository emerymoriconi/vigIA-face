#!/bin/bash

##############################################################################
# Script de Configuração Automática - Projeto vigIA-face
# Raspberry Pi 5 Setup
##############################################################################

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Banner
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║        🚀 Configuração Automática Raspberry Pi 5        ║"
echo "║                  Projeto vigIA-face                      ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Verificar se está rodando como usuário normal (não root)
if [ "$EUID" -eq 0 ]; then
    log_error "Este script NÃO deve ser executado como root!"
    log_info "Execute como usuário normal: ./setup-vigia-face.sh"
    exit 1
fi

log_info "Iniciando configuração do sistema..."
sleep 2

##############################################################################
# 1. ATUALIZAÇÃO COMPLETA DO SISTEMA
##############################################################################

log_info "Atualizando sistema operacional..."
sudo apt update
sudo apt upgrade -y
sudo apt full-upgrade -y
log_success "Sistema atualizado"

##############################################################################
# 2. INSTALAÇÃO DE DEPENDÊNCIAS BÁSICAS
##############################################################################

log_info "Instalando dependências básicas..."
sudo apt install -y \
    wget \
    gpg \
    curl \
    git \
    build-essential \
    cmake \
    pkg-config \
    libcap-dev \
    python3-dev \
    python3-pip
log_success "Dependências básicas instaladas"

##############################################################################
# 3. INSTALAÇÃO DO VSCODE
##############################################################################

log_info "Instalando Visual Studio Code..."

# Baixar e adicionar chave GPG
if [ ! -f "/etc/apt/keyrings/packages.microsoft.gpg" ]; then
    log_info "Adicionando chave GPG da Microsoft..."
    wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
    sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
    rm packages.microsoft.gpg
fi

# Adicionar repositório
if [ ! -f "/etc/apt/sources.list.d/vscode.list" ]; then
    log_info "Adicionando repositório do VSCode..."
    sudo sh -c 'echo "deb [arch=arm64 signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
fi

# Instalar VSCode
sudo apt update
sudo apt install -y code
log_success "VSCode instalado com sucesso"

##############################################################################
# 4. REMOÇÃO DE APLICATIVOS DESNECESSÁRIOS
##############################################################################

log_info "Removendo aplicativos desnecessários..."

# Lista de aplicativos para remover
APPS_TO_REMOVE=(
    "thonny"
    "geany"
    "wolfram-engine"
    "libreoffice*"
)

for app in "${APPS_TO_REMOVE[@]}"; do
    if dpkg -l | grep -q "^ii.*$app"; then
        log_info "Removendo $app..."
        sudo apt remove -y $app
        sudo apt purge -y $app
    else
        log_warning "$app não está instalado"
    fi
done

# Limpeza
sudo apt autoremove -y
sudo apt clean
log_success "Aplicativos desnecessários removidos"

##############################################################################
# 5. INSTALAÇÃO DE DEPENDÊNCIAS DO PROJETO vigIA-face
##############################################################################

log_info "Instalando dependências do projeto vigIA-face..."

sudo apt install -y \
    python3-picamera2 \
    python3-libcamera \
    python3-opencv \
    python3-numpy \
    python3-pil \
    libcamera-apps \
    libcamera-dev \
    libopenblas-dev \
    liblapack-dev \
    libatlas-base-dev
    
log_success "Dependências do projeto instaladas"

##############################################################################
# 6. CONFIGURAÇÃO DO GIT
##############################################################################

log_info "Configurando Git globalmente..."

# Definir usuário e email
git config --global user.name "raspvigia"
git config --global user.email "raspvigia@gmail.com"

# Configurações adicionais úteis
git config --global init.defaultBranch main
git config --global core.editor "code --wait"
git config --global pull.rebase false

# Verificar configuração
log_success "Git configurado:"
echo "  Nome: $(git config --global user.name)"
echo "  Email: $(git config --global user.email)"

##############################################################################
# 7. CONFIGURAÇÃO DA CÂMERA (IMX219)
##############################################################################

log_info "Configurando câmera IMX219..."

CONFIG_FILE="/boot/firmware/config.txt"
OVERLAY_LINE="dtoverlay=imx219"

# Verificar se o arquivo existe
if [ ! -f "$CONFIG_FILE" ]; then
    log_error "Arquivo $CONFIG_FILE não encontrado!"
    exit 1
fi

# Verificar se a linha já existe
if grep -q "^$OVERLAY_LINE" "$CONFIG_FILE"; then
    log_warning "Overlay da câmera IMX219 já está configurado"
else
    log_info "Adicionando overlay da câmera ao config.txt..."
    echo "" | sudo tee -a "$CONFIG_FILE" > /dev/null
    echo "# vigIA-face - Câmera IMX219" | sudo tee -a "$CONFIG_FILE" > /dev/null
    echo "$OVERLAY_LINE" | sudo tee -a "$CONFIG_FILE" > /dev/null
    log_success "Overlay da câmera adicionado ao $CONFIG_FILE"
fi

##############################################################################
# 8. VERIFICAÇÃO DE HARDWARE
##############################################################################

log_info "Verificando hardware disponível..."

# Verificar câmeras
if command -v libcamera-hello &> /dev/null; then
    echo ""
    log_info "Câmeras detectadas:"
    libcamera-hello --list-cameras 2>/dev/null || log_warning "Nenhuma câmera detectada (pode precisar de reboot)"
fi

# Informações do sistema
echo ""
log_info "Informações do sistema:"
echo "  Modelo: $(cat /proc/device-tree/model)"
echo "  Kernel: $(uname -r)"
echo "  Python: $(python3 --version)"
echo "  Git: $(git --version)"

##############################################################################
# 9. CRIAR ESTRUTURA DE PASTAS DO PROJETO
##############################################################################

log_info "Criando estrutura de pastas do projeto..."

# Diretório do projeto
PROJECT_DIR="$HOME/projetos"
mkdir -p "$PROJECT_DIR"
log_success "Estrutura de pastas criada em $PROJECT_DIR"

##############################################################################
# 10. RESUMO E PRÓXIMOS PASSOS
##############################################################################

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║        ✅ Configuração concluída com sucesso!           ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

log_success "Sistema configurado para o projeto vigIA-face"
echo ""
log_info "Próximos passos:"
echo ""
echo "  1. REINICIAR o sistema para ativar a câmera:"
echo "     sudo reboot"
echo ""
echo "  2. Clonar o repositório do projeto:"
echo "     cd ~/projetos"
echo "     git clone https://github.com/emerymoriconi/vigIA-face.git"
echo "     cd vigIA-face"
echo ""
echo "  3. Executar o script de configuração do ambiente Python:"
echo "     chmod +x setup_vigia.sh"
echo "     ./setup_vigia.sh"
echo ""
echo "  4. Executar o projeto:"
echo "     source .venv/bin/activate"
echo "     python main.py"
echo ""

log_warning "IMPORTANTE: Reinicie o sistema agora para ativar as configurações da câmera!"
echo ""
read -p "Deseja reiniciar agora? (s/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[SsYy]$ ]]; then
    log_info "Reiniciando sistema em 5 segundos..."
    sleep 5
    sudo reboot
else
    log_info "Lembre-se de reiniciar manualmente: sudo reboot"
fi

exit 0