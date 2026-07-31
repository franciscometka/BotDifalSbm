"""
DIFAL Bot Sebem - tela Streamlit

Upload de XMLs de NF-e, processamento, controle de DIFAL na tela e
apoio para gerar a guia de recolhimento por nota (PDF quando houver
automacao pronta para a UF, ou conferencia + link do portal oficial
quando ainda for manual).

Layout baseado no handoff de design "DIFAL Bot Sebem" (sidebar de
ingestao + resumo do lote + abas "Notas processadas"/"DIFAL por UF").

O sistema nunca paga a guia sozinho: no maximo gera/baixa o PDF.

Uso:
    streamlit run app.py
"""

import getpass
import html
import io
import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import certificado_configurado, descrever_status
from src.excel_writer import gerar_planilha
from src.gnre_client import GnreClient
from src.gnre_web_automacao import RECEITA_DIFAL_OPERACAO, RECEITA_FCP_OPERACAO
from src.guia_generator import gerar_guia
from src.pdf_guia import gerar_pdf_referencia
from src.processor import processar_arquivos
from src.uf_rules import obter_regra_uf

ARQUIVO_SAIDA = "controle_difal.xlsx"
PASTA_GUIAS = Path("guias")
PASTA_GUIAS.mkdir(exist_ok=True)

CSS_CUSTOMIZADO = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: "IBM Plex Sans", Helvetica, Arial, sans-serif; }
.stApp { background: #f4f4f2; }
section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e2e2dd; }

/* ---- Marca (logo + titulo) ---- */
.marca-row { display: flex; align-items: center; gap: 10px; margin-bottom: 2px; }
.marca-quadrado {
    width: 30px; height: 30px; border-radius: 7px; background: #14548c;
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-size: 12px; font-weight: 700; letter-spacing: -0.02em; flex-shrink: 0;
}
.marca-titulo { font-size: 14px; font-weight: 600; letter-spacing: -0.01em; line-height: 1.1; color: #23241f; }
.marca-subtitulo { font-size: 11px; color: #82837b; line-height: 1.3; margin-top: 1px; }

.rotulo-secao {
    font-size: 11px; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase;
    color: #82837b; margin: 4px 0 2px 0;
}
.nota-rodape { font-size: 10.5px; color: #92938a; line-height: 1.4; margin-top: 4px; }

/* ---- Ultimo lote (sidebar) ---- */
.ultimo-lote { border-top: 1px solid #e9e9e3; padding-top: 14px; margin-top: 10px; }
.ultimo-lote-linha { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px; }
.ultimo-lote-linha .rotulo { color: #6f7068; }
.ultimo-lote-linha .valor { font-family: "IBM Plex Mono", monospace; color: #23241f; }
.ultimo-lote-id { font-size: 11px; color: #92938a; line-height: 1.4; margin-top: 4px; }

/* ---- Cabecalho principal ---- */
.cabecalho-titulo { font-size: 21px; font-weight: 600; letter-spacing: -0.015em; color: #23241f; margin: 0; }
.cabecalho-subtitulo { font-size: 12.5px; color: #82837b; margin-top: 3px; }

/* ---- Cards de indicador ---- */
.difal-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 4px 0 6px 0; }
@media (max-width: 1000px) { .difal-cards { grid-template-columns: repeat(2, 1fr); } }
.difal-card { background: #fff; border: 1px solid #e2e2dd; border-radius: 8px; padding: 14px 16px 15px; display: flex; flex-direction: column; gap: 8px; }
.difal-card .difal-card-label { font-size: 11px; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase; color: #82837b; }
.difal-card .difal-card-value { font-family: "IBM Plex Mono", monospace; font-size: 27px; font-weight: 500; letter-spacing: -0.02em; color: #23241f; line-height: 1; }
.difal-card .difal-card-legenda { font-size: 11.5px; color: #92938a; }
.difal-card.warn { background: #fffaf5; border: 1px solid #e8c9a4; }
.difal-card.warn .difal-card-label { color: #9a6321; }
.difal-card.warn .difal-card-value { color: #8a4f13; }
.difal-card.warn .difal-card-legenda { color: #a1743f; }

/* ---- Badge de status ---- */
.badge { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: 600; padding: 3px 8px 3px 7px; border-radius: 4px; white-space: nowrap; }
.badge .dot { width: 5px; height: 5px; border-radius: 50%; }
.badge.ok { background: #f1f8f3; color: #256b41; border: 1px solid #c9e3d3; }
.badge.ok .dot { background: #2f8b52; }
.badge.erro { background: #fdf2f2; color: #a02222; border: 1px solid #f0cccc; }
.badge.erro .dot { background: #c23434; }

/* ---- Tabela "Notas processadas" ---- */
.tabela-wrap { background: #fff; border: 1px solid #e2e2dd; border-radius: 8px; overflow-x: auto; margin-bottom: 4px; }
.tabela-notas { width: 100%; border-collapse: collapse; min-width: 640px; }
.tabela-notas thead th {
    text-align: left; font-size: 10.5px; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase;
    color: #82837b; background: #fafaf8; padding: 10px 16px; border-bottom: 1px solid #e9e9e3;
}
.tabela-notas td { padding: 12px 16px; border-bottom: 1px solid #f0f0ea; font-size: 13px; color: #23241f; }
.tabela-notas tbody tr:hover { background: #fbfbf9; }
.tabela-notas td.mono { font-family: "IBM Plex Mono", monospace; font-size: 12.5px; }
.tabela-notas td.right { text-align: right; font-variant-numeric: tabular-nums; }
.tabela-rodape { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 11px 16px; background: #fafaf8; font-size: 11.5px; color: #82837b; }

/* ---- Tabela "DIFAL por UF" ---- */
.tabela-uf thead th {
    text-align: left; font-size: 10.5px; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase;
    color: #82837b; background: #fafaf8; padding: 10px 16px; border-bottom: 1px solid #e9e9e3;
}
.tabela-uf td { padding: 12px 16px; border-bottom: 1px solid #f0f0ea; font-size: 12.5px; color: #23241f; font-family: "IBM Plex Mono", monospace; }
.tabela-uf tr.total td { background: #fafaf8; font-family: "IBM Plex Sans"; font-size: 12.5px; }
.barra-trilha { flex: 1 1 auto; height: 6px; background: #f0f0ea; border-radius: 3px; overflow: hidden; }
.barra-preenchimento { height: 6px; background: #14548c; border-radius: 3px; }
.barra-linha { display: flex; align-items: center; gap: 10px; }
.barra-pct { font-family: "IBM Plex Mono", monospace; font-size: 11.5px; color: #82837b; flex: 0 0 42px; text-align: right; }

/* ---- Painel de detalhe fiscal (dentro do expander) ---- */
.det-chave-label { font-size: 10.5px; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase; color: #82837b; margin-bottom: 4px; }
.det-chave-valor { font-family: "IBM Plex Mono", monospace; font-size: 12px; color: #23241f; letter-spacing: 0.02em; margin-bottom: 14px; word-break: break-all; }
.det-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px 20px; margin-bottom: 10px; }
@media (max-width: 900px) { .det-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.det-item { display: flex; flex-direction: column; gap: 3px; }
.det-label { font-size: 10.5px; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase; color: #82837b; }
.det-valor { font-family: "IBM Plex Mono", monospace; font-size: 12.5px; color: #23241f; }
.det-obs { font-size: 11.5px; color: #82837b; line-height: 1.5; }

/* ---- Dropzone de upload ---- */
[data-testid="stFileUploaderDropzone"] {
    border: 1px dashed #cfcfc7 !important;
    background: #fafaf8 !important;
    border-radius: 8px !important;
}
</style>
"""


def fmt_num_ptbr(valor, vazio="-", casas=2):
    """Formata numero no padrao pt-BR (milhar com ponto, decimal com virgula)."""
    if valor in (None, ""):
        return vazio
    try:
        valor_float = float(valor)
    except (TypeError, ValueError):
        return vazio
    texto = f"{valor_float:,.{casas}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def valor_difal(linha):
    """Soma ICMS UF destino + FCP UF destino, tratando valores vazios como 0."""
    icms = linha.get("valor_icms_uf_dest") or 0
    fcp = linha.get("valor_fcp_uf_dest") or 0
    return float(icms) + float(fcp)


def _texto(valor):
    """Escapa texto pra uso seguro dentro de HTML customizado."""
    if valor in (None, ""):
        return ""
    return html.escape(str(valor))


def badge_status_html(status):
    """Badge colorido de status (OK/Erro), igual ao handoff de design."""
    if status == "OK":
        return '<span class="badge ok"><span class="dot"></span>OK</span>'
    if status == "Erro":
        return '<span class="badge erro"><span class="dot"></span>Erro</span>'
    return _texto(status)


def cor_difal(linha):
    """Cor do valor de DIFAL: cinza se erro/zero, âmbar quando há valor a recolher."""
    if linha.get("status") != "OK":
        return "#92938a"
    if valor_difal(linha) <= 0:
        return "#92938a"
    return "#8a4f13"


def montar_tabela_notas_html(linhas):
    """Monta a tabela HTML de notas processadas (Status, Número NF, Cliente, UF, Valor da NF, DIFAL)."""
    linhas_html = []
    for linha in linhas:
        cor = cor_difal(linha)
        difal_txt = fmt_num_ptbr(valor_difal(linha)) if linha.get("status") == "OK" else "-"
        linhas_html.append(
            "<tr>"
            f"<td>{badge_status_html(linha.get('status', ''))}</td>"
            f"<td class='mono'>{_texto(linha.get('numero_nf')) or '-'}</td>"
            f"<td>{_texto(linha.get('nome_destinatario')) or '-'}</td>"
            f"<td class='mono'>{_texto(linha.get('uf_destino')) or '-'}</td>"
            f"<td class='mono right'>{fmt_num_ptbr(linha.get('valor_total_nf'))}</td>"
            f"<td class='mono right' style='color:{cor}'>{difal_txt}</td>"
            "</tr>"
        )
    return (
        '<div class="tabela-wrap"><table class="tabela-notas">'
        "<thead><tr><th>Status</th><th>Número NF</th><th>Cliente</th><th>UF</th>"
        "<th style='text-align:right'>Valor da NF</th><th style='text-align:right'>DIFAL</th></tr></thead>"
        f"<tbody>{''.join(linhas_html)}</tbody>"
        "</table></div>"
    )


def montar_tabela_uf_html(linhas):
    """Monta a tabela HTML 'DIFAL por UF' (participação, base total, DIFAL), com linha de total."""
    notas_difal = [linha for linha in linhas if linha.get("precisa_difal") == "Sim"]
    if not notas_difal:
        return None

    agregados = {}
    for linha in notas_difal:
        uf = linha.get("uf_destino") or "-"
        agregados.setdefault(uf, {"notas": 0, "base": 0.0, "difal": 0.0})
        agregados[uf]["notas"] += 1
        agregados[uf]["base"] += float(linha.get("valor_total_nf") or 0)
        agregados[uf]["difal"] += valor_difal(linha)

    difal_total = sum(v["difal"] for v in agregados.values())
    base_total = sum(v["base"] for v in agregados.values())
    total_notas = sum(v["notas"] for v in agregados.values())

    linhas_ordenadas = sorted(agregados.items(), key=lambda item: item[1]["difal"], reverse=True)

    linhas_html = []
    for uf, dados in linhas_ordenadas:
        pct = (dados["difal"] / difal_total * 100) if difal_total > 0 else 0
        linhas_html.append(
            "<tr>"
            f"<td>{_texto(uf)}</td>"
            f"<td>{dados['notas']}</td>"
            "<td><div class='barra-linha'>"
            f"<div class='barra-trilha'><div class='barra-preenchimento' style='width:{pct:.0f}%'></div></div>"
            f"<span class='barra-pct'>{pct:.0f}%</span>"
            "</div></td>"
            f"<td style='text-align:right'>{fmt_num_ptbr(dados['base'])}</td>"
            f"<td style='text-align:right'>{fmt_num_ptbr(dados['difal'])}</td>"
            "</tr>"
        )

    linha_total = (
        "<tr class='total'>"
        "<td style='font-weight:600'>Total</td>"
        f"<td>{total_notas}</td><td></td>"
        f"<td style='text-align:right'>{fmt_num_ptbr(base_total)}</td>"
        f"<td style='text-align:right;font-weight:500'>{fmt_num_ptbr(difal_total)}</td>"
        "</tr>"
    )

    return (
        '<div class="tabela-wrap"><table class="tabela-uf" style="width:100%;border-collapse:collapse">'
        "<thead><tr><th>UF</th><th>Notas</th><th>Participação no lote</th>"
        "<th style='text-align:right'>Base total</th><th style='text-align:right'>DIFAL</th></tr></thead>"
        f"<tbody>{''.join(linhas_html)}{linha_total}</tbody>"
        "</table></div>"
    )


def grid_detalhe_html(linha):
    """HTML do painel de detalhe fiscal: chave de acesso + grid de 8 campos."""
    aliquota = linha.get("aliquota_icms_uf_dest")
    aliquota_fmt = f"{fmt_num_ptbr(aliquota)}%" if aliquota not in (None, "") else "-"
    difal_fmt = fmt_num_ptbr(valor_difal(linha)) if linha.get("status") == "OK" else "-"
    cor = cor_difal(linha)

    def item(label, valor, cor_valor=None):
        estilo = f" style='color:{cor_valor}'" if cor_valor else ""
        return (
            "<div class='det-item'>"
            f"<div class='det-label'>{label}</div>"
            f"<div class='det-valor'{estilo}>{valor}</div>"
            "</div>"
        )

    itens = "".join([
        item("CFOPs", _texto(linha.get("cfops")) or "-"),
        item("NCMs", _texto(linha.get("ncms")) or "-"),
        item("Base de cálculo ICMS UF destino", fmt_num_ptbr(linha.get("base_calculo_icms_uf_dest"))),
        item("Alíquota ICMS UF destino", aliquota_fmt),
        item("ICMS origem (remetente)", fmt_num_ptbr(linha.get("valor_icms_uf_remet"))),
        item("ICMS destino", fmt_num_ptbr(linha.get("valor_icms_uf_dest"))),
        item("FCP destino", fmt_num_ptbr(linha.get("valor_fcp_uf_dest"))),
        item("DIFAL a recolher", difal_fmt, cor),
    ])

    return (
        f"<div class='det-chave-label'>Chave de acesso</div>"
        f"<div class='det-chave-valor'>{_texto(linha.get('chave_acesso')) or 'não identificada'}</div>"
        f"<div class='det-grid'>{itens}</div>"
    )


def abrir_gnre_preenchida(linha, receita, valor):
    """
    Escreve os dados da nota num arquivo temporário e abre, em um
    processo separado, um navegador de verdade já preenchido no
    formulário público da GNRE (não trava a tela do Streamlit
    enquanto o navegador fica aberto esperando o captcha).
    """
    dados = {"linha": linha, "receita": receita, "valor": valor}
    arquivo_tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(dados, arquivo_tmp, ensure_ascii=False)
    arquivo_tmp.close()

    flags = 0
    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP") and hasattr(subprocess, "DETACHED_PROCESS"):
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    subprocess.Popen(
        [sys.executable, "abrir_guia_gnre.py", arquivo_tmp.name],
        creationflags=flags,
    )


def secao_acoes_guia(linha, indice, regra):
    """Botão 'Gerar guia' + fluxo (PDF de referência / automação GNRE) dentro do detalhe da nota."""
    uf = linha["uf_destino"]
    valor = valor_difal(linha)

    st.markdown(f"**Beneficiário esperado:** Secretaria da Fazenda / Governo do Estado ({uf}) "
                f"· **Código de receita:** {regra['codigo_receita'] or 'verificar no portal'} "
                f"· **Tipo de guia:** {regra['tipo_guia']}")

    status_atual = linha.get("status_guia", "Pendente")
    if status_atual not in ("Pendente", ""):
        st.info(f"Status atual: {status_atual}")

    if st.button("Gerar guia", key=f"gerar_guia_{indice}"):
        resultado = gerar_guia(uf, linha)

        if resultado["status"] == "gerado":
            st.success(resultado["mensagem"])
            linha["pdf_guia"] = resultado["caminho_pdf"]
            linha["status_guia"] = "Gerada"

        elif resultado["status"] == "manual":
            caminho_pdf = gerar_pdf_referencia(linha, regra)
            linha["pdf_guia"] = str(caminho_pdf)
            linha["status_guia"] = "PDF de referência gerado - preencher no portal"

            st.warning(resultado["mensagem"])
            st.success(f"PDF de referência gerado: {caminho_pdf}")

            with open(caminho_pdf, "rb") as arquivo_pdf:
                st.download_button(
                    "Baixar guia GNRE desta nota (PDF de referência)",
                    data=arquivo_pdf.read(),
                    file_name=caminho_pdf.name,
                    mime="application/pdf",
                    key=f"baixar_pdf_{indice}",
                )

            if regra["url"]:
                st.link_button(f"Abrir portal ({regra['nome_portal']})", regra["url"])

            st.caption(
                "O PDF é só um documento de referência (sem código de barras nem "
                "validade fiscal) — a guia de verdade é emitida no portal oficial."
            )

            if regra["tipo_guia"] == "GNRE":
                st.divider()
                st.markdown("**Preencher automaticamente no site da GNRE**")
                st.caption(
                    "Abre um navegador de verdade já preenchido com os dados da nota. "
                    "Você só precisa resolver o captcha e clicar no botão final de gerar "
                    "a guia — o sistema não faz isso sozinho."
                )
                if st.button("Preencher guia da GNRE (DIFAL)", key=f"preencher_gnre_{indice}"):
                    abrir_gnre_preenchida(linha, RECEITA_DIFAL_OPERACAO, linha["valor_icms_uf_dest"])
                    st.success("Abrindo o navegador com os dados preenchidos...")

                valor_fcp = linha.get("valor_fcp_uf_dest") or 0
                if valor_fcp > 0:
                    st.caption(
                        "Essa UF também cobra FCP — é uma guia separada, com código de "
                        "receita próprio (não é só somar ao valor do ICMS)."
                    )
                    if st.button("Preencher guia da GNRE (FCP)", key=f"preencher_gnre_fcp_{indice}"):
                        abrir_gnre_preenchida(linha, RECEITA_FCP_OPERACAO, valor_fcp)
                        st.success("Abrindo o navegador com os dados preenchidos (FCP)...")

        else:
            st.error(resultado["mensagem"])
            linha["status_guia"] = "Erro"


def linha_expander(linha, indice):
    """Expander com o detalhe fiscal completo de uma nota (+ ações de guia, quando com DIFAL)."""
    if linha.get("status") == "Erro":
        titulo = f"Erro · {linha.get('observacoes') or 'arquivo não pôde ser lido'}"
    else:
        titulo = f"{linha.get('numero_nf') or '-'} · {linha.get('nome_destinatario') or 'sem cliente'}"

    with st.expander(titulo):
        st.markdown(grid_detalhe_html(linha), unsafe_allow_html=True)

        if linha.get("status") == "Erro":
            st.markdown(f"<div class='det-obs'>{_texto(linha.get('observacoes'))}</div>", unsafe_allow_html=True)
            return

        if linha.get("precisa_difal") == "Sim":
            regra = st.session_state.regras_por_indice[indice]
            secao_acoes_guia(linha, indice, regra)
        else:
            st.markdown(
                "<div class='det-obs'>Destinatário contribuinte ou operação sem DIFAL — "
                "nenhuma guia é necessária para esta nota.</div>",
                unsafe_allow_html=True,
            )


st.set_page_config(page_title="DIFAL Bot Sebem", page_icon="📊", layout="wide")
st.markdown(CSS_CUSTOMIZADO, unsafe_allow_html=True)

if "linhas" not in st.session_state:
    st.session_state.linhas = None
    st.session_state.totais = None
    st.session_state.regras_por_indice = None
    st.session_state.lote_info = None
    st.session_state.lote_contador = 0

# ---------------------------------------------------------------- Sidebar
with st.sidebar:
    st.markdown(
        """
        <div class="marca-row">
          <div class="marca-quadrado">DB</div>
          <div>
            <div class="marca-titulo">DIFAL Bot Sebem</div>
            <div class="marca-subtitulo">Controle fiscal interno</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="rotulo-secao">Entrada de arquivos</div>', unsafe_allow_html=True)
    arquivos_upload = st.file_uploader(
        "Arraste os XMLs de NF-e aqui ou clique para selecionar",
        type=["xml"],
        accept_multiple_files=True,
        label_visibility="visible",
    )

    processar_clicado = st.button(
        "Processar XMLs",
        type="primary",
        use_container_width=True,
        disabled=not arquivos_upload,
    )
    st.markdown(
        '<div class="nota-rodape">Somente NF-e de saída interestadual são avaliadas.</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.lote_info:
        info = st.session_state.lote_info
        st.markdown(
            f"""
            <div class="ultimo-lote">
              <div class="rotulo-secao" style="margin-top:0">Último lote</div>
              <div class="ultimo-lote-linha"><span class="rotulo">Arquivos</span><span class="valor">{info['arquivos']}</span></div>
              <div class="ultimo-lote-linha"><span class="rotulo">Processado às</span><span class="valor">{info['horario']}</span></div>
              <div class="ultimo-lote-linha"><span class="rotulo">Data</span><span class="valor">{info['data']}</span></div>
              <div class="ultimo-lote-id">Lote #{info['lote_id']} · usuário {info['usuario']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------- Processamento
if processar_clicado and arquivos_upload:
    with st.spinner("Processando XMLs..."):
        linhas, total_processados, total_com_difal, total_com_erro = processar_arquivos(arquivos_upload)
    st.session_state.linhas = linhas
    st.session_state.totais = (total_processados, total_com_difal, total_com_erro)
    st.session_state.regras_por_indice = {
        i: obter_regra_uf(linha["uf_destino"]) for i, linha in enumerate(linhas)
    }

    agora = datetime.now()
    st.session_state.lote_contador += 1
    st.session_state.lote_info = {
        "arquivos": len(arquivos_upload),
        "horario": agora.strftime("%H:%M"),
        "data": agora.strftime("%d/%m/%Y"),
        "lote_id": f"{agora:%Y-%m%d}-{st.session_state.lote_contador:02d}",
        "usuario": getpass.getuser(),
        "competencia": agora.strftime("%m/%Y"),
    }

# ---------------------------------------------------------------- Main
if st.session_state.linhas is not None:
    linhas = st.session_state.linhas
    total_processados, total_com_difal, total_com_erro = st.session_state.totais
    info = st.session_state.lote_info

    valor_difal_total = sum(valor_difal(linha) for linha in linhas if linha.get("precisa_difal") == "Sim")

    buffer = io.BytesIO()
    gerar_planilha(linhas, buffer)
    buffer.seek(0)

    col_titulo, col_botao = st.columns([4, 1.4])
    with col_titulo:
        st.markdown(
            f"""
            <h1 class="cabecalho-titulo">Resumo do lote</h1>
            <div class="cabecalho-subtitulo">
              {info['arquivos']} XMLs recebidos · apuração de DIFAL por UF de destino ·
              competência {info['competencia']}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_botao:
        st.write("")
        st.download_button(
            label="⬇ Baixar Excel do lote",
            data=buffer,
            file_name=ARQUIVO_SAIDA,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    classe_com_difal = "difal-card warn" if total_com_difal > 0 else "difal-card"
    st.markdown(
        f"""
        <div class="difal-cards">
          <div class="difal-card">
            <div class="difal-card-label">Processados</div>
            <div class="difal-card-value">{total_processados}</div>
            <div class="difal-card-legenda">de {info['arquivos']} arquivos enviados</div>
          </div>
          <div class="{classe_com_difal}">
            <div class="difal-card-label">Com DIFAL</div>
            <div class="difal-card-value">{total_com_difal}</div>
            <div class="difal-card-legenda">notas exigem recolhimento</div>
          </div>
          <div class="difal-card">
            <div class="difal-card-label">Com erro</div>
            <div class="difal-card-value">{total_com_erro}</div>
            <div class="difal-card-legenda">XML inválido ou incompleto</div>
          </div>
          <div class="difal-card">
            <div class="difal-card-label">Valor total de DIFAL</div>
            <div class="difal-card-value">{fmt_num_ptbr(valor_difal_total)}</div>
            <div class="difal-card-legenda">em reais, somando {total_com_difal} nota(s)</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    aba_notas, aba_uf = st.tabs(["Notas processadas", "DIFAL por UF"])

    with aba_notas:
        st.caption("Ordenado por número da NF · clique em uma nota abaixo para ver os detalhes fiscais.")
        st.markdown(montar_tabela_notas_html(linhas), unsafe_allow_html=True)
        st.markdown(
            f"<div class='tabela-rodape'><span>Exibindo {len(linhas)} de {len(linhas)} notas</span>"
            "<span>Clique em uma nota abaixo para ver os detalhes fiscais</span></div>",
            unsafe_allow_html=True,
        )
        for indice, linha in enumerate(linhas):
            linha_expander(linha, indice)

    with aba_uf:
        st.caption("Agrupado por UF de destino.")
        tabela_uf_html = montar_tabela_uf_html(linhas)
        if tabela_uf_html:
            st.markdown(tabela_uf_html, unsafe_allow_html=True)
        else:
            st.info("Nenhuma nota com DIFAL encontrada nesse lote.")
else:
    st.markdown('<h1 class="cabecalho-titulo">Resumo do lote</h1>', unsafe_allow_html=True)
    st.info("Envie os XMLs na barra lateral e clique em 'Processar XMLs' para começar.")

with st.expander("Diagnóstico da integração GNRE (não mostra a senha)"):
    st.write(descrever_status())
    st.caption(
        "Configure GNRE_CERT_PATH e GNRE_CERT_PASSWORD no arquivo .env (veja .env.example). "
        "A automação de envio de guia ainda não está implementada - isso aqui só testa a "
        "conexão e consulta as regras de uma UF (tudo somente leitura, não envia nada)."
    )

    uf_teste = st.text_input("UF para testar (consulta somente leitura)", value="PI", max_chars=2).strip().upper()

    if st.button("Testar conexão com a GNRE"):
        if not certificado_configurado():
            st.error("Certificado não configurado - preencha o .env primeiro.")
        else:
            with st.spinner("Testando..."):
                cliente = GnreClient()
                resultado_conexao = cliente.testar_conexao()

            if not resultado_conexao["ok"]:
                st.error(resultado_conexao["mensagem"])
            else:
                st.success(resultado_conexao["mensagem"])
                with st.spinner(f"Consultando configuração da UF {uf_teste}..."):
                    config = cliente.consultar_config_uf(uf_teste)

                st.write(f"**Situação:** {config['codigo_situacao']} - {config['descricao_situacao']}")

                if config["codigo_situacao"] == "102":
                    st.warning(
                        "O CNPJ do certificado ainda não está habilitado para usar o "
                        "webservice da GNRE. Precisa pedir habilitação por e-mail a "
                        "gnre@sefaz.pe.gov.br informando o CNPJ - não dá pra contornar no código."
                    )
                elif config["receitas"]:
                    st.dataframe(pd.DataFrame(config["receitas"]), use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum código de receita retornado para essa UF.")
