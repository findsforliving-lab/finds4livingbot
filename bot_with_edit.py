#!/usr/bin/env python3
"""
Bot com funcionalidade de edição
"""

import logging
from typing import Optional, Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler
from urllib.parse import urlparse
from extractors import SiteSpecificExtractor
from config import Config, Messages
import shopify

# Estados da conversa
WAITING_TITLE, WAITING_PRICE_CURRENT, WAITING_PRICE_ORIGINAL, WAITING_DESCRIPTION, WAITING_IMAGES = range(5)

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ProductExtractor:
    def __init__(self):
        self.site_extractor = SiteSpecificExtractor()
    
    async def extract_product_info(self, url: str) -> Dict:
        """Extrai informações do produto a partir da URL"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Expandir links curtos (amzn.to, etc)
            final_url = await self._expand_short_url(url)
            
            headers = Config.get_headers()
            response = requests.get(final_url, headers=headers, timeout=Config.REQUEST_TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Usar extrator específico do site
            product_info = self.site_extractor.extract(final_url, soup)
            product_info['original_url'] = url  # Manter URL original (pode ser link curto)
            
            return product_info
            
        except Exception as e:
            logger.error(f"Erro ao extrair produto: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {'error': str(e)}
    
    async def _expand_short_url(self, url: str) -> str:
        """Expande URLs curtas (amzn.to, etc)"""
        try:
            # Se não é link curto, retornar como está
            if 'amzn.to' not in url.lower():
                return url
            
            import requests
            # Fazer requisição HEAD para pegar a URL final sem baixar o conteúdo
            response = requests.head(url, allow_redirects=True, timeout=10)
            final_url = response.url
            
            # Se conseguiu expandir, retornar URL final
            if final_url and final_url != url:
                logger.info(f"URL expandida: {url} -> {final_url}")
                return final_url
            
            return url
        except Exception as e:
            logger.warning(f"Erro ao expandir URL curta: {e}, usando URL original")
            return url

class ShopifyManager:
    def __init__(self):
        if Config.SHOPIFY_SHOP_URL and Config.SHOPIFY_ACCESS_TOKEN:
            shopify.ShopifyResource.set_site(f"https://{Config.SHOPIFY_SHOP_URL}/admin/api/2023-10/")
            shopify.ShopifyResource.set_headers({"X-Shopify-Access-Token": Config.SHOPIFY_ACCESS_TOKEN})
    
    async def create_product(self, product_data: Dict, affiliate_link: str) -> Optional[Dict]:
        """Cria produto no Shopify"""
        try:
            # Preparar dados do produto
            categories = product_data.get('categories', ['Electronics'])
            main_category = categories[0]  # Primeira categoria como principal
            
            shopify_product = {
                'title': product_data.get('title', 'Produto Importado'),
                'body_html': product_data.get('description', ''),
                'vendor': 'Importado',
                'product_type': main_category,
                'status': 'active',
                'images': []
            }
            
            # Adicionar imagens
            images_list = product_data.get('images', [])
            logger.info(f"Imagens sendo enviadas para o Shopify: {images_list}")
            
            for img_url in images_list:
                shopify_product['images'].append({'src': img_url})
                logger.info(f"Adicionando imagem ao Shopify: {img_url}")
            
            # Adicionar variante com preço
            price_info = product_data.get('price', {})
            current_price = price_info.get('current', 0)
            original_price = price_info.get('original', current_price)
            
            shopify_product['variants'] = [{
                'price': str(current_price),
                'compare_at_price': str(original_price) if original_price > current_price else None,
                'inventory_management': None,
                'inventory_policy': 'continue'
            }]
            
            # Criar produto
            product = shopify.Product(shopify_product)
            if product.save():
                # Adicionar metafield com link de afiliado
                logger.info(f"🔗 SALVANDO AFFILIATE LINK: {affiliate_link}")
                logger.info(f"🔗 Namespace: {Config.AFFILIATE_LINK_METAFIELD_NAMESPACE}")
                logger.info(f"🔗 Key: {Config.AFFILIATE_LINK_METAFIELD_KEY}")
                try:
                    # Usar a MESMA lógica que funcionou no teste
                    logger.info(f"🔍 Buscando metafield usando método que funcionou...")
                    logger.info(f"🔗 Link a ser salvo: {affiliate_link}")
                    logger.info(f"🎯 Produto ID: {product.id}")
                    
                    # Buscar TODOS os metafields (igual ao teste que funcionou)
                    all_metafields = shopify.Metafield.find()
                    logger.info(f"📋 Total de metafields encontrados: {len(all_metafields)}")
                    
                    # Procurar o metafield específico do produto
                    affiliate_metafield = None
                    for mf in all_metafields:
                        # Verificar se é do produto atual E tem namespace/key corretos
                        if (mf.owner_resource == 'product' and 
                            str(mf.owner_id) == str(product.id) and
                            mf.namespace == 'custom' and 
                            mf.key == 'affiliate_link'):
                            affiliate_metafield = mf
                            logger.info(f"✅ ENCONTRADO metafield do produto: {mf.namespace}.{mf.key} (ID: {mf.id})")
                            break
                    
                    if affiliate_metafield:
                        # Preencher o metafield (igual ao teste que funcionou)
                        logger.info(f"✏️ Preenchendo metafield com: {affiliate_link}")
                        affiliate_metafield.value = affiliate_link
                        
                        if affiliate_metafield.save():
                            logger.info(f"✅ Metafield preenchido com sucesso!")
                            logger.info(f"✅ Produto ID: {product.id}")
                            logger.info(f"✅ Metafield ID: {affiliate_metafield.id}")
                            logger.info(f"✅ Valor salvo: {affiliate_link}")
                        else:
                            logger.error(f"❌ Erro ao preencher metafield: {affiliate_metafield.errors}")
                    else:
                        # Se não encontrou, criar um novo com as configurações corretas
                        logger.warning(f"⚠️ Metafield não encontrado para produto {product.id}")
                        logger.info(f"🆕 Criando metafield com configurações corretas...")
                        
                        # Usar as configurações que funcionaram no teste
                        new_metafield = shopify.Metafield({
                            'namespace': 'custom',
                            'key': 'affiliate_link',
                            'value': affiliate_link,
                            'type': 'url',  # Tipo correto que aparece na interface
                            'owner_id': product.id,
                            'owner_resource': 'product'
                        })
                        
                        if new_metafield.save():
                            logger.info(f"✅ Metafield criado com sucesso!")
                            logger.info(f"✅ ID: {new_metafield.id}")
                            logger.info(f"✅ Namespace: custom")
                            logger.info(f"✅ Key: affiliate_link")
                            logger.info(f"✅ Type: url")
                            logger.info(f"✅ Valor: {affiliate_link}")
                            logger.info(f"✅ Agora deve aparecer na interface do Shopify!")
                        else:
                            logger.error(f"❌ Erro ao criar metafield: {new_metafield.errors}")
                            try:
                                logger.error(f"❌ Detalhes: {new_metafield.errors.full_messages()}")
                            except:
                                logger.error(f"❌ Sem detalhes do erro")
                            
                except Exception as e:
                    logger.error(f"❌ Erro ao processar metafield: {e}")
                
                # Adicionar produto às Collections
                logger.info(f"Adicionando produto às Collections: {categories}")
                self.add_product_to_collections(product.id, categories)
                
                return {
                    'id': product.id,
                    'handle': product.handle,
                    'title': product.title,
                    'url': f"https://{Config.SHOPIFY_SHOP_URL}/products/{product.handle}"
                }
            else:
                logger.error(f"Erro ao criar produto: {product.errors}")
                return None
                
        except Exception as e:
            logger.error(f"Erro no Shopify: {e}")
            return None
    
    def get_collections(self):
        """Busca todas as collections existentes no Shopify"""
        try:
            collections = shopify.CustomCollection.find()
            collection_dict = {}
            for collection in collections:
                collection_dict[collection.title.lower()] = collection.id
            logger.info(f"Collections encontradas: {list(collection_dict.keys())}")
            return collection_dict
        except Exception as e:
            logger.error(f"Erro ao buscar collections: {e}")
            return {}
    
    def create_collection(self, collection_name):
        """Cria uma nova collection no Shopify"""
        try:
            collection = shopify.CustomCollection({
                'title': collection_name,
                'published': True
            })
            if collection.save():
                logger.info(f"Collection '{collection_name}' criada com ID: {collection.id}")
                return collection.id
            else:
                logger.error(f"Erro ao criar collection '{collection_name}': {collection.errors}")
                return None
        except Exception as e:
            logger.error(f"Erro ao criar collection '{collection_name}': {e}")
            return None
    
    def add_product_to_collections(self, product_id, collection_names):
        """Adiciona produto às collections especificadas"""
        try:
            existing_collections = self.get_collections()
            
            for collection_name in collection_names:
                collection_name_lower = collection_name.lower()
                
                # Verificar se collection existe
                if collection_name_lower in existing_collections:
                    collection_id = existing_collections[collection_name_lower]
                    logger.info(f"Collection '{collection_name}' já existe (ID: {collection_id})")
                else:
                    # Criar nova collection
                    collection_id = self.create_collection(collection_name)
                    if not collection_id:
                        logger.error(f"Falha ao criar collection '{collection_name}'")
                        continue
                
                # Adicionar produto à collection
                try:
                    collect = shopify.Collect({
                        'product_id': product_id,
                        'collection_id': collection_id
                    })
                    if collect.save():
                        logger.info(f"Produto {product_id} adicionado à collection '{collection_name}'")
                    else:
                        logger.error(f"Erro ao adicionar produto à collection '{collection_name}': {collect.errors}")
                except Exception as e:
                    logger.error(f"Erro ao criar Collect para '{collection_name}': {e}")
                    
        except Exception as e:
            logger.error(f"Erro ao processar collections: {e}")

class TelegramBotWithEdit:
    def __init__(self):
        self.product_extractor = ProductExtractor()
        self.shopify_manager = ShopifyManager()
        self.pending_products = {}
        self.editing_products = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        welcome_msg = """
🤖 Bot de Importação de Produtos
Funcionalidades:✅ Extração automática de produtos
✅ Edição de informações antes de publicar
✅ Integração com Shopify
✅ Postagem no canal do Telegram

Como usar:1. Envie um link de produto
2. Revise e edite as informações
3. Confirme a publicação

Envie um link para começar! 🚀
        """
        await update.message.reply_text(welcome_msg)
    
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa URLs enviadas pelo usuário"""
        url = update.message.text.strip()
        user_id = update.effective_user.id
        
        # CRÍTICO: Se o usuário está editando, não processar como nova URL
        if user_id in self.editing_products:
            logger.info(f"Usuário {user_id} está editando, redirecionando para handle_edit_input")
            await self.handle_edit_input(update, context)
            return
        
        if not self._is_valid_url(url):
            await update.message.reply_text("❌ Por favor, envie uma URL válida.")
            return
        
        processing_msg = await update.message.reply_text("🔍 Extraindo informações do produto...")
        
        try:
            product_info = await self.product_extractor.extract_product_info(url)
            
            if 'error' in product_info:
                await processing_msg.edit_text(f"❌ Erro ao extrair produto: {product_info['error']}")
                return
            
            # Inicializar categorias se não existir
            if 'categories' not in product_info:
                product_info['categories'] = [product_info.get('category', 'Electronics')]
            
            # Armazenar produto pendente
            self.pending_products[user_id] = product_info
            
            # Mostrar menu inicial com opções
            await self._show_initial_menu(update, product_info, processing_msg)
            
        except Exception as e:
            logger.error(f"Erro ao processar URL: {e}")
            await processing_msg.edit_text("❌ Erro ao processar o link. Tente novamente.")
    
    async def _show_initial_menu(self, update: Update, product_info: Dict, msg_to_edit):
        """Mostra menu inicial com opções: Shopify ou Canal"""
        title = product_info.get('title', 'Sem título')
        price_info = product_info.get('price', {})
        current_price = price_info.get('current', 0)
        original_price = price_info.get('original', current_price)
        images_count = len(product_info.get('images', []))
        
        menu_text = f"""
📦 PRODUTO EXTRAÍDO

📝 Título: {title}
💰 Preço: ${current_price:.2f}
📸 Imagens: {images_count} encontradas

🎯 Onde deseja publicar este produto?
        """
        
        keyboard = [
            [InlineKeyboardButton("🛍️ Enviar para Shopify", callback_data="publish_to_shopify")],
            [InlineKeyboardButton("📢 Enviar para Canal Telegram", callback_data="publish_to_channel_only")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await msg_to_edit.edit_text(menu_text, reply_markup=reply_markup)
    
    async def _show_product_preview_with_edit(self, update: Update, product_info: Dict, msg_to_edit):
        """Mostra preview do produto com opções de edição"""
        logger.info(f"Mostrando preview para produto: {product_info}")
        
        title = product_info.get('title', 'Sem título')
        price_info = product_info.get('price', {})
        current_price = price_info.get('current', 0)
        original_price = price_info.get('original', current_price)
        discount = price_info.get('discount_percent', 0)
        description = product_info.get('description', 'Sem descrição')
        images_count = len(product_info.get('images', []))
        
        logger.info(f"Dados extraídos - Título: {title}, Imagens: {images_count}, Preço: {current_price}")
        
        # Mostrar URLs das imagens
        images = product_info.get('images', [])
        logger.info(f"PREVIEW - Imagens sendo mostradas: {images}")
        
        images_text = ""
        if images:
            images_text = "\nURLs das imagens:\n"
            for i, img in enumerate(images[:3], 1):
                images_text += f"{i}. {img}\n"
            if len(images) > 3:
                images_text += f"... e mais {len(images) - 3} imagens\n"
        
        categories = product_info.get('categories', ['Electronics'])
        categories_text = " | ".join(categories)
        
        affiliate_link = product_info.get('original_url', 'Não informado')
        
        preview_text = f"""
📦 PRODUTO EXTRAÍDO
📝 Título: {title}

🏷️ Categorias: {categories_text}

💰 Preços:• Atual: R$ {current_price:.2f}
{f"• Original: R$ {original_price:.2f}" if original_price > current_price else ""}
{f"• Desconto: {discount}% OFF" if discount > 0 else ""}

📸 Imagens: {images_count} encontradas{images_text}

📄 Descrição: {description[:100]}{"..." if len(description) > 100 else ""}

🔗 Link Afiliado: {affiliate_link}

O que deseja fazer?        """
        
        keyboard = [
            [InlineKeyboardButton("✏️ Editar Título", callback_data="edit_title")],
            [InlineKeyboardButton("🏷️ Gerenciar Categorias", callback_data="manage_categories")],
            [InlineKeyboardButton("💰 Editar Preços", callback_data="edit_prices")],
            [InlineKeyboardButton("📄 Editar Descrição", callback_data="edit_description")],
            [InlineKeyboardButton("📸 Editar Imagens", callback_data="edit_images")],
            [InlineKeyboardButton("✅ Publicar Assim", callback_data="publish_as_is")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await msg_to_edit.edit_text(preview_text, reply_markup=reply_markup)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa callbacks dos botões"""
        query = update.callback_query
        
        # CRÍTICO: Responder ao callback IMEDIATAMENTE
        try:
            await query.answer()
        except Exception as e:
            logger.error(f"Erro ao responder callback: {e}")
            return
        
        user_id = update.effective_user.id
        
        try:
            if query.data == "publish_to_shopify":
                # Fluxo completo: mostrar preview com todas as opções de edição
                if user_id in self.pending_products:
                    product_info = self.pending_products[user_id]
                    # Criar um objeto fake para update (a função não usa, mas precisa da assinatura)
                    from types import SimpleNamespace
                    fake_update = SimpleNamespace()
                    await self._show_product_preview_with_edit(fake_update, product_info, query.message)
            elif query.data == "publish_to_channel_only":
                # Fluxo simplificado: só canal do Telegram
                await self._handle_channel_only_flow(query, user_id)
            elif query.data == "edit_title":
                await self._start_edit_title(query, user_id)
            elif query.data == "manage_categories":
                await self._show_category_management(query, user_id)
            elif query.data == "add_main_category":
                await self._show_main_categories(query, user_id)
            elif query.data == "add_discount_category":
                await self._show_discount_categories(query, user_id)
            elif query.data.startswith("main_cat_"):
                category = query.data.replace("main_cat_", "").replace("_", " ")
                await self._add_category(query, user_id, category)
            elif query.data.startswith("disc_cat_"):
                category = query.data.replace("disc_cat_", "")
                await self._add_category(query, user_id, category)
            elif query.data.startswith("remove_cat_"):
                category = query.data.replace("remove_cat_", "").replace("_", " ")
                await self._remove_category(query, user_id, category)
            elif query.data == "back_to_preview":
                await self._back_to_preview(query, user_id)
            elif query.data == "edit_prices":
                await self._start_edit_prices(query, user_id)
            elif query.data == "edit_description":
                await self._start_edit_description(query, user_id)
            elif query.data == "edit_images":
                await self._start_edit_images(query, user_id)
            elif query.data == "publish_as_is":
                await self._publish_product(query, user_id, context)
            elif query.data == "confirm_post_channel":
                await self._confirm_post_channel(query, user_id, context)
            elif query.data == "edit_channel_text":
                await self._edit_channel_text(query, user_id)
            elif query.data == "edit_channel_preview":
                await self._edit_channel_preview(query, user_id)
            elif query.data == "cancel_channel_post":
                await self._cancel_channel_post(query, user_id)
            elif query.data == "channel_edit_title":
                await self._start_channel_edit_title(query, user_id)
            elif query.data == "channel_edit_image":
                await self._start_channel_edit_image(query, user_id)
            elif query.data == "channel_edit_price":
                await self._start_channel_edit_price(query, user_id)
            elif query.data == "channel_post_direct":
                await self._post_channel_direct(query, user_id, context)
            elif query.data == "cancel":
                await query.edit_message_text("❌ Operação cancelada.")
                if user_id in self.pending_products:
                    del self.pending_products[user_id]
        except Exception as e:
            logger.error(f"Erro ao processar callback {query.data}: {e}")
            try:
                await query.edit_message_text(f"❌ Erro interno. Tente novamente.")
            except:
                pass
    
    async def _start_edit_title(self, query, user_id: int):
        """Inicia edição do título"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        current_title = self.pending_products[user_id].get('title', 'Sem título')
        
        await query.edit_message_text(
            f"✏️ Editar Título\n\n"
            f"Título atual: {current_title}\n\n"
            f"Digite o novo título:"
        )
        
        # Armazenar estado de edição
        self.editing_products[user_id] = {'field': 'title', 'message_id': query.message.message_id}
    
    async def _start_edit_prices(self, query, user_id: int):
        """Inicia edição dos preços"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        price_info = self.pending_products[user_id].get('price', {})
        current_price = price_info.get('current', 0)
        original_price = price_info.get('original', current_price)
        
        await query.edit_message_text(
            f"💰 Editar Preços\n\n"
            f"Preço atual: R$ {current_price:.2f}\n"
            f"Preço original: R$ {original_price:.2f}\n\n"
            f"Digite os novos preços no formato:\n"
            f"`preço_atual,preço_original`\n\n"
            f"Exemplo: `39.90,69.90`"
        )
        
        self.editing_products[user_id] = {'field': 'prices', 'message_id': query.message.message_id}
    
    async def _start_edit_description(self, query, user_id: int):
        """Inicia edição da descrição"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        current_desc = self.pending_products[user_id].get('description', 'Sem descrição')
        
        await query.edit_message_text(
            f"📄 Editar Descrição\n\n"
            f"Descrição atual: {current_desc[:200]}{'...' if len(current_desc) > 200 else ''}\n\n"
            f"Digite a nova descrição:"
        )
        
        self.editing_products[user_id] = {'field': 'description', 'message_id': query.message.message_id}
    
    async def _start_edit_images(self, query, user_id: int):
        """Inicia edição das imagens"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        # Inicializar sistema de edição de imagens
        if user_id not in self.editing_products:
            self.editing_products[user_id] = {}
        
        self.editing_products[user_id] = {
            'field': 'images',
            'images': [],  # Lista de novas imagens
            'current_step': 1,  # Qual imagem está pedindo
            'max_images': 4
        }
        
        await query.edit_message_text(
            f"📸 Editar Imagens (1/4)\n\n"
            f"Vou pedir as imagens uma por vez para facilitar!\n\n"
            f"📷 Envie o link da PRIMEIRA imagem:\n"
            f"Ou digite 0 para voltar ao preview"
        )
    
    async def handle_edit_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa entrada de edição"""
        user_id = update.effective_user.id
        
        if user_id not in self.editing_products:
            return
        
        edit_info = self.editing_products[user_id]
        field = edit_info['field']
        new_value = update.message.text.strip()
        
        # Atualizar produto
        if field == 'title':
            self.pending_products[user_id]['title'] = new_value
        elif field == 'prices':
            try:
                prices = new_value.split(',')
                if len(prices) == 2:
                    current = float(prices[0].strip())
                    original = float(prices[1].strip())
                    discount = round(((original - current) / original) * 100) if original > current else 0
                    
                    self.pending_products[user_id]['price'] = {
                        'current': current,
                        'original': original,
                        'discount_percent': discount
                    }
                else:
                    await update.message.reply_text("❌ Formato inválido. Use: preço_atual,preço_original")
                    return
            except ValueError:
                await update.message.reply_text("❌ Preços inválidos. Use números válidos.")
                return
        elif field == 'description':
            self.pending_products[user_id]['description'] = new_value
        elif field == 'channel_title':
            # Editar título no fluxo simplificado
            self.pending_products[user_id]['title'] = new_value
            # Voltar ao preview simplificado
            del self.editing_products[user_id]
            success_msg = await update.message.reply_text("✅ Título atualizado!")
            # Simular query para voltar ao preview
            from types import SimpleNamespace
            fake_query = SimpleNamespace()
            fake_query.edit_message_text = success_msg.edit_text
            fake_query.message = success_msg
            fake_query.from_user = update.effective_user
            await self._show_channel_only_preview(fake_query, user_id, self.pending_products[user_id])
            return
        elif field == 'channel_image':
            # Editar primeira imagem no fluxo simplificado
            images = self.pending_products[user_id].get('images', [])
            if images:
                images[0] = new_value.strip()
            else:
                images = [new_value.strip()]
            self.pending_products[user_id]['images'] = images
            # Voltar ao preview simplificado
            del self.editing_products[user_id]
            success_msg = await update.message.reply_text("✅ Primeira imagem atualizada!")
            # Simular query para voltar ao preview
            from types import SimpleNamespace
            fake_query = SimpleNamespace()
            fake_query.edit_message_text = success_msg.edit_text
            fake_query.message = success_msg
            fake_query.from_user = update.effective_user
            await self._show_channel_only_preview(fake_query, user_id, self.pending_products[user_id])
            return
        elif field == 'channel_price':
            # Editar preço no fluxo simplificado
            try:
                prices = new_value.split(',')
                if len(prices) == 2:
                    current = float(prices[0].strip())
                    original = float(prices[1].strip())
                    discount = round(((original - current) / original) * 100) if original > current else 0
                    
                    self.pending_products[user_id]['price'] = {
                        'current': current,
                        'original': original,
                        'discount_percent': discount
                    }
                else:
                    await update.message.reply_text("❌ Formato inválido. Use: preço_atual,preço_original")
                    return
            except ValueError:
                await update.message.reply_text("❌ Preços inválidos. Use números válidos.")
                return
            # Voltar ao preview simplificado
            del self.editing_products[user_id]
            success_msg = await update.message.reply_text("✅ Preço atualizado!")
            # Simular query para voltar ao preview
            from types import SimpleNamespace
            fake_query = SimpleNamespace()
            fake_query.edit_message_text = success_msg.edit_text
            fake_query.message = success_msg
            fake_query.from_user = update.effective_user
            await self._show_channel_only_preview(fake_query, user_id, self.pending_products[user_id])
            return
        elif field == 'channel_text':
            # Salvar texto customizado do canal
            self.pending_products[user_id]['custom_channel_text'] = new_value
        elif field == 'custom_category':
            # Adicionar categoria personalizada
            categories = self.pending_products[user_id].get('categories', ['Electronics'])
            custom_category = new_value.strip()
            
            if custom_category and custom_category not in categories:
                categories.append(custom_category)
                self.pending_products[user_id]['categories'] = categories
        elif field == 'images':
            # Sistema novo de imagens passo a passo
            if new_value.strip() == '0':
                # Usuário quer finalizar com as imagens que já enviou
                edit_info = self.editing_products[user_id]
                
                if edit_info['images']:  # Se já enviou algumas imagens
                    # SALVAR as imagens que já foram enviadas
                    logger.info(f"Finalizando com {len(edit_info['images'])} imagens enviadas")
                    logger.info(f"ANTES da atualização - Imagens originais: {self.pending_products[user_id].get('images', [])}")
                    logger.info(f"ANTES da atualização - Novas imagens: {edit_info['images']}")
                    
                    # FORÇAR a atualização das imagens
                    new_images = edit_info['images'].copy()
                    self.pending_products[user_id]['images'] = new_images
                    
                    logger.info(f"DEPOIS da atualização - Imagens no produto: {self.pending_products[user_id]['images']}")
                    
                    del self.editing_products[user_id]
                    success_msg = await update.message.reply_text(f"✅ {len(new_images)} imagens salvas! Voltando ao preview...")
                else:
                    # Se não enviou nenhuma imagem, só voltar
                    del self.editing_products[user_id]
                    success_msg = await update.message.reply_text("🔙 Voltando ao preview sem alterar imagens...")
                
                # Debug: verificar se os dados estão preservados
                logger.info(f"Voltando ao preview, produto: {self.pending_products[user_id]}")
                
                try:
                    await self._show_simple_preview_after_edit(update, user_id, success_msg)
                except Exception as e:
                    logger.error(f"Erro ao mostrar preview: {e}")
                    await success_msg.edit_text(f"❌ Erro ao mostrar preview: {str(e)}")
                return
            
            # Adicionar imagem à lista
            edit_info = self.editing_products[user_id]
            edit_info['images'].append(new_value.strip())
            current_step = edit_info['current_step']
            max_images = edit_info['max_images']
            
            if current_step < max_images:
                # Pedir próxima imagem
                edit_info['current_step'] += 1
                next_step = edit_info['current_step']
                
                await update.message.reply_text(
                    f"✅ Imagem {current_step} recebida!\n\n"
                    f"📸 Editar Imagens ({next_step}/{max_images})\n\n"
                    f"📷 Envie o link da {self._get_ordinal(next_step)} imagem:\n"
                    f"Ou digite 0 para finalizar e voltar ao preview"                )
                return
            else:
                # Finalizar edição de imagens
                logger.info(f"ANTES da atualização - Imagens originais: {self.pending_products[user_id].get('images', [])}")
                logger.info(f"ANTES da atualização - Novas imagens: {edit_info['images']}")
                
                # FORÇAR a atualização das imagens
                new_images = edit_info['images'].copy()  # Fazer uma cópia
                self.pending_products[user_id]['images'] = new_images
                
                # Verificar se realmente foi atualizado
                logger.info(f"DEPOIS da atualização - Imagens no produto: {self.pending_products[user_id]['images']}")
                logger.info(f"Verificação - São iguais às novas? {self.pending_products[user_id]['images'] == new_images}")
                logger.info(f"Imagens atualizadas para usuário {user_id}: {len(edit_info['images'])} imagens")
                
                # Limpar estado de edição
                del self.editing_products[user_id]
                
                # Mostrar preview atualizado
                success_msg = await update.message.reply_text(f"✅ {len(edit_info['images'])} imagens atualizadas! Aqui está o preview:")
                
                # Debug: verificar se os dados ainda estão lá
                logger.info(f"Produto FINAL após atualização de imagens: {self.pending_products[user_id]}")
                
                try:
                    await self._show_simple_preview_after_edit(update, user_id, success_msg)
                except Exception as e:
                    logger.error(f"Erro ao mostrar preview após 4 imagens: {e}")
                    await success_msg.edit_text(f"❌ Erro ao mostrar preview: {str(e)}")
                return
        
        # Limpar estado de edição
        del self.editing_products[user_id]
        
        # Verificar se estamos editando texto do canal (após Shopify)
        if field == 'channel_text':
            # Voltar para o menu do canal (não para edição do produto)
            try:
                product_info = self.pending_products[user_id]
                shopify_result = product_info.get('shopify_result')
                affiliate_link = product_info.get('affiliate_link')
                
                if shopify_result and affiliate_link:
                    # Voltar para o preview do canal
                    success_msg = await update.message.reply_text("✅ Texto do canal atualizado!")
                    await self._show_channel_preview_with_confirmation_by_message(user_id, success_msg.message_id, product_info, affiliate_link, shopify_result)
                else:
                    await update.message.reply_text("✅ Texto atualizado! Use /start para continuar.")
            except Exception as e:
                logger.error(f"Erro ao voltar para preview do canal: {e}")
                await update.message.reply_text("✅ Texto atualizado! Use /start para continuar.")
        elif field == 'custom_category':
            # Voltar para gerenciamento de categorias
            try:
                custom_category = new_value.strip()
                if custom_category:
                    success_msg = await update.message.reply_text(f"✅ Categoria '{custom_category}' adicionada!")
                    # Aguardar 1 segundo e voltar ao gerenciamento
                    import asyncio
                    await asyncio.sleep(1)
                    # Simular query para voltar ao gerenciamento
                    from types import SimpleNamespace
                    fake_query = SimpleNamespace()
                    fake_query.edit_message_text = success_msg.edit_text
                    fake_query.message = success_msg
                    await self._show_category_management(fake_query, user_id)
                else:
                    await update.message.reply_text("❌ Nome da categoria não pode estar vazio!")
            except Exception as e:
                logger.error(f"Erro ao adicionar categoria personalizada: {e}")
                await update.message.reply_text("❌ Erro ao adicionar categoria. Tente novamente.")
        else:
            # Mostrar preview normal do produto (antes do Shopify)
            success_msg = await update.message.reply_text("✅ Atualizado! Aqui está o preview:")
            await self._show_product_preview_with_edit(update, self.pending_products[user_id], success_msg)
    
    async def _handle_channel_only_flow(self, query, user_id: int):
        """Fluxo simplificado: apenas canal do Telegram (só título, primeira imagem, preço)"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        product_info = self.pending_products[user_id]
        
        # Marcar como fluxo simplificado
        product_info['channel_only'] = True
        
        # Mostrar preview simplificado
        await self._show_channel_only_preview(query, user_id, product_info)
    
    async def _show_channel_only_preview(self, query, user_id: int, product_info: Dict):
        """Mostra preview simplificado para canal apenas"""
        title = product_info.get('title', 'Sem título')
        price_info = product_info.get('price', {})
        current_price = price_info.get('current', 0)
        original_price = price_info.get('original', current_price)
        discount = price_info.get('discount_percent', 0)
        images = product_info.get('images', [])
        first_image = images[0] if images else 'Nenhuma imagem'
        
        preview_text = f"""
📢 PREVIEW PARA CANAL DO TELEGRAM

📝 Título: {title}

💰 Preço Atual: ${current_price:.2f}
{f"💰 Preço Original: ${original_price:.2f}" if original_price > current_price else ""}
{f"💥 Desconto: {discount}% OFF" if discount > 0 else ""}

🖼️ Primeira Imagem: {first_image[:50]}{"..." if len(first_image) > 50 else ""}

✏️ Você pode editar antes de postar:
        """
        
        keyboard = [
            [InlineKeyboardButton("✏️ Editar Título", callback_data="channel_edit_title")],
            [InlineKeyboardButton("🖼️ Editar Primeira Imagem", callback_data="channel_edit_image")],
            [InlineKeyboardButton("💰 Editar Preço", callback_data="channel_edit_price")],
            [InlineKeyboardButton("✅ Postar no Canal", callback_data="channel_post_direct")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(preview_text, reply_markup=reply_markup)
    
    async def _start_channel_edit_title(self, query, user_id: int):
        """Inicia edição do título no fluxo simplificado"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        current_title = self.pending_products[user_id].get('title', 'Sem título')
        
        await query.edit_message_text(
            f"✏️ Editar Título\n\n"
            f"Título atual: {current_title}\n\n"
            f"Digite o novo título:"
        )
        
        self.editing_products[user_id] = {'field': 'channel_title', 'message_id': query.message.message_id}
    
    async def _start_channel_edit_image(self, query, user_id: int):
        """Inicia edição da primeira imagem no fluxo simplificado"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        images = self.pending_products[user_id].get('images', [])
        current_image = images[0] if images else 'Nenhuma imagem'
        
        await query.edit_message_text(
            f"🖼️ Editar Primeira Imagem\n\n"
            f"Imagem atual: {current_image[:50]}{'...' if len(current_image) > 50 else ''}\n\n"
            f"📷 Envie o link da nova primeira imagem:"
        )
        
        self.editing_products[user_id] = {'field': 'channel_image', 'message_id': query.message.message_id}
    
    async def _start_channel_edit_price(self, query, user_id: int):
        """Inicia edição do preço no fluxo simplificado"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        price_info = self.pending_products[user_id].get('price', {})
        current_price = price_info.get('current', 0)
        original_price = price_info.get('original', current_price)
        
        await query.edit_message_text(
            f"💰 Editar Preços\n\n"
            f"Preço atual: ${current_price:.2f}\n"
            f"Preço original: ${original_price:.2f}\n\n"
            f"Digite os novos preços no formato:\n"
            f"`preço_atual,preço_original`\n\n"
            f"Exemplo: `39.90,69.90`"
        )
        
        self.editing_products[user_id] = {'field': 'channel_price', 'message_id': query.message.message_id}
    
    async def _post_channel_direct(self, query, user_id: int, context):
        """Posta diretamente no canal do Telegram (sem Shopify)"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        product_info = self.pending_products[user_id]
        affiliate_link = product_info.get('original_url', '')
        
        # Criar um shopify_result fake para usar a função existente
        fake_shopify_result = {'url': 'N/A', 'title': product_info.get('title', 'Produto')}
        
        await query.edit_message_text("🚀 Postando no canal...")
        
        # Postar no canal
        await self._post_to_telegram_channel(product_info, fake_shopify_result, affiliate_link, context)
        
        # Gerar texto formatado para preview
        formatted_text = self._format_channel_text_for_copy(product_info, affiliate_link)
        
        # Mensagem de sucesso com preview (sem parse_mode para manter asteriscos visíveis)
        success_msg = f"""🎉 PRODUTO POSTADO NO CANAL!

📢 Canal: @hotdealsdailyf4l

━━━━━━━━━━━━━━━━━━━━

{formatted_text}"""
        
        await query.edit_message_text(success_msg)
        
        # Limpar produto pendente
        del self.pending_products[user_id]
    
    async def _publish_product(self, query, user_id: int, context):
        """Publica o produto no Shopify e canal"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        await query.edit_message_text("🚀 Publicando produto no Shopify...")
        
        try:
            product_info = self.pending_products[user_id]
            affiliate_link = product_info.get('original_url', '')
            
            # Debug: verificar dados antes de enviar para Shopify
            logger.info(f"Dados do produto sendo enviados para Shopify: {product_info}")
            logger.info(f"Imagens no produto: {product_info.get('images', [])}")
            
            # Criar produto no Shopify
            shopify_result = await self.shopify_manager.create_product(product_info, affiliate_link)
            
            if shopify_result:
                # Mostrar preview e aguardar confirmação
                await self._show_channel_preview_with_confirmation(query, product_info, affiliate_link, context, shopify_result)
            else:
                await query.edit_message_text("❌ Erro ao publicar no Shopify. Verifique as configurações.")
                # Limpar produto pendente apenas em caso de erro
                del self.pending_products[user_id]
            
        except Exception as e:
            logger.error(f"Erro ao publicar: {e}")
            await query.edit_message_text("❌ Erro ao publicar produto. Tente novamente.")
    
    async def _show_channel_preview_with_confirmation(self, query, product_info: Dict, affiliate_link: str, context, shopify_result: Dict):
        """Mostra preview do canal e aguarda confirmação"""
        try:
            user_id = query.from_user.id
            
            # Preparar dados
            title = product_info.get('title', 'Produto')
            price_info = product_info.get('price', {})
            current_price = price_info.get('current', 0)
            original_price = price_info.get('original', current_price)
            discount = price_info.get('discount_percent', 0)
            
            # Detectar loja para o botão
            button_text = self._get_button_text(affiliate_link)
            
            # Salvar dados para confirmação
            self.pending_products[user_id]['shopify_result'] = shopify_result
            self.pending_products[user_id]['affiliate_link'] = affiliate_link
            
            # Gerar texto do canal para preview
            if 'custom_channel_text' in product_info and product_info['custom_channel_text']:
                channel_text = product_info['custom_channel_text']
            else:
                if original_price > current_price:
                    channel_text = f"""🔥 *{title}*

💥 {discount}% OFF
${original_price:.2f} → ${current_price:.2f}"""
                else:
                    channel_text = f"""🔥 *{title}*

💰 ${current_price:.2f}"""
            
            # Mensagem de preview com botões de confirmação
            preview_message = f"""📺 PREVIEW DO CANAL:

{channel_text}

🖼️ Primeira imagem: {product_info.get('images', ['Nenhuma'])[0] if product_info.get('images') else 'Nenhuma'}
🔘 Botão: "{button_text}"

✅ Produto já foi criado no Shopify!
🤔 Deseja postar no canal do Telegram?"""
            
            # Botões de confirmação
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [
                    InlineKeyboardButton("✅ Postar no Canal", callback_data="confirm_post_channel"),
                    InlineKeyboardButton("✏️ Editar Texto", callback_data="edit_channel_text")
                ],
                [
                    InlineKeyboardButton("🔄 Editar Produto", callback_data="edit_channel_preview"),
                    InlineKeyboardButton("❌ Cancelar", callback_data="cancel_channel_post")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(preview_message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Erro ao mostrar preview com confirmação: {e}")

    async def _show_channel_preview_with_confirmation_by_message(self, user_id: int, message_id: int, product_info: Dict, affiliate_link: str, shopify_result: Dict):
        """Mostra preview do canal via message_id (para edição de texto)"""
        try:
            # Preparar dados
            title = product_info.get('title', 'Produto')
            price_info = product_info.get('price', {})
            current_price = price_info.get('current', 0)
            original_price = price_info.get('original', current_price)
            discount = price_info.get('discount_percent', 0)
            
            # Detectar loja para o botão
            button_text = self._get_button_text(affiliate_link)
            
            # Gerar texto do canal para preview
            if 'custom_channel_text' in product_info and product_info['custom_channel_text']:
                channel_text = product_info['custom_channel_text']
            else:
                if original_price > current_price:
                    channel_text = f"""🔥 *{title}*

💥 {discount}% OFF
${original_price:.2f} → ${current_price:.2f}"""
                else:
                    channel_text = f"""🔥 *{title}*

💰 ${current_price:.2f}"""
            
            # Mensagem de preview com botões de confirmação
            preview_message = f"""📺 PREVIEW DO CANAL ATUALIZADO:

{channel_text}

🖼️ Primeira imagem: {product_info.get('images', ['Nenhuma'])[0] if product_info.get('images') else 'Nenhuma'}
🔘 Botão: "{button_text}"

✅ Produto já foi criado no Shopify!
🤔 Deseja postar no canal do Telegram?"""
            
            # Botões de confirmação
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [
                    InlineKeyboardButton("✅ Postar no Canal", callback_data="confirm_post_channel"),
                    InlineKeyboardButton("✏️ Editar Texto", callback_data="edit_channel_text")
                ],
                [
                    InlineKeyboardButton("🔄 Editar Produto", callback_data="edit_channel_preview"),
                    InlineKeyboardButton("❌ Cancelar", callback_data="cancel_channel_post")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Usar o bot atual para editar a mensagem
            from telegram.ext import Application
            current_app = Application.get_running()
            if current_app:
                await current_app.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text=preview_message,
                    reply_markup=reply_markup
                )
            else:
                logger.error("Não foi possível obter a aplicação atual")
            
        except Exception as e:
            logger.error(f"Erro ao mostrar preview do canal por message_id: {e}")

    def _get_button_text(self, affiliate_link: str) -> str:
        """Detecta a loja e retorna o texto apropriado para o botão"""
        link_lower = affiliate_link.lower()
        
        if 'amazon' in link_lower or 'amzn' in link_lower:
            return "🛒 Buy on Amazon"
        elif 'walmart' in link_lower:
            return "🛒 Buy on Walmart"
        elif 'target' in link_lower:
            return "🛒 Buy on Target"
        elif 'ebay' in link_lower:
            return "🛒 Buy on eBay"
        elif 'aliexpress' in link_lower:
            return "🛒 Buy on AliExpress"
        else:
            return "🛒 Get This Promo"
    
    def _convert_to_telegram_markdown(self, text: str) -> str:
        """Converte ~texto~ para ~~texto~~ (formato do Telegram)"""
        import re
        # Converte ~texto~ para ~~texto~~ (mas não ~~texto~~ que já está correto)
        # Usa regex para encontrar ~texto~ que não seja ~~texto~~
        pattern = r'(?<!~)~([^~]+)~(?!~)'
        return re.sub(pattern, r'~~\1~~', text)
    
    def _format_channel_text_for_copy(self, product_info: Dict, affiliate_link: str) -> str:
        """Gera o texto formatado para copiar (WhatsApp)"""
        title = product_info.get('title', 'Produto')
        price_info = product_info.get('price', {})
        current_price = price_info.get('current', 0)
        original_price = price_info.get('original', current_price)
        discount = price_info.get('discount_percent', 0)
        
        # Limpar título (remover espaços extras)
        title = ' '.join(title.split()) if title else 'Produto'
        
        # Usar texto customizado se existir, senão usar padrão
        if 'custom_channel_text' in product_info and product_info['custom_channel_text']:
            # Se tiver texto customizado, verificar se já tem o link
            custom_text = product_info['custom_channel_text']
            # Se o texto customizado já contém o link, usar como está
            if affiliate_link in custom_text:
                return custom_text
            # Senão, adicionar o link no final (1 linha em branco)
            return f"{custom_text}\n\nLink: {affiliate_link}"
        else:
            # Formato padrão com espaçamentos corretos (1 linha em branco entre seções)
            if original_price > current_price:
                return f"""🔥 *{title}*

💥 {discount}% OFF

~${original_price:.2f}~ → ${current_price:.2f}

Link: {affiliate_link}"""
            else:
                return f"""🔥 *{title}*

💰 ${current_price:.2f}

Link: {affiliate_link}"""

    async def _post_to_telegram_channel(self, product_info: Dict, shopify_result: Dict, affiliate_link: str, context):
        """Posta produto no canal do Telegram"""
        try:
            if not Config.TELEGRAM_CHANNEL_ID:
                logger.error("TELEGRAM_CHANNEL_ID não configurado")
                return
            
            logger.info(f"Postando no canal: {Config.TELEGRAM_CHANNEL_ID}")
            
            # Preparar mensagem
            title = product_info.get('title', 'Produto')
            price_info = product_info.get('price', {})
            current_price = price_info.get('current', 0)
            original_price = price_info.get('original', current_price)
            discount = price_info.get('discount_percent', 0)
            
            # Usar texto customizado se existir, senão usar padrão
            if 'custom_channel_text' in product_info and product_info['custom_channel_text']:
                # Converter ~texto~ para ~~texto~~ (formato do Telegram)
                message = self._convert_to_telegram_markdown(product_info['custom_channel_text'])
            else:
                # Mensagem formatada padrão (sem o link, vai no botão)
                if original_price > current_price:
                    # Usar strikethrough para preço original (Telegram usa ~~texto~~)
                    message = f"""🔥 *{title}*

💥 {discount}% OFF

~~${original_price:.2f}~~ → ${current_price:.2f}"""
                else:
                    message = f"""🔥 *{title}*

💰 ${current_price:.2f}"""
            
            logger.info(f"Mensagem preparada: {message[:100]}...")
            
            # Criar botão inteligente baseado na loja
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            button_text = self._get_button_text(affiliate_link)
            keyboard = [[InlineKeyboardButton(button_text, url=affiliate_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Enviar primeira imagem com a mensagem e botão
            images = product_info.get('images', [])
            if images:
                logger.info(f"Enviando com imagem: {images[0]}")
                result = await context.bot.send_photo(
                    chat_id=Config.TELEGRAM_CHANNEL_ID,
                    photo=images[0],
                    caption=message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                logger.info(f"Postagem no canal enviada com sucesso: {result.message_id}")
            else:
                logger.info("Enviando sem imagem")
                result = await context.bot.send_message(
                    chat_id=Config.TELEGRAM_CHANNEL_ID,
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                logger.info(f"Postagem no canal enviada com sucesso: {result.message_id}")
                
        except Exception as e:
            logger.error(f"Erro ao postar no canal {Config.TELEGRAM_CHANNEL_ID}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    async def _confirm_post_channel(self, query, user_id: int, context):
        """Confirma e posta no canal"""
        try:
            if user_id not in self.pending_products:
                await query.edit_message_text("❌ Produto não encontrado.")
                return
            
            product_info = self.pending_products[user_id]
            shopify_result = product_info.get('shopify_result')
            affiliate_link = product_info.get('affiliate_link')
            
            if not shopify_result or not affiliate_link:
                await query.edit_message_text("❌ Dados do produto não encontrados.")
                return
            
            await query.edit_message_text("🚀 Postando no canal...")
            
            # Postar no canal
            await self._post_to_telegram_channel(product_info, shopify_result, affiliate_link, context)
            
            # Gerar texto formatado para preview
            formatted_text = self._format_channel_text_for_copy(product_info, affiliate_link)
            
            # Mensagem de sucesso com preview (sem parse_mode para manter asteriscos visíveis)
            categories = product_info.get('categories', ['Electronics'])
            categories_text = " | ".join(categories)
            
            success_msg = f"""🎉 PRODUTO PUBLICADO COM SUCESSO!
🛍️ Shopify: {shopify_result['url']}
📢 Canal: Postado em @hotdealsdailyf4l

━━━━━━━━━━━━━━━━━━━━

{formatted_text}"""
            
            await query.edit_message_text(success_msg)
            
            # Limpar produto pendente
            del self.pending_products[user_id]
            
        except Exception as e:
            logger.error(f"Erro ao confirmar postagem: {e}")
            await query.edit_message_text("❌ Erro ao postar no canal.")

    async def _edit_channel_text(self, query, user_id: int):
        """Permite editar o texto que será postado no canal"""
        try:
            if user_id not in self.pending_products:
                await query.edit_message_text("❌ Produto não encontrado.")
                return
            
            product_info = self.pending_products[user_id]
            
            # Gerar texto atual do canal
            title = product_info.get('title', 'Produto')
            price_info = product_info.get('price', {})
            current_price = price_info.get('current', 0)
            original_price = price_info.get('original', current_price)
            discount = price_info.get('discount_percent', 0)
            
            if original_price > current_price:
                current_text = f"""🔥 {title}

💥 {discount}% OFF
${original_price:.2f} → ${current_price:.2f}"""
            else:
                current_text = f"""🔥 {title}

💰 ${current_price:.2f}"""
            
            # Salvar texto atual se não existir
            if 'custom_channel_text' not in product_info:
                product_info['custom_channel_text'] = current_text
            
            edit_message = f"""✏️ EDITAR TEXTO DO CANAL

📝 Texto atual:
{product_info.get('custom_channel_text', current_text)}

💡 Exemplos de modificações:
• Adicionar cupons: "Clip 5% coupon + use code: ABC123"
• Adicionar informações: "Price drop", "Limited time"
• Modificar qualquer parte do texto

📱 Digite o novo texto completo:"""
            
            await query.edit_message_text(edit_message)
            
            # Armazenar estado de edição
            self.editing_products[user_id] = {
                'field': 'channel_text', 
                'message_id': query.message.message_id
            }
            
        except Exception as e:
            logger.error(f"Erro ao editar texto do canal: {e}")
            await query.edit_message_text("❌ Erro ao editar texto. Tente novamente.")

    async def _edit_channel_preview(self, query, user_id: int):
        """Permite editar o preview do canal"""
        try:
            if user_id not in self.pending_products:
                await query.edit_message_text("❌ Produto não encontrado.")
                return
            
            # Limpar dados do Shopify para permitir nova edição
            product_info = self.pending_products[user_id]
            if 'shopify_result' in product_info:
                del product_info['shopify_result']
            if 'affiliate_link' in product_info:
                del product_info['affiliate_link']
            
            # Voltar para o preview de edição normal
            from types import SimpleNamespace
            fake_update = SimpleNamespace()
            await self._show_product_preview_with_edit(fake_update, product_info, query.message)
            
        except Exception as e:
            logger.error(f"Erro ao editar preview: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await query.edit_message_text("❌ Erro ao editar preview. Tente novamente.")

    async def _cancel_channel_post(self, query, user_id: int):
        """Cancela a postagem no canal"""
        try:
            if user_id not in self.pending_products:
                await query.edit_message_text("❌ Produto não encontrado.")
                return
            
            product_info = self.pending_products[user_id]
            shopify_result = product_info.get('shopify_result')
            
            # Mensagem informando que o produto foi criado no Shopify mas não postado no canal
            msg = f"""✅ Produto criado no Shopify com sucesso!
🛍️ URL: {shopify_result['url'] if shopify_result else 'N/A'}

❌ Postagem no canal cancelada.

O produto está disponível no seu Shopify, mas não foi divulgado no canal do Telegram."""
            
            await query.edit_message_text(msg)
            
            # Limpar produto pendente
            del self.pending_products[user_id]
            
        except Exception as e:
            logger.error(f"Erro ao cancelar postagem: {e}")
            await query.edit_message_text("❌ Erro ao cancelar.")
    
    async def _show_category_management(self, query, user_id: int):
        """Mostra gerenciamento de categorias"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        categories = self.pending_products[user_id].get('categories', ['Electronics'])
        categories_text = " | ".join(categories)
        
        # Botões para remover categorias existentes
        remove_buttons = []
        for cat in categories:
            if len(categories) > 1:  # Manter pelo menos uma categoria
                callback_data = f"remove_cat_{cat.replace(' ', '_')}"
                remove_buttons.append([InlineKeyboardButton(f"❌ {cat}", callback_data=callback_data)])
        
        keyboard = [
            [InlineKeyboardButton("➕ Categoria Principal", callback_data="add_main_category")],
            [InlineKeyboardButton("🔥 Categoria de Desconto", callback_data="add_discount_category")],
        ] + remove_buttons + [
            [InlineKeyboardButton("🔙 Voltar ao Preview", callback_data="back_to_preview")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🏷️ Gerenciar Categorias\n\n"
            f"Categorias atuais: {categories_text}\n\n"
            f"Escolha uma opção:",
            reply_markup=reply_markup
        )
    
    async def _show_main_categories(self, query, user_id: int):
        """Mostra categorias principais"""
        from config import SHOPIFY_CATEGORIES
        
        keyboard = []
        for i in range(0, len(SHOPIFY_CATEGORIES), 2):
            row = []
            for j in range(2):
                if i + j < len(SHOPIFY_CATEGORIES):
                    category = SHOPIFY_CATEGORIES[i + j]
                    callback_data = f"main_cat_{category.replace(' ', '_').replace('&', 'and')}"
                    row.append(InlineKeyboardButton(category, callback_data=callback_data))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="manage_categories")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🏷️ Categorias Principais\n\nSelecione uma categoria:",
            reply_markup=reply_markup
        )
    
    async def _show_discount_categories(self, query, user_id: int):
        """Mostra categorias de desconto"""
        from config import DISCOUNT_CATEGORIES
        
        keyboard = []
        for i in range(0, len(DISCOUNT_CATEGORIES), 3):
            row = []
            for j in range(3):
                if i + j < len(DISCOUNT_CATEGORIES):
                    category = DISCOUNT_CATEGORIES[i + j]
                    callback_data = f"disc_cat_{category}"
                    row.append(InlineKeyboardButton(category, callback_data=callback_data))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="manage_categories")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔥 Categorias de Desconto\n\nSelecione uma categoria:",
            reply_markup=reply_markup
        )
    
    async def _add_category(self, query, user_id: int, category: str):
        """Adiciona categoria ao produto"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        # Se for "Other", pedir para digitar categoria personalizada
        if category == "Other":
            await query.edit_message_text(
                "✏️ CATEGORIA PERSONALIZADA\n\n"
                "Digite o nome da categoria que você deseja:\n\n"
                "Exemplos:\n"
                "• Kitchen Appliances\n"
                "• Smart Home\n"
                "• Outdoor Gear\n"
                "• Beauty Products\n\n"
                "📱 Digite a categoria:"
            )
            
            # Armazenar estado de edição
            self.editing_products[user_id] = {
                'field': 'custom_category', 
                'message_id': query.message.message_id
            }
            return
        
        categories = self.pending_products[user_id].get('categories', ['Electronics'])
        
        if category not in categories:
            categories.append(category)
            self.pending_products[user_id]['categories'] = categories
            
            await query.edit_message_text(f"✅ Categoria '{category}' adicionada!")
        else:
            await query.edit_message_text(f"⚠️ Categoria '{category}' já existe!")
        
        # Voltar ao gerenciamento após 1 segundo
        import asyncio
        await asyncio.sleep(1)
        await self._show_category_management(query, user_id)
    
    async def _remove_category(self, query, user_id: int, category: str):
        """Remove categoria do produto"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        categories = self.pending_products[user_id].get('categories', ['Electronics'])
        
        if len(categories) > 1 and category in categories:
            categories.remove(category)
            self.pending_products[user_id]['categories'] = categories
            
            await query.edit_message_text(f"✅ Categoria '{category}' removida!")
        else:
            await query.edit_message_text(f"⚠️ Deve ter pelo menos uma categoria!")
        
        # Voltar ao gerenciamento após 1 segundo
        import asyncio
        await asyncio.sleep(1)
        await self._show_category_management(query, user_id)
    
    async def _back_to_preview(self, query, user_id: int):
        """Volta ao preview do produto"""
        if user_id not in self.pending_products:
            await query.edit_message_text("❌ Produto não encontrado.")
            return
        
        product_info = self.pending_products[user_id]
        
        # Mostrar preview simples
        title = product_info.get('title', 'N/A')
        price_info = product_info.get('price', {})
        current_price = price_info.get('current', 0)
        original_price = price_info.get('original', current_price)
        discount = price_info.get('discount_percent', 0)
        description = product_info.get('description', 'N/A')
        categories = product_info.get('categories', ['Electronics'])
        categories_text = " | ".join(categories)
        
        preview_text = f"""
📦 PRODUTO ATUALIZADO
📝 Título: {title}

🏷️ Categorias: {categories_text}

💰 Preços:• Atual: R$ {current_price:.2f}
{f"• Original: R$ {original_price:.2f}" if original_price > current_price else ""}
{f"• Desconto: {discount}% OFF" if discount > 0 else ""}

📸 Imagens: {len(product_info.get('images', []))}

📄 Descrição: {description[:100]}{"..." if len(description) > 100 else ""}

O que deseja fazer?        """
        
        keyboard = [
            [InlineKeyboardButton("✏️ Editar Título", callback_data="edit_title")],
            [InlineKeyboardButton("🏷️ Gerenciar Categorias", callback_data="manage_categories")],
            [InlineKeyboardButton("💰 Editar Preços", callback_data="edit_prices")],
            [InlineKeyboardButton("📄 Editar Descrição", callback_data="edit_description")],
            [InlineKeyboardButton("📸 Editar Imagens", callback_data="edit_images")],
            [InlineKeyboardButton("✅ Publicar Assim", callback_data="publish_as_is")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(preview_text, reply_markup=reply_markup)
    
    def _get_ordinal(self, num: int) -> str:
        """Converte número em ordinal (1->PRIMEIRA, 2->SEGUNDA, etc.)"""
        ordinals = {
            1: "PRIMEIRA",
            2: "SEGUNDA", 
            3: "TERCEIRA",
            4: "QUARTA"
        }
        return ordinals.get(num, f"{num}ª")
    
    async def _show_simple_preview_after_edit(self, update: Update, user_id: int, msg_to_edit):
        """Mostra preview simples após edição"""
        if user_id not in self.pending_products:
            await msg_to_edit.edit_text("❌ Produto não encontrado.")
            return
        
        product_info = self.pending_products[user_id]
        
        # Escapar textos para evitar problemas com Markdown
        title = product_info.get('title', 'Sem título')
        price_info = product_info.get('price', {})
        current_price = price_info.get('current', 0)
        original_price = price_info.get('original', current_price)
        discount = price_info.get('discount_percent', 0)
        description = product_info.get('description', 'Sem descrição')
        categories = product_info.get('categories', ['Electronics'])
        categories_text = " | ".join(categories)
        images = product_info.get('images', [])
        images_count = len(images)
        
        # Mostrar URLs das imagens (simplificado)
        images_text = ""
        if images:
            images_text = f"\nSuas imagens:\n"
            for i, img in enumerate(images[:3], 1):
                images_text += f"{i}. {img[:50]}...\n"
            if len(images) > 3:
                images_text += f"... e mais {len(images) - 3} imagens\n"
        
        affiliate_link = product_info.get('original_url', 'Não informado')
        
        # Usar texto simples sem Markdown para evitar erros de parsing
        preview_text = f"""
📦 PRODUTO ATUALIZADO

📝 Título: {product_info.get('title', 'Sem título')}

🏷️ Categorias: {categories_text}

💰 Preços:
• Atual: R$ {current_price:.2f}
{f"• Original: R$ {original_price:.2f}" if original_price > current_price else ""}
{f"• Desconto: {discount}% OFF" if discount > 0 else ""}

📸 Imagens: {images_count} encontradas{images_text}

📄 Descrição: {product_info.get('description', 'Sem descrição')[:100]}{"..." if len(product_info.get('description', '')) > 100 else ""}

🔗 Link Afiliado: {affiliate_link}

O que deseja fazer?
        """
        
        keyboard = [
            [InlineKeyboardButton("✏️ Editar Título", callback_data="edit_title")],
            [InlineKeyboardButton("🏷️ Gerenciar Categorias", callback_data="manage_categories")],
            [InlineKeyboardButton("💰 Editar Preços", callback_data="edit_prices")],
            [InlineKeyboardButton("📄 Editar Descrição", callback_data="edit_description")],
            [InlineKeyboardButton("📸 Editar Imagens", callback_data="edit_images")],
            [InlineKeyboardButton("✅ Publicar Assim", callback_data="publish_as_is")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Sem parse_mode para evitar problemas com caracteres especiais
        await msg_to_edit.edit_text(preview_text, reply_markup=reply_markup)
    
    def _is_valid_url(self, url: str) -> bool:
        """Verifica se a URL é válida"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

def main():
    """Função principal do bot"""
    if not Config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN não configurado!")
        return
    
    # Criar aplicação
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Criar instância do bot
    bot = TelegramBotWithEdit()
    
    # Adicionar handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'^https?://'), bot.handle_url))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_edit_input))
    
    # Iniciar bot
    logger.info("🤖 Bot com Edição iniciado!")
    logger.info("✏️ Funcionalidade de edição ativa")
    
    application.run_polling()

if __name__ == '__main__':
    main()
