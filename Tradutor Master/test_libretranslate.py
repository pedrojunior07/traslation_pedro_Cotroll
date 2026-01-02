# -*- coding: utf-8 -*-
"""Teste rápido do LibreTranslate"""
import requests
import json

# Teste 1: Tradução simples
print("=" * 60)
print("TESTE 1: Tradução simples (Hello world)")
print("=" * 60)

url = "http://102.211.186.44:5000/translate"
payload = {
    "q": "Hello world",
    "source": "en",
    "target": "pt"
}

print(f"\nEnviando para: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}\n")

try:
    response = requests.post(url, json=payload, timeout=15)
    print(f"Status HTTP: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}\n")

    data = response.json()
    print(f"Response JSON: {json.dumps(data, indent=2, ensure_ascii=False)}")

    translated = data.get("translatedText", "")
    print(f"\nTRADUCAO: '{translated}'")
    print(f"ENCODING OK: {translated == 'Olá, mundo'}")

except Exception as e:
    print(f"ERRO: {e}")

# Teste 2: Tradução em lote
print("\n" + "=" * 60)
print("TESTE 2: Tradução em lote (3 textos)")
print("=" * 60)

payload_batch = {
    "q": ["Hello", "Good morning", "Thank you"],
    "source": "en",
    "target": "pt"
}

print(f"\nEnviando para: {url}")
print(f"Payload: {json.dumps(payload_batch, indent=2)}\n")

try:
    response = requests.post(url, json=payload_batch, timeout=15)
    print(f"Status HTTP: {response.status_code}")

    data = response.json()
    print(f"Response JSON: {json.dumps(data, indent=2, ensure_ascii=False)}")

    if isinstance(data, list):
        print(f"\nTRADUCOES:")
        for i, item in enumerate(data):
            translation = item.get("translatedText", "")
            print(f"  {i+1}. '{payload_batch['q'][i]}' -> '{translation}'")
    else:
        print(f"\nFormato inesperado: {type(data)}")

except Exception as e:
    print(f"ERRO: {e}")

print("\n" + "=" * 60)
print("TESTE COMPLETO")
print("=" * 60)
