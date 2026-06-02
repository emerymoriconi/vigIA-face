import requests
import os
from dotenv import load_dotenv

def inspect():
    """Consulta estatísticas e lista de pessoas do banco via API."""
    load_dotenv()
    api_key = os.getenv("VITE_VIGIA_API_KEY")
    url = "http://localhost:8000/db_inspect"
    headers = {"X-API-Key": api_key}
    
    print("\n--- STATUS DO BANCO VIGIA-FACE ---")

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()

        print(f"Total de faces no banco: {data.get('total', 0)}")
        print("-" * 30)

        people = data.get('people', [])
        if not people:
            print("Nenhuma pessoa listada ou detalhes não enviados.")
        else:
            for p in people:
                print(f"Nome: {p.get('nome', 'N/A')} | CPF: {p.get('cpf', 'N/A')} | Nasc: {p.get('nascimento', 'N/A')}")

        backups = data.get('backups', [])
        if backups:
            print("\nÚLTIMOS BACKUPS:")
            for b in backups[:3]:
                print(f" - {b['filename']} ({b['status']})")

    except Exception as e:
        print(f"Erro ao conectar ou processar dados: {e}")

if __name__ == "__main__":
    inspect()
