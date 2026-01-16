#!/usr/bin/env python3
"""
Script para testar headers no Replit e ver o que a Amazon está retornando
Execute isso no terminal do Replit para diagnosticar
"""

import requests
from bs4 import BeautifulSoup
import json

# Teste 1: Headers básicos (atual)
print("=" * 60)
print("TESTE 1: Headers básicos (atual)")
print("=" * 60)
headers1 = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

try:
    r = requests.get('https://www.amazon.com/dp/B08N5WRWNW', headers=headers1, timeout=10)
    soup = BeautifulSoup(r.content, 'html.parser')
    price_blocks = soup.select('#corePriceDisplay_desktop_feature_div, #corePrice_feature_div')
    print(f'Status: {r.status_code}')
    print(f'Blocos de preço encontrados: {len(price_blocks)}')
    print(f'HTML sample: {str(soup.select_one("#corePriceDisplay_desktop_feature_div"))[:200] if price_blocks else "NENHUM BLOCO ENCONTRADO"}')
except Exception as e:
    print(f'Erro: {e}')

# Teste 2: Headers completos (como no código)
print("\n" + "=" * 60)
print("TESTE 2: Headers completos (como no bot)")
print("=" * 60)
headers2 = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'Referer': 'https://www.google.com/',
}

try:
    session = requests.Session()
    session.headers.update(headers2)
    r = session.get('https://www.amazon.com/dp/B08N5WRWNW', timeout=10, allow_redirects=True)
    soup = BeautifulSoup(r.content, 'html.parser')
    price_blocks = soup.select('#corePriceDisplay_desktop_feature_div, #corePrice_feature_div')
    print(f'Status: {r.status_code}')
    print(f'Blocos de preço encontrados: {len(price_blocks)}')
    print(f'URL final: {r.url[:100]}')
    print(f'HTML sample: {str(soup.select_one("#corePriceDisplay_desktop_feature_div"))[:200] if price_blocks else "NENHUM BLOCO ENCONTRADO"}')
except Exception as e:
    print(f'Erro: {e}')

# Teste 3: Verificar se há JSON-LD com preços
print("\n" + "=" * 60)
print("TESTE 3: Buscar preços em JSON-LD")
print("=" * 60)
try:
    r = requests.get('https://www.amazon.com/dp/B08N5WRWNW', headers=headers2, timeout=10)
    soup = BeautifulSoup(r.content, 'html.parser')
    scripts = soup.find_all('script', type='application/ld+json')
    prices_found = []
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if 'offers' in data:
                    offers = data['offers']
                    if isinstance(offers, dict) and 'price' in offers:
                        prices_found.append(offers['price'])
                    elif isinstance(offers, list) and len(offers) > 0:
                        if 'price' in offers[0]:
                            prices_found.append(offers[0]['price'])
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'offers' in item:
                        offers = item['offers']
                        if isinstance(offers, dict) and 'price' in offers:
                            prices_found.append(offers['price'])
        except:
            continue
    print(f'Preços encontrados em JSON-LD: {prices_found}')
except Exception as e:
    print(f'Erro: {e}')

# Teste 4: Verificar User-Agent que a Amazon está vendo
print("\n" + "=" * 60)
print("TESTE 4: Verificar IP e headers enviados")
print("=" * 60)
try:
    r = requests.get('https://httpbin.org/headers', headers=headers2, timeout=10)
    print(f'Headers que o servidor vê: {json.dumps(r.json(), indent=2)}')
except Exception as e:
    print(f'Erro: {e}')

print("\n" + "=" * 60)
print("DIAGNÓSTICO COMPLETO")
print("=" * 60)
