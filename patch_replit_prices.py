#!/usr/bin/env python3
"""
PATCH PARA REPLIT - Melhora extração de preços
Execute isso no Replit ANTES de iniciar o bot
Ou adicione no início do bot_with_edit.py apenas no Replit
"""

import re
import json

def patch_extractors_for_replit():
    """Aplica patch no extrator para melhorar busca de preços no Replit"""
    
    # Importar o extrator
    from extractors import SiteSpecificExtractor
    
    # Salvar método original
    original_extract_amazon_prices = SiteSpecificExtractor._extract_amazon_prices
    
    def improved_extract_amazon_prices(self, soup):
        """Versão melhorada que busca preços em mais lugares"""
        prices = []
        
        # Método 1: Blocos originais (tentar primeiro)
        for block_selector in ['#corePriceDisplay_desktop_feature_div', '#corePrice_feature_div', '#apex_desktop']:
            prices = self._extract_prices_from_block(soup, block_selector)
            if prices:
                break
        
        # Método 2: Buscar em spans com classe de preço (mais genérico)
        if not prices:
            price_spans = soup.select('span.a-price, span.a-price-whole, .a-price .a-offscreen, span[data-a-color="price"]')
            for span in price_spans:
                text = span.get_text(strip=True)
                val = self._extract_price_value(text)
                if val is not None and val > 0:
                    prices.append(val)
        
        # Método 3: Buscar em qualquer elemento com "$" seguido de número
        if not prices:
            # Buscar padrões de preço no texto
            all_text = soup.get_text()
            price_patterns = [
                r'\$\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',  # $19.99
                r'\$\s*(\d+\.\d{2})',  # $19.99
                r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})\s*USD',  # 19.99 USD
            ]
            for pattern in price_patterns:
                matches = re.findall(pattern, all_text)
                for match in matches:
                    val = self._extract_price_value(match)
                    if val is not None and val > 0 and val < 10000:  # Preços razoáveis
                        prices.append(val)
        
        # Método 4: Buscar em scripts JavaScript (Amazon às vezes coloca preços aqui)
        if not prices:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Buscar padrões de preço em scripts
                    script_text = script.string
                    # Procurar por "price": 19.99 ou "amount": 19.99
                    price_matches = re.findall(r'["\']price["\']\s*:\s*["\']?(\d+\.?\d*)', script_text, re.IGNORECASE)
                    price_matches += re.findall(r'["\']amount["\']\s*:\s*["\']?(\d+\.?\d*)', script_text, re.IGNORECASE)
                    for match in price_matches:
                        try:
                            val = float(match)
                            if val > 0 and val < 10000:
                                prices.append(val)
                        except:
                            pass
        
        # Método 5: Buscar em data attributes
        if not prices:
            elements_with_price = soup.select('[data-price], [data-a-price], [data-asin-price]')
            for elem in elements_with_price:
                for attr in ['data-price', 'data-a-price', 'data-asin-price']:
                    price_str = elem.get(attr)
                    if price_str:
                        val = self._extract_price_value(price_str)
                        if val is not None and val > 0:
                            prices.append(val)
        
        # Método 6: Fallback original
        if not prices:
            texts = [
                self._get_price_by_selectors(soup, ['span.priceToPay span.a-offscreen']),
                self._get_price_by_selectors(soup, ['#priceblock_dealprice', '#priceblock_saleprice', '#priceblock_ourprice']),
                self._get_price_by_selectors(soup, ['.a-price-whole']),
                self._get_price_by_selectors(soup, ['span[class*="price"]']),
            ]
            for txt in texts:
                val = self._extract_price_value(txt) if txt else None
                if val is not None:
                    prices.append(val)
        
        if not prices:
            return {'current': 0, 'original': 0, 'discount_percent': 0}
        
        # Remover duplicatas e valores muito pequenos
        prices = list(set(prices))
        prices = [p for p in prices if p >= 0.01]  # Preços mínimos
        
        if not prices:
            return {'current': 0, 'original': 0, 'discount_percent': 0}
        
        # Remover "preço por unidade" (ex.: $4.75/count) que normalmente é muito menor
        max_price = max(prices)
        filtered = [p for p in prices if p >= max_price * 0.30]
        candidates = filtered or prices
        
        current_price = min(candidates)
        original_price = max(candidates)
        
        return self._parse_prices(str(current_price), str(original_price))
    
    # Aplicar patch
    SiteSpecificExtractor._extract_amazon_prices = improved_extract_amazon_prices
    
    print("✅ Patch aplicado! Extração de preços melhorada para Replit.")
    return True

if __name__ == '__main__':
    patch_extractors_for_replit()
