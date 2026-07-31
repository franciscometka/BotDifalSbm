"""
Abre um navegador de verdade, ja preenchido, na tela de emissao
individual da GNRE. Roda separado do Streamlit (via subprocess) pra
nao travar a tela enquanto o navegador fica aberto esperando o usuario
resolver o captcha e clicar em gerar.

Uso:
    python abrir_guia_gnre.py caminho_para_dados.json

O JSON deve ter as chaves: "linha" (dict da nota), "receita" e "valor".
"""

import json
import sys

from playwright.sync_api import sync_playwright

from src.gnre_web_automacao import preencher_formulario_gnre


def main():
    if len(sys.argv) < 2:
        print("Uso: python abrir_guia_gnre.py caminho_para_dados.json")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        dados = json.load(f)

    linha = dados["linha"]
    receita = dados["receita"]
    valor = dados["valor"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        resultado = preencher_formulario_gnre(page, linha, receita, valor)
        for aviso in resultado["avisos"]:
            print("-", aviso)

        # Mantem o navegador aberto ate o usuario fechar a aba/janela.
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
        browser.close()


if __name__ == "__main__":
    main()
