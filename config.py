"""
Configurações do bot
"""

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('config.env')

class Config:
    """Classe de configuração centralizada"""
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '').strip()
    
    # Shopify
    SHOPIFY_SHOP_URL = os.getenv('SHOPIFY_SHOP_URL', '').strip()
    SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN', '').strip()
    
    # OpenAI (opcional)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Metafields
    AFFILIATE_LINK_METAFIELD_NAMESPACE = os.getenv('AFFILIATE_LINK_METAFIELD_NAMESPACE', 'custom')
    AFFILIATE_LINK_METAFIELD_KEY = os.getenv('AFFILIATE_LINK_METAFIELD_KEY', 'affiliate_link')
    
    # Configurações de extração
    MAX_IMAGES = int(os.getenv('MAX_IMAGES', '4'))
    MAX_DESCRIPTION_LENGTH = int(os.getenv('MAX_DESCRIPTION_LENGTH', '500'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '10'))
    
    # Headers para requests
    USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    @classmethod
    def validate(cls) -> tuple[bool, list]:
        """Valida se todas as configurações obrigatórias estão presentes"""
        errors = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN é obrigatório")
        
        if not cls.TELEGRAM_CHANNEL_ID:
            errors.append("TELEGRAM_CHANNEL_ID é obrigatório")
        
        if not cls.SHOPIFY_SHOP_URL:
            errors.append("SHOPIFY_SHOP_URL é obrigatório")
        
        if not cls.SHOPIFY_ACCESS_TOKEN:
            errors.append("SHOPIFY_ACCESS_TOKEN é obrigatório")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_headers(cls) -> dict:
        """Retorna headers padrão para requests"""
        return {
            'User-Agent': cls.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

# Mensagens do bot
class Messages:
    """Mensagens padronizadas do bot"""
    
    WELCOME = """
🤖 *Bot de Importação de Produtos*

Olá! Eu posso ajudar você a importar produtos para o Shopify e postar no Telegram.

*Como usar:*
1. Envie o link do produto que deseja importar
2. Eu vou extrair as informações automaticamente
3. Você pode revisar e ajustar se necessário
4. Eu posto no Shopify e no canal do Telegram

*Comandos disponíveis:*
/start - Mostrar esta mensagem
/help - Ajuda detalhada
/status - Status das configurações

Envie um link para começar! 🚀
    """
    
    HELP = """
📖 *Ajuda - Bot de Importação*

*Sites suportados:*
• Amazon (amazon.com.br, amazon.com)
• Mercado Livre (mercadolivre.com.br)
• AliExpress (aliexpress.com)
• Shopee (shopee.com.br)
• Magazine Luiza (magazineluiza.com.br)
• Americanas (americanas.com.br)
• Outros sites de e-commerce

*Processo de importação:*
1. 📎 Envie o link do produto
2. 🔍 Bot extrai informações automaticamente
3. 📋 Revise os dados extraídos
4. ✅ Confirme a publicação
5. 🛍️ Produto criado no Shopify
6. 📢 Postagem automática no canal

*Dados extraídos:*
• Título otimizado
• 3-4 imagens principais
• Preços (atual e original)
• Porcentagem de desconto
• Descrição do produto
• Link de afiliado

*Comandos:*
/start - Mensagem inicial
/help - Esta ajuda
/status - Verificar configurações
    """
    
    INVALID_URL = "❌ Por favor, envie uma URL válida."
    PROCESSING = "🔍 Extraindo informações do produto..."
    ERROR_EXTRACTING = "❌ Erro ao extrair produto: {error}"
    ERROR_PROCESSING = "❌ Erro ao processar o link. Tente novamente."
    OPERATION_CANCELLED = "❌ Operação cancelada."
    PRODUCT_NOT_FOUND = "❌ Produto não encontrado. Envie um novo link."
    PUBLISHING = "🚀 Publicando produto no Shopify..."
    AFFILIATE_LINK_REQUEST = "🔗 Por favor, envie o link de afiliado para este produto:"
    ERROR_PUBLISHING = "❌ Erro ao publicar no Shopify."
    ERROR_PUBLISHING_GENERAL = "❌ Erro ao publicar produto."
    
    @staticmethod
    def product_preview(title: str, current_price: float, original_price: float, 
                       discount: int, description: str, images_count: int) -> str:
        """Gera mensagem de preview do produto"""
        preview = f"""
📦 *Produto Extraído*

*Título:* {title}

*Preço:* R$ {current_price:.2f}
{f"*De:* R$ {original_price:.2f}" if original_price > current_price else ""}
{f"*Desconto:* {discount}% OFF" if discount > 0 else ""}

*Descrição:* {description[:100]}{"..." if len(description) > 100 else ""}

*Imagens encontradas:* {images_count}

O que deseja fazer?
        """
        return preview.strip()
    
    @staticmethod
    def success_message(shopify_url: str, title: str) -> str:
        """Gera mensagem de sucesso"""
        return f"""
✅ *Produto publicado com sucesso!*

*Shopify:* {shopify_url}
*Canal:* Postado no canal do Telegram

Produto: {title}
        """.strip()
    
    @staticmethod
    def telegram_channel_post(title: str, current_price: float, original_price: float, 
                            discount: int, affiliate_link: str) -> str:
        """Gera mensagem para o canal do Telegram"""
        message = f"*{title}*\n\n"
        
        if discount > 0:
            message += f"💥 {discount}% OFF\n"
            message += f"~~R$ {original_price:.2f}~~\n"
        
        message += f"💰 *R$ {current_price:.2f}*\n\n"
        message += f"🛒 Link da Amazon (afiliado): {affiliate_link}"
        
        return message

# Configurações de categorias do Shopify (em inglês)
SHOPIFY_CATEGORIES = [
    "Electronics",
    "Home & Garden", 
    "Fashion & Beauty",
    "Sports & Leisure",
    "Books & Media",
    "Toys & Games",
    "Automotive",
    "Health & Wellness",
    "Computing",
    "Cell Phones & Tablets",
    "Appliances",
    "Tools",
    "Pet Shop",
    "Baby & Kids",
    "General",
    "Other"
]

# Categorias de desconto
DISCOUNT_CATEGORIES = [
    "10off",
    "20off", 
    "30off",
    "40off",
    "50off",
    "60off",
    "70off",
    "80off",
    "90off",
    "hotdeal",
    "flash-sale",
    "clearance"
]
