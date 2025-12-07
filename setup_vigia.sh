# chmod +x setup_vigia.sh
# ./setup_vigia.sh

#!/bin/bash

# setup_vigia.sh
# Script de configuração automática para Raspberry Pi 5 (Bookworm)
# Projeto: vigIA-face (Picamera2 + Dlib + YOLO + Tkinter)

# Interrompe o script se qualquer comando der erro
set -e

echo "=========================================================="
echo " INICIANDO CONFIGURAÇÃO DO AMBIENTE VIGIA-FACE (RPi 5)"
echo "=========================================================="

# 1. ATUALIZAÇÃO E DEPENDÊNCIAS DO SISTEMA (APT)
echo ""
echo "[1/5] Instalando dependências do sistema (root)..."
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
echo "[2/5] Configurando Ambiente Virtual Python..."

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

# 4. COMPILAÇÃO DO DLIB
echo ""
echo "[3/5] Instalando Dlib (Compilação)..."
echo "      ATENÇÃO: No Raspberry Pi 5, isso deve levar de 5 a 10 minutos."
echo "      O cooler pode acelerar. Não desligue!"

pip install dlib

# 5. INSTALAÇÃO DAS BIBLIOTECAS FINAIS (COM TRAVAS DE VERSÃO)
echo ""
echo "[4/5] Instalando Face Recognition, YOLO e OpenCV..."
echo "      Aplicando travas de versão para manter compatibilidade com Picamera2."

# face_recognition: Biblioteca de reconhecimento facial
# ultralytics: YOLO
# numpy<2: Vital para não quebrar o picamera2 (evita erro de binary incompatibility)
# opencv-python<4.10: Vital para funcionar com numpy antigo
pip install face_recognition
pip install ultralytics "numpy<2" "opencv-python<4.10"

echo ""
echo "=========================================================="
echo " CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!"
echo "=========================================================="
echo ""
echo "Para rodar seu projeto:"
echo "  1. source .venv/bin/activate"
echo "  2. python main.py"
echo ""