# 🤖 Bot de Importação de Produtos - Shopify + Telegram

Este bot automatiza o processo de importação de produtos de qualquer site para o Shopify e postagem automática em canais do Telegram.

## 🚀 Funcionalidades

- ✅ Extração automática de dados do produto via URL
- ✅ Identificação inteligente com GPT (opcional)
- ✅ Coleta de título, imagens (3-4), descrição e preços
- ✅ Cálculo automático de porcentagem de desconto
- ✅ Criação automática de produtos no Shopify
- ✅ Adição de metafields para links de afiliado
- ✅ Postagem automática no canal do Telegram
- ✅ Interface amigável via bot do Telegram

## 📋 Pré-requisitos

### 1. Bot do Telegram
1. Fale com [@BotFather](https://t.me/botfather) no Telegram
2. Crie um novo bot com `/newbot`
3. Anote o token do bot

### 2. Canal do Telegram
1. Crie um canal no Telegram
2. Adicione o bot como administrador
3. Anote o ID do canal (ex: @meucanal)

### 3. Shopify
1. Acesse seu painel admin do Shopify
2. Vá em Apps > Develop apps > Create an app
3. Configure as permissões necessárias:
   - `write_products`
   - `write_product_listings`
   - `write_metafields`
4. Anote a URL da loja e o Access Token

### 4. OpenAI (Opcional)
1. Crie uma conta na OpenAI
2. Gere uma API Key
3. Adicione créditos à conta

## 🛠️ Instalação

### 1. Clone o projeto
```bash
git clone <seu-repositorio>
cd "Boot FINDS4living"
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente
Copie o arquivo `config.env.example` para `config.env` e preencha:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=seu_token_do_bot_aqui
TELEGRAM_CHANNEL_ID=@seu_canal_ou_id

# Shopify Configuration
SHOPIFY_SHOP_URL=sua-loja.myshopify.com
SHOPIFY_ACCESS_TOKEN=seu_token_shopify

# OpenAI Configuration (opcional)
OPENAI_API_KEY=sua_chave_openai

# Metafield Configuration
AFFILIATE_LINK_METAFIELD_NAMESPACE=custom
AFFILIATE_LINK_METAFIELD_KEY=affiliate_link
```

### 4. Execute o bot (localmente)
```bash
python3 bot_with_edit.py
```

## 🌐 Deploy no Render.com

Para rodar o bot 24/7 de graça, veja o guia completo: [DEPLOY_RENDER.md](DEPLOY_RENDER.md)

### Resumo rápido:
1. Faça push para GitHub (repositório privado recomendado)
2. Crie conta no [Render.com](https://render.com)
3. Crie um "Background Worker" conectado ao seu repositório
4. Configure as variáveis de ambiente no Render
5. Deploy automático!

## 📱 Como Usar

### 1. Inicie o bot
- Envie `/start` para o bot no Telegram
- O bot mostrará as instruções

### 2. Importe um produto
- Envie o link do produto que deseja importar
- O bot extrairá automaticamente:
  - Título do produto
  - 3-4 imagens principais
  - Preços (atual e original)
  - Descrição
  - Porcentagem de desconto

### 3. Revise e publique
- O bot mostrará um preview do produto
- Você pode revisar as informações
- Clique em "Publicar no Shopify"
- O bot criará o produto no Shopify
- Postará automaticamente no canal do Telegram

## 🎯 Formato da Postagem no Canal

```
🔥 Nome do Produto

💥 25% OFF
~~R$ 69,90~~
💰 R$ 39,90

🛒 Link da Amazon (afiliado): https://...
```

## 🔧 Configurações Avançadas

### Metafields do Shopify
O bot cria automaticamente um metafield para armazenar o link de afiliado:
- **Namespace:** `custom` (configurável)
- **Key:** `affiliate_link` (configurável)
- **Type:** `single_line_text_field`

### Extração de Produtos
O bot suporta extração de produtos de diversos sites:
- Amazon
- Mercado Livre  
- AliExpress
- E-commerces em geral
- Sites com estrutura HTML padrão

### IA para Melhorar Extração (Opcional)
Se configurado com OpenAI, o bot:
- Melhora títulos para serem mais atrativos
- Sugere categorias apropriadas
- Otimiza descrições para conversão

## 🐛 Solução de Problemas

### Bot não responde
- Verifique se o token está correto
- Confirme que o bot está ativo no BotFather

### Erro no Shopify
- Verifique as permissões da API
- Confirme se o Access Token está válido
- Teste a conexão com a loja

### Não posta no canal
- Verifique se o bot é admin do canal
- Confirme o ID do canal (com @)
- Teste enviando mensagem manual

### Erro na extração
- Alguns sites podem bloquear bots
- Tente com diferentes URLs
- Verifique se o site está acessível

## 📈 Próximas Funcionalidades

- [ ] Edição de produtos antes da publicação
- [ ] Suporte a múltiplas lojas Shopify
- [ ] Agendamento de postagens
- [ ] Relatórios de performance
- [ ] Interface web para configuração
- [ ] Suporte a mais idiomas

## 🤝 Suporte

Para dúvidas ou problemas:
1. Verifique este README
2. Consulte os logs do bot
3. Teste com diferentes produtos
4. Entre em contato com o desenvolvedor

## 📄 Licença

Este projeto é de uso privado. Todos os direitos reservados.
