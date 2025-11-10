"""
Extractors específicos para diferentes sites de e-commerce
"""

import re
import json
from typing import Dict, List, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup

class SiteSpecificExtractor:
    """Extrator específico para diferentes sites"""
    
    def __init__(self):
        self.extractors = {
            'amazon.com.br': self._extract_amazon,
            'amazon.com': self._extract_amazon,
            'mercadolivre.com.br': self._extract_mercadolivre,
            'aliexpress.com': self._extract_aliexpress,
            'shopee.com.br': self._extract_shopee,
            'magazineluiza.com.br': self._extract_magalu,
            'americanas.com.br': self._extract_americanas,
        }
    
    def extract(self, url: str, soup: BeautifulSoup) -> Dict:
        """Extrai dados usando extrator específico do site"""
        domain = urlparse(url).netloc.lower()
        
        # Encontrar extrator apropriado
        extractor = None
        for site_domain, site_extractor in self.extractors.items():
            if site_domain in domain:
                extractor = site_extractor
                break
        
        if extractor:
            return extractor(soup, url)
        else:
            return self._extract_generic(soup, url)
    
    def _extract_amazon(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extrator específico para Amazon"""
        data = {}
        
        # Título - mais seletores para melhor captura
        title_selectors = [
            '#productTitle',
            'h1#title span',
            'h1.a-size-large',
            'h1.a-size-base',
            '.product-title',
            'h1',
            'span#productTitle'
        ]
        data['title'] = self._get_text_by_selectors(soup, title_selectors)
        
        # Se não encontrou título, tentar JSON-LD
        if not data['title']:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict) and 'name' in json_data:
                        data['title'] = json_data['name']
                        break
                    elif isinstance(json_data, list):
                        for item in json_data:
                            if isinstance(item, dict) and 'name' in item:
                                data['title'] = item['name']
                                break
                except:
                    continue
        
        # Preços - mais seletores e métodos
        price_current = self._get_text_by_selectors(soup, [
            '.a-price .a-offscreen',
            '.a-price-current .a-offscreen',
            '#priceblock_dealprice',
            '#priceblock_ourprice',
            '#priceblock_saleprice',
            '.a-price-whole',
            'span.a-price[data-a-color="price"] .a-offscreen',
            'span[data-a-color="price"] .a-offscreen'
        ])
        
        # Se não encontrou preço atual, tentar JSON-LD
        if not price_current:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict):
                        if 'offers' in json_data:
                            offers = json_data['offers']
                            if isinstance(offers, dict) and 'price' in offers:
                                price_current = str(offers['price'])
                                break
                            elif isinstance(offers, list) and len(offers) > 0:
                                if 'price' in offers[0]:
                                    price_current = str(offers[0]['price'])
                                    break
                except:
                    continue
        
        price_original = self._get_text_by_selectors(soup, [
            '.a-price-was .a-offscreen',
            '#priceblock_listprice',
            '.a-text-strike .a-offscreen',
            '.basisPrice .a-offscreen',
            'span.a-price.a-text-price .a-offscreen'
        ])
        
        data['price'] = self._parse_prices(price_current, price_original)
        
        # Imagens
        data['images'] = self._extract_amazon_images(soup)
        
        # Descrição
        desc_selectors = [
            '#feature-bullets ul',
            '#productDescription',
            '.a-unordered-list.a-vertical',
            '#productDescription_feature_div'
        ]
        data['description'] = self._get_text_by_selectors(soup, desc_selectors)
        
        return data
    
    def _extract_amazon_images(self, soup: BeautifulSoup) -> List[str]:
        """Extrai imagens específicas da Amazon"""
        images = []
        
        # Imagens principais
        main_img = soup.select_one('#landingImage')
        if main_img:
            src = main_img.get('data-old-hires') or main_img.get('src')
            if src:
                images.append(src)
        
        # Imagens da galeria
        gallery_imgs = soup.select('.a-button-thumbnail img')
        for img in gallery_imgs:
            src = img.get('src')
            if src:
                # Converter para versão de alta resolução
                src = src.replace('._SS40_', '._SL1500_')
                if src not in images:
                    images.append(src)
        
        # JSON-LD data
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if 'image' in data:
                    img_urls = data['image'] if isinstance(data['image'], list) else [data['image']]
                    for img_url in img_urls:
                        if img_url not in images:
                            images.append(img_url)
            except:
                continue
        
        return images[:4]
    
    def _extract_mercadolivre(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extrator específico para Mercado Livre"""
        data = {}
        
        # Título
        title_selectors = [
            '.ui-pdp-title',
            'h1.item-title__primary',
            '.x-item-title-label h1'
        ]
        data['title'] = self._get_text_by_selectors(soup, title_selectors)
        
        # Preços
        price_current = self._get_text_by_selectors(soup, [
            '.andes-money-amount__fraction',
            '.price-tag-fraction',
            '.notranslate'
        ])
        
        price_original = self._get_text_by_selectors(soup, [
            '.ui-pdp-price__original-value',
            '.price-tag-was'
        ])
        
        data['price'] = self._parse_prices(price_current, price_original)
        
        # Imagens
        img_elements = soup.select('.ui-pdp-gallery img, .gallery-image img')
        images = []
        for img in img_elements:
            src = img.get('data-src') or img.get('src')
            if src and src not in images:
                images.append(src)
        data['images'] = images[:4]
        
        # Descrição
        desc_selectors = [
            '.ui-pdp-description__content',
            '.item-description',
            '.ui-pdp-specs'
        ]
        data['description'] = self._get_text_by_selectors(soup, desc_selectors)
        
        return data
    
    def _extract_aliexpress(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extrator específico para AliExpress"""
        data = {}
        
        # Título
        title_selectors = [
            'h1[data-pl="product-title"]',
            '.product-title-text',
            'h1.product-name'
        ]
        data['title'] = self._get_text_by_selectors(soup, title_selectors)
        
        # Preços
        price_current = self._get_text_by_selectors(soup, [
            '.product-price-current',
            '.uniform-banner-box-price',
            '.notranslate'
        ])
        
        price_original = self._get_text_by_selectors(soup, [
            '.product-price-del',
            '.uniform-banner-box-original-price'
        ])
        
        data['price'] = self._parse_prices(price_current, price_original)
        
        # Imagens
        img_elements = soup.select('.images-view-item img, .product-image img')
        images = []
        for img in img_elements:
            src = img.get('src') or img.get('data-src')
            if src and src not in images:
                images.append(src)
        data['images'] = images[:4]
        
        # Descrição
        desc_selectors = [
            '.product-overview',
            '.product-description',
            '.product-property'
        ]
        data['description'] = self._get_text_by_selectors(soup, desc_selectors)
        
        return data
    
    def _extract_shopee(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extrator específico para Shopee"""
        data = {}
        
        # Título
        title_selectors = [
            '._44qnta',
            '.qaNIZv',
            'h1'
        ]
        data['title'] = self._get_text_by_selectors(soup, title_selectors)
        
        # Preços
        price_current = self._get_text_by_selectors(soup, [
            '._16N3Fb',
            '.flex-no-wrap',
            '.notranslate'
        ])
        
        price_original = self._get_text_by_selectors(soup, [
            '._1w9jLI',
            '.mq6Cw7'
        ])
        
        data['price'] = self._parse_prices(price_current, price_original)
        
        # Imagens
        img_elements = soup.select('._2JbXVy img, .product-image img')
        images = []
        for img in img_elements:
            src = img.get('src')
            if src and src not in images:
                images.append(src)
        data['images'] = images[:4]
        
        # Descrição
        desc_selectors = [
            '._2u0jt9',
            '.product-detail',
            '._2aZyWI'
        ]
        data['description'] = self._get_text_by_selectors(soup, desc_selectors)
        
        return data
    
    def _extract_magalu(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extrator específico para Magazine Luiza"""
        data = {}
        
        # Título
        title_selectors = [
            '[data-testid="heading-product-title"]',
            '.header-product__title',
            'h1'
        ]
        data['title'] = self._get_text_by_selectors(soup, title_selectors)
        
        # Preços
        price_current = self._get_text_by_selectors(soup, [
            '[data-testid="price-value"]',
            '.price-template__text',
            '.price'
        ])
        
        price_original = self._get_text_by_selectors(soup, [
            '[data-testid="price-original"]',
            '.price-template__discount'
        ])
        
        data['price'] = self._parse_prices(price_current, price_original)
        
        # Imagens
        img_elements = soup.select('[data-testid="product-image"] img, .product-gallery img')
        images = []
        for img in img_elements:
            src = img.get('src')
            if src and src not in images:
                images.append(src)
        data['images'] = images[:4]
        
        # Descrição
        desc_selectors = [
            '[data-testid="product-description"]',
            '.description-product',
            '.product-resume'
        ]
        data['description'] = self._get_text_by_selectors(soup, desc_selectors)
        
        return data
    
    def _extract_americanas(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extrator específico para Americanas"""
        data = {}
        
        # Título
        title_selectors = [
            'h1[data-testid="product-name"]',
            '.product-title',
            'h1'
        ]
        data['title'] = self._get_text_by_selectors(soup, title_selectors)
        
        # Preços
        price_current = self._get_text_by_selectors(soup, [
            '[data-testid="price-value"]',
            '.sales-price',
            '.price'
        ])
        
        price_original = self._get_text_by_selectors(soup, [
            '[data-testid="list-price"]',
            '.list-price'
        ])
        
        data['price'] = self._parse_prices(price_current, price_original)
        
        # Imagens
        img_elements = soup.select('[data-testid="product-image"] img, .product-image img')
        images = []
        for img in img_elements:
            src = img.get('src')
            if src and src not in images:
                images.append(src)
        data['images'] = images[:4]
        
        # Descrição
        desc_selectors = [
            '[data-testid="product-description"]',
            '.product-description',
            '.product-details'
        ]
        data['description'] = self._get_text_by_selectors(soup, desc_selectors)
        
        return data
    
    def _extract_generic(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extrator genérico para sites não específicos"""
        data = {}
        
        # Título genérico
        title_selectors = [
            'h1.product-title, h1.product-name',
            '.product-title, .product-name',
            'h1',
            'title'
        ]
        data['title'] = self._get_text_by_selectors(soup, title_selectors)
        
        # Preços genéricos
        price_selectors = [
            '.price, .product-price',
            '[class*="price"]',
            '[data-price]'
        ]
        
        prices = []
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                price_text = element.get_text().strip()
                price_value = self._extract_price_value(price_text)
                if price_value:
                    prices.append(price_value)
        
        if prices:
            prices.sort()
            data['price'] = {
                'current': prices[0],
                'original': prices[-1] if len(prices) > 1 else prices[0],
                'discount_percent': 0
            }
            
            if len(prices) > 1 and prices[-1] > prices[0]:
                discount = ((prices[-1] - prices[0]) / prices[-1]) * 100
                data['price']['discount_percent'] = round(discount)
        
        # Imagens genéricas
        img_elements = soup.select('img[alt*="product"], img[class*="product"], .product img')
        images = []
        for img in img_elements:
            src = img.get('src') or img.get('data-src')
            if src and self._is_valid_image_url(src):
                if src not in images:
                    images.append(src)
        data['images'] = images[:4]
        
        # Descrição genérica
        desc_selectors = [
            '.product-description, .description',
            '[class*="description"]',
            '.product-details, .details'
        ]
        data['description'] = self._get_text_by_selectors(soup, desc_selectors)
        
        return data
    
    def _get_text_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """Obtém texto usando lista de seletores"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text()
                if text:
                    # Limpar texto: remover espaços extras e quebras de linha
                    text = ' '.join(text.split())
                    if text.strip():
                        return text.strip()
        return ""
    
    def _parse_prices(self, current_str: str, original_str: str) -> Dict:
        """Processa strings de preço"""
        current_price = self._extract_price_value(current_str) if current_str else 0
        original_price = self._extract_price_value(original_str) if original_str else current_price
        
        # Se preço original é menor que atual, trocar
        if original_price < current_price:
            current_price, original_price = original_price, current_price
        
        discount_percent = 0
        if original_price > current_price:
            discount_percent = round(((original_price - current_price) / original_price) * 100)
        
        return {
            'current': current_price,
            'original': original_price,
            'discount_percent': discount_percent
        }
    
    def _extract_price_value(self, price_text: str) -> Optional[float]:
        """Extrai valor numérico do preço"""
        if not price_text:
            return None
        
        # Remover caracteres não numéricos exceto vírgula e ponto
        price_clean = re.sub(r'[^\d,.]', '', price_text.strip())
        
        if not price_clean:
            return None
        
        try:
            # Tratar formato brasileiro (123,45) ou americano (123.45)
            if ',' in price_clean and '.' in price_clean:
                # Formato: 1.234,56 (brasileiro) ou 1,234.56 (americano)
                # Verificar qual é o separador de milhares
                if price_clean.rindex('.') > price_clean.rindex(','):
                    # Último ponto está depois da vírgula = formato americano (1,234.56)
                    price_clean = price_clean.replace(',', '')
                else:
                    # Última vírgula está depois do ponto = formato brasileiro (1.234,56)
                    price_clean = price_clean.replace('.', '').replace(',', '.')
            elif ',' in price_clean:
                # Verificar se é separador decimal ou de milhares
                parts = price_clean.split(',')
                if len(parts[-1]) == 2:  # Provavelmente decimal (123,45)
                    price_clean = price_clean.replace(',', '.')
                elif len(parts[-1]) == 3:  # Provavelmente milhares (1,234)
                    price_clean = price_clean.replace(',', '')
            elif '.' in price_clean:
                # Verificar se é decimal ou milhares
                parts = price_clean.split('.')
                if len(parts) > 2:  # Múltiplos pontos = milhares (1.234.567)
                    price_clean = price_clean.replace('.', '')
                elif len(parts) == 2 and len(parts[-1]) > 2:  # Mais de 2 dígitos após ponto = milhares
                    price_clean = price_clean.replace('.', '')
            
            return float(price_clean)
        except (ValueError, IndexError):
            return None
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Verifica se a URL é uma imagem válida"""
        if not url:
            return False
        
        # Filtrar imagens muito pequenas ou irrelevantes
        skip_patterns = [
            'logo', 'icon', 'sprite', 'pixel', '1x1', 'tracking',
            'analytics', 'facebook', 'twitter', 'instagram'
        ]
        
        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False
        
        # Verificar extensões de imagem
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        return any(ext in url_lower for ext in image_extensions) or 'image' in url_lower
