#!/bin/bash

# setup_venv.sh
# Script de configuração automática para Raspberry Pi 5 (Bookworm)
# Projeto: vigIA-face (Picamera2 + Dlib + YOLO + Tkinter)

# Interrompe o script se qualquer comando der erro
set -e

echo "=========================================================="
echo " INICIANDO CONFIGURAÇÃO DO AMBIENTE VIGIA-FACE (RPi 5)"
echo "=========================================================="

# 1. ATUALIZAÇÃO E DEPENDÊNCIAS DO SISTEMA (APT)
echo ""
echo "[1/4] Instalando dependências do sistema (root)..."
echo "      Isso inclui bibliotecas gráficas e ferramentas para compilar o Dlib."

sudo apt update

# python3-pil.imagetk python3-tk: Necessários para a GUI (o erro do ImageTk)
# build-essential cmake ...: Necessários para compilar o Dlib localmente
sudo apt install -y \
    python3-pil.imagetk \
    python3-tk \
    python3-dev \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev

# 2. CRIAÇÃO DO AMBIENTE VIRTUAL
echo ""
echo "[2/4] Configurando Ambiente Virtual Python..."

# Remove ambiente antigo se existir para garantir uma instalação limpa
if [ -d ".venv" ]; then
    echo "      Removendo ambiente .venv antigo..."
    rm -rf .venv
fi

# --system-site-packages: O PULO DO GATO.
# Permite que o ambiente veja o 'picamera2' e o 'rpi-lgpio' instalados no sistema.
python3 -m venv --system-site-packages .venv

echo "      Ambiente .venv criado com sucesso."

# 3. ATIVAÇÃO DO AMBIENTE
source .venv/bin/activate
echo "      Ambiente ativado."

# Atualiza o pip do ambiente para evitar avisos
pip install --upgrade pip

# 4. INSTALAÇÃO DAS DEPENDÊNCIAS VIA REQUIREMENTS
echo ""
echo "[3/4] Instalando dependências do requirements_rasp.txt..."
echo "      ATENÇÃO: A compilação do Dlib no Raspberry Pi 5 leva de 5 a 10 minutos."
echo "      O cooler pode acelerar. Não desligue!"

# Verifica se o arquivo requirements existe
if [ ! -f "requirements_rasp.txt" ]; then
    echo "ERRO: Arquivo requirements_rasp.txt não encontrado!"
    exit 1
fi

# Instala todas as dependências do arquivo requirements
pip install -r requirements_rasp.txt

echo ""
echo "=========================================================="
echo " CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!"
echo "=========================================================="
echo ""
echo "Para rodar seu projeto:"
echo "  1. source .venv/bin/activate"
echo "  2. python main.py"
echo ""
echo "Pacotes instalados:"
pip list | grep -E "(numpy|opencv|ultralytics|dlib|face-recognition|psutil|requests|python-dotenv)"
echo ""