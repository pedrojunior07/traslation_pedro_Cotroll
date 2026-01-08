#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste de auto-correção de JSON com aspas triplas escapadas erradas
"""
import json
import re

# JSON problemático (do erro real)
json_with_error = r'''{
  "translations": [
    {
      "location": "T1321",
      "translation": "(\"""FCPA\"""), a Lei de Suborno do Reino Unido de 2010"
    }
  ]
}'''

print("="*80)
print("TESTE DE AUTO-CORREÇÃO DE JSON")
print("="*80)

print("\n1. JSON ORIGINAL (COM ERRO):")
print(json_with_error)

print("\n2. TENTANDO PARSE DIRETO (DEVE FALHAR):")
try:
    result = json.loads(json_with_error)
    print("   ✅ Sucesso (inesperado!)")
except json.JSONDecodeError as e:
    print(f"   ❌ Erro esperado: {e}")

print("\n3. APLICANDO AUTO-CORREÇÃO:")
fixed = json_with_error
corrections_made = []

# 1. Corrigir aspas triplas escapadas erradas: \""" → \"
if r'\"""' in fixed:
    fixed = fixed.replace(r'\"""', r'\"')
    corrections_made.append("aspas triplas → aspas simples")
    print(f"   ✓ Correção aplicada: aspas triplas → aspas simples")

print("\n4. JSON CORRIGIDO:")
print(fixed)

print("\n5. TENTANDO PARSE APÓS CORREÇÃO:")
try:
    result = json.loads(fixed)
    print(f"   ✅ Sucesso! Correções aplicadas: {', '.join(corrections_made)}")
    print(f"\n6. RESULTADO PARSEADO:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
except json.JSONDecodeError as e:
    print(f"   ❌ Ainda com erro: {e}")

print("\n" + "="*80)
print("FIM DO TESTE")
print("="*80)
