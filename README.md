# vigIA-face

Sistema de reconhecimento facial para Raspberry Pi 5 com suporte a múltiplas câmeras.

## 🚀 Instalação

### Passo 1: Configurar o Sistema

Execute o script de configuração do sistema:

```bash
chmod +x setup-vigia-face.sh
./setup-vigia-face.sh
```

**O que faz:**
- Atualiza o sistema
- Instala VS Code
- Remove apps desnecessários
- Configura Git
- Adiciona overlay da câmera
- Instala dependências do sistema

**⚠️ IMPORTANTE:** Reinicie o Raspberry Pi quando solicitado!

```bash
sudo reboot
```

### Passo 2: Clonar o Repositório

```bash
cd ~
git clone https://github.com/emerymoriconi/vigIA-face.git
cd vigIA-face
```

### Passo 3: Configurar o Ambiente Python

Após reiniciar, volte ao diretório do projeto:

```bash
cd ~/vigIA-face
chmod +x setup_venv.sh
./setup_venv.sh
```

**O que faz:**
- Cria ambiente virtual Python
- Compila Dlib (demora 5-10 minutos ⏱️)
- Instala todas as dependências do projeto

### Passo 4: Executar o Projeto

```bash
source .venv/bin/activate
python main.py
```

---

## Como Usar

1. **Selecione o modo de câmera**: Única ou Múltiplas
2. **Escolha o modo de processamento**: Local, Cenário 1 ou Cenário 2
3. **Configure resolução e FPS** conforme necessário
4. Clique em **"Aplicar Configurações"**

---

## 🔧 Modos de Processamento

- **Local**: Apenas detecção facial (sem reconhecimento)
- **Cenário 1**: Detecção local + Reconhecimento via API
- **Cenário 2**: Detecção e reconhecimento totalmente via API

---

## 📁 Estrutura do Projeto

```
vigIA-face/
├── detecao_facial/
|   ├── main.py                   
|   ├── camera.py                  
|   ├── gui.py                    
|   ├── api_client.py              
|   ├── algoritmos/               
├── setup-vigia-face.sh        # Config. do sistema
├── setup_venv.sh              # Config. do ambiente Python
└── requirements_rasp.txt      # Dependências Python
```
