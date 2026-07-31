"""
DIFAL Bot Sebem - MVP

Le todos os XMLs de NF-e da pasta /xmls, identifica quais precisam de
DIFAL e gera a planilha controle_difal.xlsx com o resumo fiscal.

Uso:
    python main.py
"""

import logging
import sys
from pathlib import Path

from src.excel_writer import gerar_planilha
from src.processor import processar_arquivos

PASTA_XMLS = Path("xmls")
ARQUIVO_SAIDA = "controle_difal.xlsx"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("difal_bot")


def main():
    if not PASTA_XMLS.exists():
        log.error("Pasta '%s' nao encontrada. Crie a pasta e coloque os XMLs de NF-e nela.", PASTA_XMLS)
        sys.exit(1)

    log.info("Lendo XMLs da pasta '%s'...", PASTA_XMLS)
    arquivos = sorted(PASTA_XMLS.glob("*.xml"))
    linhas, total_processados, total_com_difal, total_com_erro = processar_arquivos(arquivos)

    if not linhas:
        log.warning("Nenhum arquivo .xml encontrado em '%s'.", PASTA_XMLS)
        sys.exit(0)

    caminho = gerar_planilha(linhas, ARQUIVO_SAIDA)

    log.info("Planilha gerada em: %s", caminho)
    log.info("Total de XMLs processados: %d", total_processados)
    log.info("Total com DIFAL: %d", total_com_difal)
    log.info("Total com erro: %d", total_com_erro)


if __name__ == "__main__":
    main()
