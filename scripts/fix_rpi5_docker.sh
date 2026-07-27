#!/bin/bash

# Script para otimizar o Kernel do Raspberry Pi 5 (forçar páginas de 4KB)
# Necessário para compatibilidade com Qdrant (Docker) e outros binários otimizados.

CONFIG_FILE="/boot/firmware/config.txt"
REBOOT_NEEDED=0

echo "--- Verificando otimização do Kernel (RPi5) ---"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Erro: $CONFIG_FILE não encontrado. Este script deve ser executado em um Raspberry Pi."
    exit 1
fi

if grep -q "^kernel=kernel8.img" "$CONFIG_FILE"; then
    echo "Kernel já está otimizado (4KB pages)."
else
    echo "Aplicando correção kernel=kernel8.img..."
    sudo cp "$CONFIG_FILE" "$CONFIG_FILE.bak"
    
    if grep -q "^\[all\]" "$CONFIG_FILE"; then
        sudo sed -i '/^\[all\]/a kernel=kernel8.img' "$CONFIG_FILE"
    else
        echo -e "\n[all]\nkernel=kernel8.img" | sudo tee -a "$CONFIG_FILE" > /dev/null
    fi
    
    echo "Otimização aplicada com sucesso."
    REBOOT_NEEDED=1
fi

if [ $REBOOT_NEEDED -eq 1 ]; then
    echo "IMPORTANTE: Reinicie o sistema para aplicar as mudanças: sudo reboot"
    exit 10 # Código customizado para indicar que o reboot é necessário
fi

exit 0
