#!/usr/bin/env python3
"""
Script de aquecimento de sessão para o Replit
Execute isso ANTES de iniciar o bot para "aquecer" a sessão com a Amazon
"""

import requests
import time
import random

def warmup_amazon_session():
    """Aquece a sessão fazendo requisições iniciais para parecer mais humano"""
    
    session = requests.Session()
    
    # Headers mais conservadores (menos "bot-like")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    session.headers.update(headers)
    
    print("🔥 Aquecendo sessão com Amazon...")
    
    # Passo 1: Visitar página inicial da Amazon (como um humano faria)
    try:
        print("1. Visitando página inicial...")
        r = session.get('https://www.amazon.com', timeout=10)
        print(f"   ✓ Status: {r.status_code}")
        time.sleep(random.uniform(1, 2))
    except Exception as e:
        print(f"   ✗ Erro: {e}")
    
    # Passo 2: Visitar uma página de produto genérica (não a que vamos extrair)
    try:
        print("2. Visitando página de produto genérica...")
        r = session.get('https://www.amazon.com/dp/B08N5WRWNW', timeout=10)
        print(f"   ✓ Status: {r.status_code}")
        time.sleep(random.uniform(1, 2))
    except Exception as e:
        print(f"   ✗ Erro: {e}")
    
    # Passo 3: Verificar se consegue ver blocos de preço agora
    try:
        print("3. Testando extração de preço...")
        from bs4 import BeautifulSoup
        r = session.get('https://www.amazon.com/dp/B08N5WRWNW', timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        price_blocks = soup.select('#corePriceDisplay_desktop_feature_div, #corePrice_feature_div')
        print(f"   ✓ Blocos encontrados: {len(price_blocks)}")
        
        if price_blocks:
            print("   ✅ SESSÃO AQUECIDA COM SUCESSO!")
            return True
        else:
            print("   ⚠️ Ainda não encontrou blocos, mas sessão foi criada")
            return False
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        return False
    
    return False

if __name__ == '__main__':
    warmup_amazon_session()
