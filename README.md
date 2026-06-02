# Vigia-Face v1.1: Monitoramento Biométrico de Alta Performance

Vigia-Face é um ecossistema de monitoramento biométrico facial otimizado para hardware de borda (Edge Computing), com foco total na **Raspberry Pi 5**. O sistema combina detecção ultra-rápida, reconhecimento preciso com embeddings de 512 dimensões e uma interface moderna para gestão em tempo real.

---

## 🛠 Arquitetura e Tech Stack

### 1. Backend (IA & Processamento)
*   **Linguagem:** Python 3.11+ gerenciado via `uv`.
*   **Framework:** FastAPI (Assíncrono) para API REST e WebSockets.
*   **Engine de Inferência:** ONNX Runtime (otimizado para ARM64 com instruções NEON).
*   **Pipeline de IA:**
    *   **Detecção:** SCRFD (Sample and Computation Redistribution for Face Detection) - Otimizado para alta taxa de quadros.
    *   **Reconhecimento:** ArcFace (Additive Angular Margin Loss) - Alta precisão em diversas condições de iluminação.
*   **Armazenamento:**
    *   **Vetorial:** Qdrant (Local Mode) - Busca por similaridade cosseno em milissegundos.
    *   **Relacional:** SQLite - Persistência de logs de identificação, histórico de hardware e metadados.

### 2. Frontend (Dashboard Operacional)
*   **Core:** React 18, TypeScript, Vite.
*   **Estilização:** Tailwind CSS (Design Industrial de baixa fadiga visual).
*   **Comunicação:** WebSockets de baixa latência para transmissão de frames e metadados de detecção (OSD).
*   **Recursos:** Dashboard responsivo com suporte a PWA (instalável em dispositivos móveis).

---

## 🚀 Funcionalidades Principais

*   **Monitoramento em Tempo Real:** Transmissão de vídeo via WebSocket com overlay de detecção facial (bounding boxes) e taxa de FPS dinâmica.
*   **Identificação Instantânea:** Cruzamento automático de faces detectadas com o banco de dados vetorial.
*   **Gestão de Hardware:** Telemetria em tempo real da Raspberry Pi 5 (CPU, RAM, Temperatura e status da câmera).
*   **Cadastro Multi-Modal:** Registro de novas faces via upload de imagem ou captura direta do fluxo de vídeo.
*   **Histórico Detalhado:** Registro fotográfico de todas as identificações com timestamp, nível de confiança da IA e metadados do indivíduo.
*   **Auditoria e Logs:** Sistema de logs rotativos com marcação de auditoria para conformidade e segurança.
*   **Ecossistema de Backup:** Suporte a geração de backups locais em ZIP e sincronização com servidores externos.

---

## 📋 Requisitos de Hardware

*   **Principal:** Raspberry Pi 5 (Recomendado 4GB+ RAM).
*   **Câmera:** 
    *   Câmera CSI Oficial (Pi Camera v2/v3) - Suporte nativo via `libcamera`.
    *   Câmeras USB (UVC Compliant) - Suporte via OpenCV.
*   **Armazenamento:** Cartão SD Classe 10 de alta velocidade (Recomendado 32GB+).
*   **Refrigeração:** Cooler ativo é altamente recomendado devido ao processamento intensivo de IA.

---

## ⚙️ Instalação e Configuração

### 1. Preparação do Ambiente
O sistema utiliza o gerenciador `uv` para garantir máxima performance e isolamento.

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/vigia-face-rasp.git
cd vigia-face-rasp

# Execute o script de setup automático
chmod +x setup.sh
./setup.sh
```
O `setup.sh` irá:
- Instalar dependências de sistema (`libcamera`, `ffmpeg`, etc).
- Configurar o ambiente virtual Python.
- Baixar os pesos dos modelos ONNX automaticamente.
- Instalar as dependências do frontend (Node.js/NPM).

### 2. Variáveis de Ambiente (`.env`)
O sistema utiliza um arquivo `.env` na raiz para centralizar todas as configurações. Abaixo, o detalhamento das variáveis disponíveis:

#### 🔐 Segurança e Identidade
*   **`VIGIA_API_KEY`**: Chave de autenticação obrigatória. Deve ser enviada no header `X-API-Key` para chamadas REST e como parâmetro na URL para conexões WebSocket. Garante que apenas clientes autorizados acessem o stream e os dados.
*   **`VIGIA_MASTER_KEY`**: Chave de criptografia simétrica (Fernet). **Crítica:** É usada para criptografar/descriptografar metadados sensíveis (como CPFs e Nomes) no banco de dados e arquivos de metadata. Pode ser gerada via Python: `from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())`.
*   **`VIGIA_DEVICE_ID`**: Nome identificador deste dispositivo (ex: `POSTO-01`). Se omitido, usará o *hostname* da Raspberry Pi. Útil para centralizar logs de múltiplos dispositivos.

#### 🧠 Inteligência Artificial (Ajuste Fino)
*   **`AI_THRESHOLD`**: (Padrão: `0.45`) Limiar de confiança para o reconhecimento facial.
    *   *Valores menores:* Mais permissivo (pode gerar falsos positivos).
    *   *Valores maiores:* Mais rigoroso (exige maior clareza da face).
*   **`HISTORY_COOLDOWN`**: (Padrão: `60`) Intervalo em segundos para evitar registros duplicados da mesma pessoa no histórico. Se a mesma pessoa permanecer em frente à câmera, um novo registro só será salvo após este tempo.

#### 🗄 Armazenamento e Modelos
*   **`QDRANT_PATH`**: Caminho onde o banco de dados vetorial será armazenado localmente.
*   **`QDRANT_VOLUME_LIMIT_GB`**: (Padrão: `5.0`) Limite de espaço em disco reservado para o banco de faces. Ajuda a prevenir o preenchimento total do cartão SD.
*   **`DETECTOR_MODEL` / `RECOGNIZER_MODEL`**: Caminhos para os arquivos `.onnx`. Permite trocar as versões dos modelos SCRFD ou ArcFace sem alterar o código.

#### 🛠 Desenvolvimento e Outros
*   **`VIGIA_ENABLE_DOCS`**: (`true`/`false`) Habilita ou desabilita a interface Swagger da API em `/docs`. Recomendado manter `false` em produção.
*   **`QDRANT_HOST` / `QDRANT_PORT`**: Configurações de rede para o banco vetorial (usado internamente).

Exemplo de arquivo `.env` completo:
```env
VIGIA_API_KEY=sua_chave_secreta_aqui
VIGIA_MASTER_KEY=sua_chave_fernet_gerada
VIGIA_DEVICE_ID=RPi5-Vigia-01
AI_THRESHOLD=0.48
HISTORY_COOLDOWN=120
VIGIA_ENABLE_DOCS=false
```

---

## 🚦 Operação do Sistema

### Inicialização Integrada
Para rodar o backend e o frontend simultaneamente:
```bash
chmod +x run_vigia_face.sh
./run_vigia_face.sh
```

### Comandos Manuais
*   **Backend:** `source .venv/bin/activate && python src/main.py`
*   **Frontend:** `cd app && npm run dev`

---

## 📂 Estrutura do Projeto

```text
vigia-face-rasp/
├── app/                 # Frontend (React + Vite)
├── src/                 # Código-fonte Python
│   ├── api/             # Endpoints (Routes, Stream/WS)
│   ├── core/            # Engines (IA, Câmera, Estado do Sistema)
│   ├── database/        # Camada de Dados (Qdrant, SQLite)
│   ├── utils/           # Utilitários (Logs, Formatação, Helpers)
│   ├── config.py        # Configurações globais
│   └── main.py          # Ponto de entrada do Backend
├── models/              # Lógica de carregamento dos modelos SCRFD/ArcFace
├── weights/             # Arquivos .onnx dos modelos de IA
├── database/            # Armazenamento local (History, Qdrant Storage)
├── assets/              # Fotos de rostos cadastrados e metadados
└── logs/                # Arquivos de log operacionais (AUDITORIA)
```

---

## 🔒 Segurança e Privacidade

- **Criptografia:** Metadados sensíveis (CPF, Nome) são criptografados em repouso usando Fernet.
- **Isolamento:** O banco de dados vetorial opera em modo local, sem envio de biometria para a nuvem.
- **Autenticação:** Endpoints da API e conexões WebSocket são protegidos via `VIGIA_API_KEY`.
- **Privacidade por Design:** O sistema permite desabilitar a inferência de IA via dashboard a qualquer momento.

---

## 📡 API (Principais Endpoints)

- `GET /api/status`: Status de hardware e câmera.
- `POST /api/register`: Cadastro de nova face (Multipart Form).
- `GET /api/history`: Lista histórico de detecções.
- `GET /api/logs`: Visualização em tempo real dos logs de auditoria.
- `POST /api/backup`: Gera snapshot completo do sistema.

---

## 📦 Migração e Restauração de Dados

Para mover o sistema de uma Raspberry Pi para outra sem perder o banco de faces cadastrado, siga o procedimento de **Snapshot** do Qdrant:

### 1. Criar Snapshot (Na máquina de Origem)
Com o sistema rodando, execute o comando abaixo para gerar um backup completo da coleção de faces:
```bash
curl -X POST http://localhost:6333/collections/faces/snapshots
```
O arquivo `.snapshot` (aprox. 6.5 GB para 1.7M faces) será gerado na pasta:
`database/qdrant_snapshots/`

### 2. Preparar Máquina de Destino
1.  Siga o processo normal de **Instalação** (`./setup.sh`) na nova Raspberry Pi.
2.  Inicie o sistema uma vez (`./run_vigia_face.sh`) para garantir que os containers sejam criados e pare-o com `Ctrl+C`.

### 3. Transferir e Restaurar
1.  Copie o arquivo `.snapshot` da máquina antiga para a mesma pasta `database/qdrant_snapshots/` na máquina nova.
2.  Inicie o sistema novamente: `./run_vigia_face.sh`.
3.  **Via Terminal (Recomendado):**
    Execute o comando de restauração (substitua pelo nome real do seu arquivo):
    ```bash
    curl -X POST http://localhost:6333/collections/faces/snapshots/restore \
    -H 'Content-Type: application/json' \
    -d '{"location": "NOME_DO_ARQUIVO.snapshot"}'
    ```
4.  **Via Dashboard:**
    Acesse `http://localhost:6333/dashboard`, vá em **Collections** -> **faces** -> **Snapshots** e clique no botão **Restore** ao lado do arquivo transferido.

> **Nota:** Se houver erro de permissão ao criar snapshots, rode: `sudo chmod -R 777 database/qdrant_snapshots`.

---
**Vigia-Face** - Monitoramento inteligente para um mundo conectado.
