# 🚀 Como Usar o Bot de Importação de Produtos

## ⚡ Início Rápido

### 1. Instalação Automática
```bash
python setup.py
```
Este script vai:
- Instalar todas as dependências
- Criar arquivo de configuração
- Guiar você através das configurações necessárias

### 2. Configuração Manual (se preferir)

#### 2.1. Instalar dependências
```bash
pip install -r requirements.txt
```

#### 2.2. Configurar variáveis
Edite o arquivo `config.env` com suas informações:

```env
# Bot do Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHANNEL_ID=@meucanal

# Shopify
SHOPIFY_SHOP_URL=minhaloja.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_1234567890abcdef

# OpenAI (opcional)
OPENAI_API_KEY=sk-1234567890abcdef
```

### 3. Testar Configurações
```bash
python test_bot.py
```

### 4. Iniciar o Bot
```bash
python start.py
# ou
python bot.py
```

## 📱 Como Usar no Telegram

### 1. Comandos Disponíveis
- `/start` - Iniciar o bot
- `/help` - Mostrar ajuda
- `/status` - Verificar configurações

### 2. Importar um Produto

1. **Envie o link do produto**
   ```
   https://www.amazon.com.br/produto-exemplo/dp/B123456789
   ```

2. **Revise as informações extraídas**
   - Título
   - Preços (atual e original)
   - Desconto calculado
   - Imagens encontradas
   - Descrição

3. **Confirme a publicação**
   - Clique em "✅ Publicar no Shopify"
   - O bot criará o produto no Shopify
   - Postará automaticamente no canal

## 🛍️ Sites Suportados

### ✅ Totalmente Suportados
- **Amazon** (amazon.com.br, amazon.com)
- **Mercado Livre** (mercadolivre.com.br)
- **AliExpress** (aliexpress.com)
- **Shopee** (shopee.com.br)
- **Magazine Luiza** (magazineluiza.com.br)
- **Americanas** (americanas.com.br)

### ⚠️ Suporte Genérico
- Outros sites de e-commerce
- Pode funcionar com qualquer site que tenha estrutura HTML padrão

## 🔧 Configurações Avançadas

### Metafields do Shopify
O bot cria automaticamente um metafield para links de afiliado:
- **Namespace:** `custom`
- **Key:** `affiliate_link`
- **Tipo:** `single_line_text_field`

### Personalizar Extração
Edite `config.env` para ajustar:
```env
# Máximo de imagens por produto
MAX_IMAGES=4

# Tamanho máximo da descrição
MAX_DESCRIPTION_LENGTH=500

# Timeout para requests
REQUEST_TIMEOUT=10
```

## 📊 Formato da Postagem no Canal

```
🔥 Nome do Produto Incrível

💥 25% OFF
~~R$ 69,90~~
💰 R$ 39,90

🛒 Link da Amazon (afiliado): https://...
```

## 🐛 Solução de Problemas

### Bot não responde
```bash
# Verificar configurações
python test_bot.py

# Verificar status
# No Telegram: /status
```

### Erro na extração de produtos
- Alguns sites podem bloquear bots
- Tente com URLs diferentes
- Verifique se o site está acessível

### Erro no Shopify
- Verifique permissões da API
- Confirme se o token está válido
- Teste conexão: `python test_bot.py`

### Não posta no canal
- Bot deve ser admin do canal
- Confirme o ID do canal (com @)
- Teste: `/status` no bot

## 📈 Próximas Funcionalidades

- [ ] Edição de produtos antes da publicação
- [ ] Múltiplas lojas Shopify
- [ ] Agendamento de postagens
- [ ] Interface web
- [ ] Relatórios de performance

## 🆘 Suporte

1. **Verificar logs do bot**
2. **Executar testes:** `python test_bot.py`
3. **Verificar configurações:** `/status` no Telegram
4. **Consultar README.md** para detalhes técnicos

## 📝 Dicas de Uso

### ✅ Boas Práticas
- Use URLs diretas dos produtos
- Verifique se as imagens carregaram
- Teste com diferentes sites
- Monitore o canal para ver as postagens

### ❌ Evite
- URLs de busca ou listagens
- Links muito longos com parâmetros
- Sites que requerem login
- URLs de redirecionamento

## 🔒 Segurança

- **Nunca compartilhe** seus tokens
- **Mantenha** o arquivo `config.env` privado
- **Use** tokens com permissões mínimas necessárias
- **Monitore** o uso da API do OpenAI (se configurado)

---

**🎉 Pronto! Seu bot está configurado e funcionando!**

Para mais detalhes técnicos, consulte o arquivo `README.md`.
