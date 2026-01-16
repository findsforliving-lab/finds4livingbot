#!/usr/bin/env python3
"""
Auto-patch para Replit - Importe isso no início do bot_with_edit.py
Ou execute: python3 -c "import auto_patch_replit; import bot_with_edit"
"""

import os

# Verificar se está rodando no Replit
IS_REPLIT = 'REPLIT' in os.environ or 'REPL_SLUG' in os.environ

if IS_REPLIT:
    try:
        from patch_replit_prices_v2 import patch_extractors_for_replit_v2
        patch_extractors_for_replit_v2()
        print("✅ Auto-patch V2 aplicado para Replit")
    except Exception as e:
        print(f"⚠️ Erro ao aplicar auto-patch: {e}")
        # Tentar patch V1 como fallback
        try:
            from patch_replit_prices import patch_extractors_for_replit
            patch_extractors_for_replit()
            print("✅ Auto-patch V1 aplicado como fallback")
        except:
            print("❌ Não foi possível aplicar nenhum patch")
