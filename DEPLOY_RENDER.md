# 🚀 Deploy no Render.com - Guia Completo

## 📋 **Passo a Passo:**

### 1. **Criar conta no Render.com**
- Acesse: https://render.com
- Faça login com GitHub (recomendado)

### 2. **Preparar repositório no GitHub**
- Crie um repositório no GitHub
- Faça upload de todos os arquivos do bot
- **⚠️ IMPORTANTE:** NÃO faça commit do `config.env`!
- Adicione `config.env` ao `.gitignore`

### 3. **Deploy no Render**

#### A. **Criar novo serviço:**
1. No dashboard do Render, clique em **"New +"**
2. Selecione **"Background Worker"**

#### B. **Configurar:**
- **Name:** `telegram-bot-finds4living`
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python3 bot_with_edit.py`

#### C. **Adicionar variáveis de ambiente:**
Clique em **"Environment"** e adicione:

```
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHANNEL_ID=@hotdealsdailyf4l
SHOPIFY_SHOP_URL=xpxhtv-dp.myshopify.com
SHOPIFY_ACCESS_TOKEN=seu_token_aqui
OPENAI_API_KEY=sua_chave_aqui
AFFILIATE_LINK_METAFIELD_NAMESPACE=custom.affiliate_link
AFFILIATE_LINK_METAFIELD_KEY=affiliate_link
MAX_IMAGES=4
MAX_DESCRIPTION_LENGTH=500
REQUEST_TIMEOUT=10
```

#### D. **Plano:**
- Selecione **"Free"** (plano gratuito)

### 4. **Deploy:**
- Clique em **"Create Background Worker"**
- Render vai fazer build automaticamente
- Aguarde alguns minutos

### 5. **Verificar logs:**
- Vá em **"Logs"** para ver se está funcionando
- Deve aparecer: `🤖 Bot com Edição iniciado!`

## ✅ **Pronto!**
Seu bot está rodando 24/7 no Render.com!

## 🔧 **Manter bot ativo (opcional):**
Para evitar hibernação, você pode adicionar um keep-alive:
- Usar serviço como UptimeRobot para pingar
- Ou deixar o bot sempre fazendo polling (já faz isso)

## 📝 **Notas:**
- ✅ Render gratuito pode hibernar após 15min sem atividade
- ✅ Com polling constante, geralmente não hiberna
- ✅ Se hibernar, acorda automaticamente quando recebe mensagem
- ✅ Pode levar alguns segundos para acordar

## 🆘 **Troubleshooting:**
- **Bot não responde:** Verifique logs no Render
- **Erro de variáveis:** Confira se todas estão configuradas
- **Bot hiberna:** Normal no plano gratuito, acorda sozinho
