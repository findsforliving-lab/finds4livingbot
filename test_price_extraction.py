#!/usr/bin/env python3
"""
Script para testar extração de preços no Replit
Execute para verificar se os preços estão sendo extraídos corretamente
"""

import requests
from bs4 import BeautifulSoup
import sys

# Aplicar patch primeiro
try:
    from patch_replit_prices_v2 import patch_extractors_for_replit_v2
    patch_extractors_for_replit_v2()
    print("✅ Patch V2 aplicado\n")
except:
    print("⚠️ Patch não aplicado, usando método original\n")

from extractors import SiteSpecificExtractor

def test_product(url):
    """Testa extração de um produto"""
    print("=" * 60)
    print(f"Testando: {url[:60]}...")
    print("=" * 60)
    
    # Headers simplificados para Replit
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, timeout=10, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        extractor = SiteSpecificExtractor()
        
        # Extrair dados
        data = extractor.extract(url, soup)
        
        print(f"✅ Título: {data.get('title', 'N/A')[:80]}...")
        print(f"💰 Preço atual: ${data.get('price', {}).get('current', 0):.2f}")
        print(f"💰 Preço original: ${data.get('price', {}).get('original', 0):.2f}")
        print(f"💥 Desconto: {data.get('price', {}).get('discount_percent', 0)}%")
        print(f"📸 Imagens: {len(data.get('images', []))}")
        
        # Verificar se o preço faz sentido
        current = data.get('price', {}).get('current', 0)
        original = data.get('price', {}).get('original', 0)
        
        if current == 0:
            print("❌ ERRO: Preço atual é $0.00")
        elif current < 1:
            print("⚠️ AVISO: Preço muito baixo (< $1.00), pode estar errado")
        elif current > 10000:
            print("⚠️ AVISO: Preço muito alto (> $10,000), pode estar errado")
        elif original > 0 and original < current:
            print("⚠️ AVISO: Preço original menor que atual, pode estar invertido")
        elif original > current * 5:
            print("⚠️ AVISO: Diferença muito grande entre preços, pode estar errado")
        else:
            print("✅ Preço parece correto!")
        
        return data
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    # Testar com alguns produtos
    test_urls = [
        'https://www.amazon.com/dp/B08N5WRWNW',  # Produto de teste
    ]
    
    # Se passar URL como argumento, testar essa
    if len(sys.argv) > 1:
        test_urls = [sys.argv[1]]
    
    for url in test_urls:
        test_product(url)
        print("\n")
