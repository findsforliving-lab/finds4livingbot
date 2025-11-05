# 🚀 Deploy no Replit - Guia Completo

## 📋 **Passo a Passo:**

### 1. **Criar conta no Replit**
- Acesse: https://replit.com
- Faça login com GitHub (recomendado)

### 2. **Importar repositório do GitHub**

#### A. **Criar novo Repl:**
1. No dashboard do Replit, clique em **"Create Repl"** ou **"+"**
2. Selecione **"Import from GitHub"**
3. Cole a URL: `https://github.com/findsforliving-lab/finds4livingbot`
4. Clique em **"Import"**

#### B. **Ou criar manualmente:**
1. Clique em **"Create Repl"**
2. Escolha **"Python"** como linguagem
3. Nome: `telegram-bot-finds4living`
4. Depois faça upload dos arquivos ou conecte ao GitHub

### 3. **Configurar variáveis de ambiente (secrets)**

No Replit, as variáveis de ambiente são chamadas de **"Secrets"**:

1. Clique no ícone de **"Secrets"** (cadeado) na barra lateral esquerda
2. Ou vá em **"Tools"** > **"Secrets"**
3. Adicione cada variável:

```
TELEGRAM_BOT_TOKEN = seu_token_aqui
TELEGRAM_CHANNEL_ID = @hotdealsdailyf4l
SHOPIFY_SHOP_URL = xpxhtv-dp.myshopify.com
SHOPIFY_ACCESS_TOKEN = seu_token_aqui
OPENAI_API_KEY = sua_chave_aqui
AFFILIATE_LINK_METAFIELD_NAMESPACE = custom.affiliate_link
AFFILIATE_LINK_METAFIELD_KEY = affiliate_link
MAX_IMAGES = 4
MAX_DESCRIPTION_LENGTH = 500
REQUEST_TIMEOUT = 10
```

### 4. **Instalar dependências**

No console do Replit, execute:
```bash
pip install -r requirements.txt
```

### 5. **Executar o bot**

1. Clique no botão **"Run"** (verde)
2. Ou execute no console: `python3 bot_with_edit.py`
3. O bot deve iniciar!

### 6. **Manter bot rodando (Free Plan)**

⚠️ **IMPORTANTE:** No plano gratuito do Replit, o bot pode parar após inatividade.

#### **Soluções:**

**A. Always On (pago):**
- Replit oferece "Always On" por ~$5/mês
- Bot fica rodando 24/7

**B. Keep-Alive (gratuito):**
- Use um serviço como UptimeRobot para fazer ping
- Ou adicione um keep-alive no código

**C. Reexecutar quando necessário:**
- Bot para após inatividade
- Reexecuta quando você volta
- Telegram envia mensagens pendentes

### 7. **Configurar Keep-Alive (opcional)**

Se quiser manter ativo gratuitamente, adicione um endpoint HTTP:

```python
# Adicione no final do bot_with_edit.py
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# Rode em thread separada
import threading
def run_flask():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask, daemon=True).start()
```

E configure UptimeRobot para fazer ping a cada 5 minutos.

## ✅ **Vantagens do Replit:**
- ✅ Gratuito
- ✅ Interface visual
- ✅ Fácil de configurar
- ✅ Suporta Python perfeitamente
- ✅ Logs em tempo real

## ⚠️ **Limitações do plano gratuito:**
- ⚠️ Pode hibernar após inatividade
- ⚠️ Recursos limitados
- ⚠️ Always On é pago

## 🎯 **Próximos passos:**
1. Importe o repositório no Replit
2. Configure os Secrets
3. Execute o bot
4. Teste enviando um produto!

## 🆘 **Troubleshooting:**
- **Bot não inicia:** Verifique os Secrets
- **Erro de import:** Verifique se requirements.txt está correto
- **Bot para:** Normal no free plan, apenas reexecute
