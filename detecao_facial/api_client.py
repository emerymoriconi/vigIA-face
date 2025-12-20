# /vigIA-face-dblibyollo-Rasp/api_client.py

import requests
import json

# --- CONFIGURAÇÃO ---

API_BASE_URL = "http://192.168.18.242:8000/api/v1" 
#API_BASE_URL = "http://192.168.0.193:8000/api/v1" 
# Mude para o token da sua API (do .env.example)
BEARER_TOKEN = "aBc1D2eF3gH4iJ5kL6mN7pQ8rS9tU0vW"
# --------------------

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

def recognize_embedding(embedding_vector: list):
    """
    CENÁRIO 3: Envia o vetor de embedding JÁ CALCULADO para o endpoint de comparação.
    """
    
    # Endpoint otimizado: O servidor só precisa fazer o matching no banco de dados.
    url = f"{API_BASE_URL}/recognize/recognize_vector/" 
    
    # O payload será o vetor em formato JSON
    payload = {
        'embedding': embedding_vector
    }
    
    try:
        # Requisição POST com JSON (muito menor que files/multipart)
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30) 
         
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print("API Client: Vetor não reconhecido pela API.")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"API Client: Erro de conexão - {e}")
        return None

def recognize_cropped_face(image_bytes: bytes):
    """
    Envia um rosto JÁ RECORTADO para o endpoint de reconhecimento.
    
    Args:
        image_bytes: Os bytes da imagem (em formato .jpg).
    
    Returns:
        Um dict com os dados da pessoa (ex: PersonOutput) ou None se falhar.
    """
    
    # Este é o endpoint otimizado que sugerimos criar no servidor
    url = f"{API_BASE_URL}/recognize/recognize_cropped/"
    
    files = {
        'image': ('face.jpg', image_bytes, 'image/jpeg')
    }
    
    try:
        response = requests.post(url, headers=HEADERS, files=files, timeout=30) # Timeout de 30s
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print("API Client: Rosto não reconhecido pela API.")
            return None
        else:
            print(f"API Client Erro {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"API Client: Erro de conexão - {e}")
        return None

def recognize_full_frame(image_bytes: bytes):
    """
    Envia um FRAME INTEIRO para detecção e reconhecimento (CENÁRIO 2).
    """
    
    # Endpoint padrão que RODA O YOLO
    url = f"{API_BASE_URL}/recognize/" 
    
    files = {
        'image': ('frame.jpg', image_bytes, 'image/jpeg')
    }
    
    try:
        # Aumenta o timeout, pois a API vai demorar mais (detecção + reconhecimento)
        response = requests.post(url, headers=HEADERS, files=files, timeout=10) 
        
        if response.status_code == 200:
            # Retorna o JSON que agora contém a 'bbox'
            return response.json() 
        elif response.status_code == 404:
            # Pode ser "No faces detected" ou "Face not recognized"
            print(f"API Client (C2): 404 - {response.json().get('detail')}")
            return None
        else:
            print(f"API Client (C2) Erro {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"API Client (C2): Erro de conexão - {e}")
        return None