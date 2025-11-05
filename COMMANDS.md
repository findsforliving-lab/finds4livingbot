# 🚀 Comandos para Deploy

## 1️⃣ **Configurar Git (se ainda não fez):**

```bash
cd "/Users/victorprecinoti/Plataformas/Boot FINDS4living"
git init
git remote add origin https://github.com/findsforliving-lab/finds4livingbot.git
```

## 2️⃣ **Adicionar arquivos e fazer commit:**

```bash
# Adicionar todos os arquivos (exceto os que estão no .gitignore)
git add .

# Verificar o que vai ser commitado (importante!)
git status

# Fazer commit
git commit -m "Initial commit: Telegram bot for Shopify"
```

## 3️⃣ **Fazer push para GitHub:**

```bash
git branch -M main
git push -u origin main
```

## ⚠️ **IMPORTANTE:**
- ✅ O arquivo `config.env` NÃO será commitado (está no .gitignore)
- ✅ Todos os tokens ficam seguros
- ✅ Apenas código será enviado

## 4️⃣ **Depois do push, configurar Render:**

1. Acesse: https://dashboard.render.com
2. Clique em "New +" > "Background Worker"
3. Conecte ao repositório: `findsforliving-lab/finds4livingbot`
4. Configure as variáveis de ambiente (veja DEPLOY_RENDER.md)
5. Clique em "Create Background Worker"

## ✅ **Pronto!**
