"""
Geracao do PDF de referencia do DIFAL.

Este PDF NAO e uma guia oficial (nao tem codigo de barras, autenticacao
bancaria ou validade fiscal). E so um documento organizado com os
dados da nota e do DIFAL, pra usar de apoio na hora de preencher a
guia de verdade no portal oficial da UF.
"""

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

PASTA_GUIAS_PADRAO = Path("guias")


def _tabela(linhas_tabela):
    tabela = Table(linhas_tabela, colWidths=[6 * cm, 10.3 * cm])
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tabela


def gerar_pdf_referencia(linha, regra, pasta_guias=PASTA_GUIAS_PADRAO):
    """
    Gera um PDF de referencia com os dados da nota e do DIFAL.

    `linha` e o dict de uma nota processada (ver src/processor.py).
    `regra` e o dict de regras da UF (ver src/uf_rules.obter_regra_uf).

    Retorna o caminho (Path) do PDF gerado dentro de `pasta_guias`.
    """
    pasta_guias = Path(pasta_guias)
    pasta_guias.mkdir(exist_ok=True)

    valor_difal = (linha.get("valor_icms_uf_dest") or 0) + (linha.get("valor_fcp_uf_dest") or 0)

    identificador = linha.get("chave_acesso") or linha.get("numero_nf") or "sem_chave"
    caminho_pdf = pasta_guias / f"referencia_difal_{identificador}.pdf"

    estilos = getSampleStyleSheet()
    estilo_aviso = ParagraphStyle(
        "Aviso",
        parent=estilos["Normal"],
        textColor=colors.red,
        fontName="Helvetica-Bold",
        fontSize=9,
    )
    estilo_titulo = ParagraphStyle("TituloCompacto", parent=estilos["Title"], fontSize=16, spaceAfter=6)
    estilo_secao = ParagraphStyle(
        "SecaoCompacta", parent=estilos["Heading2"], fontSize=11, spaceBefore=2, spaceAfter=4
    )

    elementos = [
        Paragraph("DIFAL - Documento de Referência", estilo_titulo),
        Paragraph(
            "Este documento NÃO é uma guia oficial (sem código de barras nem validade "
            "fiscal). Use apenas como apoio para preencher a guia de verdade no portal "
            "oficial da UF.",
            estilo_aviso,
        ),
        Spacer(1, 0.3 * cm),
        Paragraph("Dados da nota", estilo_secao),
        _tabela(
            [
                ["Número NF", linha.get("numero_nf", "")],
                ["Série", linha.get("serie", "")],
                ["Chave de acesso", linha.get("chave_acesso", "")],
                ["Data de emissão", linha.get("data_emissao", "")],
                ["Cliente", linha.get("nome_destinatario", "")],
                ["CPF/CNPJ cliente", linha.get("doc_destinatario", "")],
                ["UF destino", linha.get("uf_destino", "")],
                ["Valor total da NF", f"R$ {linha.get('valor_total_nf', 0):,.2f}"],
                ["CFOPs", linha.get("cfops", "")],
                ["NCMs", linha.get("ncms", "")],
            ]
        ),
        Spacer(1, 0.3 * cm),
        Paragraph("Valores do DIFAL", estilo_secao),
        _tabela(
            [
                ["Valor ICMS UF destino", f"R$ {linha.get('valor_icms_uf_dest', 0):,.2f}"],
                ["Valor FCP UF destino", f"R$ {linha.get('valor_fcp_uf_dest', 0):,.2f}"],
                ["Valor ICMS UF remetente", f"R$ {linha.get('valor_icms_uf_remet', 0):,.2f}"],
                ["Valor total do DIFAL", f"R$ {valor_difal:,.2f}"],
            ]
        ),
        Spacer(1, 0.3 * cm),
        Paragraph("Guia sugerida", estilo_secao),
        _tabela(
            [
                ["Portal sugerido", regra.get("nome_portal", "")],
                ["URL do portal", regra.get("url", "") or "Não informado"],
                ["Tipo de guia", regra.get("tipo_guia", "")],
                ["Código de receita", regra.get("codigo_receita") or "Verificar no portal"],
                ["Observação", regra.get("observacao", "")],
            ]
        ),
        Spacer(1, 0.3 * cm),
        Paragraph("Conferência", estilo_secao),
        _tabela(
            [
                ["Beneficiário esperado", f"Secretaria da Fazenda / Governo do Estado ({linha.get('uf_destino', '')})"],
                ["UF", linha.get("uf_destino", "")],
                ["Valor", f"R$ {valor_difal:,.2f}"],
                ["Chave NF-e", linha.get("chave_acesso", "")],
            ]
        ),
        Spacer(1, 0.4 * cm),
        Paragraph(
            f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} pelo DIFAL Bot Sebem.",
            estilos["Italic"],
        ),
    ]

    documento = SimpleDocTemplate(str(caminho_pdf), pagesize=A4, title="DIFAL - Documento de Referência")
    documento.build(elementos)

    return caminho_pdf
