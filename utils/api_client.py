import requests
from typing import List, Dict, Optional


def send_chat_request(history: List[Dict[str, str]], model: str = "gemma:2b",
                       endpoint: str = "http://localhost:11434/v1/chat/completions",
                       api_key: Optional[str] = None) -> str:
    """Verilen geçmişe göre modeli çağırıp yanıt döndürür."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {"model": model, "messages": history, "stream": False}

    resp = requests.post(endpoint, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    if "response" in data:
        return data["response"]
    raise RuntimeError("Geçersiz API yanıtı")
