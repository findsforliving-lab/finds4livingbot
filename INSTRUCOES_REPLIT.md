# 🔧 Instruções para Corrigir Preços no Replit

## ⚠️ ATUALIZAÇÃO: Use o Patch V2 (filtra preços incorretos)

## Opção 1: Aplicar Patch V2 Automaticamente (RECOMENDADO)

No terminal do Replit, execute ANTES de iniciar o bot:

```bash
python3 patch_replit_prices_v2.py
python3 bot_with_edit.py
```

## Testar se está funcionando:

```bash
python3 test_price_extraction.py https://www.amazon.com/dp/B08N5WRWNW
```

Isso vai mostrar se o preço está sendo extraído corretamente.

## Opção 2: Adicionar Patch Direto no Código (Apenas no Replit)

Adicione estas linhas no **INÍCIO** do arquivo `bot_with_edit.py` no Replit (depois dos imports, antes de tudo):

```python
# PATCH PARA REPLIT - Adicionar no início do arquivo
import os
if 'REPLIT' in os.environ or 'REPL_SLUG' in os.environ:
    try:
        from patch_replit_prices import patch_extractors_for_replit
        patch_extractors_for_replit()
        print("✅ Patch de preços aplicado para Replit")
    except Exception as e:
        print(f"⚠️ Erro ao aplicar patch: {e}")
```

## Opção 3: Modificar Apenas a Função no Replit

Se as opções acima não funcionarem, você pode modificar **apenas no Replit** a função `_extract_amazon_prices` no arquivo `extractors.py`:

1. Abra `extractors.py` no Replit
2. Encontre a função `_extract_amazon_prices` (linha ~91)
3. Adicione mais seletores de busca de preços

**NÃO FAÇA COMMIT DESSAS MUDANÇAS** - são apenas para o Replit!

## ✅ Verificação

Após aplicar o patch, teste com um produto Amazon. Se ainda não pegar preço, execute:

```bash
python3 test_headers_replit.py
```

E me envie o resultado para ajustarmos mais.
