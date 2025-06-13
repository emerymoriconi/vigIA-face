# Projeto de Reconhecimento Facial

Este projeto visa desenvolver um sistema de reconhecimento facial utilizando câmeras e processamento de imagem.

---

## Funcionalidades Principais

* **Interface de Vídeo Adaptativa:** Desenvolver interface compatível com a tela da Raspberry Pi e exibir o feed da câmera. A interface permitirá o ajuste de largura, altura e FPS (frames por segundo) do vídeo.
* **Pipeline de Processamento:** Projetar um fluxo que inclua captura de vídeo, detecção, filtros, reconhecimento e exibição/log.
* **Otimização de Imagem (Filtros):**
    * Cálculo de ângulo mínimo da face para garantir visibilidade dos olhos e boca, com estudo de limiares.
    * Filtro para descartar falsos positivos (não-faces) usando modelo auxiliar ou heurísticas.
    * Análise de nitidez (`sharpness`) da face detectada e descarte de faces abaixo do limiar de qualidade visual.
    * Verificação de tamanho mínimo da face (largura × altura em pixels) e descarte automático de faces menores.
* **Detecção de Atributos:**
    * Implementação de detecção de sexo utilizando modelo leve.
    * Implementação de detecção de cor/raça, avaliando modelos compatíveis com restrições de performance.

---

## Ambiente de Desenvolvimento

* **Raspberry Pi:** Setup de testes, incluindo instalação de bibliotecas, drivers de câmera e preparação de ambiente com consumo otimizado.

---

## Como Rodar

(Instruções de instalação e execução serão adicionadas aqui após a implementação.)

---
