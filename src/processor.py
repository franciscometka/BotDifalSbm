"""
Processamento compartilhado entre a CLI (main.py) e a tela Streamlit (app.py).

Recebe uma lista de arquivos XML (caminhos ou arquivos em memória, ambos
com atributo `.name` e aceitos por `xml.etree.ElementTree.parse`) e
devolve as linhas prontas para a planilha, junto dos totais.
"""

import logging

from src.xml_reader import ler_nfe
from src.difal_detector import precisa_difal
from src.uf_rules import obter_regra_uf

log = logging.getLogger("difal_bot")


def processar_arquivos(arquivos):
    """
    Processa uma lista de arquivos XML de NF-e.

    Retorna (linhas, total_processados, total_com_difal, total_com_erro).
    """
    linhas = []
    total_processados = 0
    total_com_difal = 0
    total_com_erro = 0

    for arquivo in arquivos:
        nome_arquivo = getattr(arquivo, "name", str(arquivo))
        try:
            dados = ler_nfe(arquivo)
            tem_difal = precisa_difal(dados)
            regra_uf = obter_regra_uf(dados["uf_destino"]) if tem_difal else None

            linhas.append({
                "status": "OK",
                "numero_nf": dados["numero_nf"],
                "serie": dados["serie"],
                "chave_acesso": dados["chave_acesso"],
                "data_emissao": dados["data_emissao"],
                "nome_destinatario": dados["nome_destinatario"],
                "doc_destinatario": dados["doc_destinatario"],
                "uf_destino": dados["uf_destino"],
                "municipio_destinatario": dados["municipio_destinatario"],
                "valor_total_nf": dados["valor_total_nf"],
                "valor_icms_uf_dest": dados["valor_icms_uf_dest"],
                "valor_fcp_uf_dest": dados["valor_fcp_uf_dest"],
                "valor_icms_uf_remet": dados["valor_icms_uf_remet"],
                "base_calculo_icms_uf_dest": dados["base_calculo_icms_uf_dest"],
                "aliquota_icms_uf_dest": dados["aliquota_icms_uf_dest"],
                "cfops": ", ".join(sorted(set(dados["cfops"]))),
                "ncms": ", ".join(sorted(set(dados["ncms"]))),
                "precisa_difal": "Sim" if tem_difal else "Não",
                "portal_sugerido": regra_uf["nome_portal"] if regra_uf else "",
                "tipo_guia": regra_uf["tipo_guia"] if regra_uf else "",
                "pdf_guia": "",
                "status_guia": "Pendente" if tem_difal else "Não se aplica",
                "observacoes": "",
            })

            total_processados += 1
            if tem_difal:
                total_com_difal += 1

        except Exception as erro:
            log.warning("Erro ao processar %s: %s", nome_arquivo, erro)
            linhas.append({
                "status": "Erro",
                "numero_nf": "",
                "serie": "",
                "chave_acesso": "",
                "data_emissao": "",
                "nome_destinatario": "",
                "doc_destinatario": "",
                "uf_destino": "",
                "valor_total_nf": "",
                "valor_icms_uf_dest": "",
                "valor_fcp_uf_dest": "",
                "valor_icms_uf_remet": "",
                "base_calculo_icms_uf_dest": "",
                "aliquota_icms_uf_dest": "",
                "cfops": "",
                "ncms": "",
                "precisa_difal": "",
                "portal_sugerido": "",
                "tipo_guia": "",
                "pdf_guia": "",
                "status_guia": "",
                "observacoes": f"Arquivo: {nome_arquivo} | Erro: {erro}",
            })
            total_com_erro += 1

    return linhas, total_processados, total_com_difal, total_com_erro
