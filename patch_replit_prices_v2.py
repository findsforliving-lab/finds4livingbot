#!/usr/bin/env python3
"""
PATCH V2 PARA REPLIT - Filtra preços incorretos e pega apenas o preço principal
Execute isso no Replit ANTES de iniciar o bot
"""

import re
import json

def patch_extractors_for_replit_v2():
    """Aplica patch melhorado que filtra preços incorretos"""
    
    from extractors import SiteSpecificExtractor
    
    original_extract_amazon_prices = SiteSpecificExtractor._extract_amazon_prices
    
    def improved_extract_amazon_prices_v2(self, soup):
        """Versão melhorada que filtra preços incorretos"""
        all_prices = []
        
        # Método 1: Blocos originais
        for block_selector in ['#corePriceDisplay_desktop_feature_div', '#corePrice_feature_div', '#apex_desktop']:
            prices = self._extract_prices_from_block(soup, block_selector)
            if prices:
                all_prices.extend(prices)
                break
        
        # Método 2: Buscar em spans com classe de preço (mas filtrar melhor)
        price_spans = soup.select('span.a-price, span.a-price-whole, .a-price .a-offscreen, span[data-a-color="price"], .a-price-range')
        for span in price_spans:
            # IGNORAR se estiver dentro de "price per unit" ou variações
            parent = span.find_parent()
            if parent:
                parent_text = parent.get_text().lower()
                # Ignorar preços por unidade
                if any(word in parent_text for word in ['per unit', 'per count', 'per oz', 'per lb', 'per pack', '/unit', '/count']):
                    continue
                # Ignorar se estiver em seção de variações
                if any(word in parent_text for word in ['variation', 'size', 'color', 'option']):
                    continue
            
            text = span.get_text(strip=True)
            val = self._extract_price_value(text)
            if val is not None and val > 0:
                all_prices.append(val)
        
        # Método 3: Buscar em elementos principais de preço (prioridade)
        main_price_selectors = [
            'span.priceToPay span.a-offscreen',
            '#priceblock_dealprice',
            '#priceblock_saleprice', 
            '#priceblock_ourprice',
            '.a-price-whole',
            '[data-a-color="price"] .a-offscreen',
            '.a-price .a-offscreen'
        ]
        for selector in main_price_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                val = self._extract_price_value(text)
                if val is not None and val > 0:
                    all_prices.append(val)
        
        # Método 4: Buscar em scripts JavaScript (filtrar melhor)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                script_text = script.string
                # Buscar apenas em contextos de preço principal
                # Procurar por padrões como "displayPrice": 19.99 ou "buyingPrice": 19.99
                price_patterns = [
                    r'["\']displayPrice["\']\s*:\s*["\']?(\d+\.?\d*)',
                    r'["\']buyingPrice["\']\s*:\s*["\']?(\d+\.?\d*)',
                    r'["\']price["\']\s*:\s*["\']?(\d+\.?\d*)',
                    r'["\']amount["\']\s*:\s*["\']?(\d+\.?\d*)',
                ]
                for pattern in price_patterns:
                    matches = re.findall(pattern, script_text, re.IGNORECASE)
                    for match in matches:
                        try:
                            val = float(match)
                            if val > 0 and val < 10000:
                                all_prices.append(val)
                        except:
                            pass
        
        # FILTRAR PREÇOS INCORRETOS
        if not all_prices:
            return {'current': 0, 'original': 0, 'discount_percent': 0}
        
        # Remover duplicatas
        all_prices = list(set(all_prices))
        
        # FILTRO 1: Remover preços muito pequenos (< $1.00)
        all_prices = [p for p in all_prices if p >= 1.00]
        
        if not all_prices:
            return {'current': 0, 'original': 0, 'discount_percent': 0}
        
        # FILTRO 2: Se houver preços muito diferentes, pegar o maior (mais provável ser o preço principal)
        max_price = max(all_prices)
        min_price = min(all_prices)
        
        # Se a diferença for muito grande (> 50%), provavelmente tem preço por unidade
        if max_price > 0 and (max_price - min_price) / max_price > 0.5:
            # Filtrar preços que são muito menores que o máximo
            # Manter apenas preços que são pelo menos 30% do máximo
            filtered = [p for p in all_prices if p >= max_price * 0.30]
            if filtered:
                all_prices = filtered
        
        # FILTRO 3: Se ainda tiver muitos preços, pegar os 2 maiores
        if len(all_prices) > 3:
            all_prices = sorted(all_prices, reverse=True)[:3]
        
        # FILTRO 4: Remover preços que são claramente "por unidade"
        # Se o menor preço for menos de 20% do maior, ignorar
        if len(all_prices) > 1:
            max_p = max(all_prices)
            all_prices = [p for p in all_prices if p >= max_p * 0.20]
        
        if not all_prices:
            return {'current': 0, 'original': 0, 'discount_percent': 0}
        
        # Determinar preço atual e original
        # Preço atual = menor (geralmente é o preço com desconto)
        # Preço original = maior (geralmente é o preço sem desconto)
        current_price = min(all_prices)
        original_price = max(all_prices)
        
        # Se o preço "original" for muito maior que o atual, pode ser preço errado
        # Limitar diferença máxima de 300% (ex: $10 -> $30 é razoável, mas $10 -> $100 não)
        if original_price > current_price * 3:
            # Se a diferença for absurda, usar o atual como ambos
            original_price = current_price
        
        return self._parse_prices(str(current_price), str(original_price))
    
    # Aplicar patch
    SiteSpecificExtractor._extract_amazon_prices = improved_extract_amazon_prices_v2
    
    print("✅ Patch V2 aplicado! Filtragem de preços melhorada.")
    return True

if __name__ == '__main__':
    patch_extractors_for_replit_v2()
