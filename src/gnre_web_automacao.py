"""
Preenchimento automatico do formulario publico de emissao individual
de guia da GNRE (https://www.gnre.pe.gov.br/gnre/v/guia/digitar).

Esse formulario e publico - NAO exige certificado digital nem
credenciamento previo (diferente do webservice em src/gnre_client.py).
Mas ele tem um reCAPTCHA de imagens na etapa final, e o sistema NUNCA
resolve captcha sozinho (isso e phishing/bypass de bot-detection,
proibido). Por isso este modulo preenche tudo e para exatamente antes
do captcha - o usuario so precisa resolver o captcha e clicar no botao
final pra gerar/baixar o PDF.

Os ids dos campos foram mapeados inspecionando o HTML real do
formulario (nao sao documentados publicamente), entao podem quebrar se
a GNRE mudar o layout do site - nesse caso, os ids/fluxo precisam ser
remapeados.
"""

import unicodedata
from datetime import datetime, timedelta

from src.empresa import DADOS_EMITENTE

URL_GERAR_GUIA = "https://www.gnre.pe.gov.br:444/gnre/v/guia/digitar"

RECEITA_DIFAL_OPERACAO = "100102"  # ICMS Consumidor Final Nao Contribuinte Outra UF por Operacao
RECEITA_FCP_OPERACAO = "100129"    # ICMS Fundo Estadual de Combate a Pobreza por Operacao


def _normalizar(texto):
    """Maiusculo e sem acento, pra comparar com as opcoes da GNRE (que nao usam acento)."""
    texto = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return texto.strip().upper()


def _selecionar_municipio_por_nome(page, seletor, nome_municipio):
    """Seleciona o município na lista comparando nomes sem acento. Retorna True se achou."""
    opcoes = page.eval_on_selector_all(f"{seletor} option", "els => els.map(e => e.textContent)")
    alvo = _normalizar(nome_municipio)
    for opcao in opcoes:
        if _normalizar(opcao) == alvo:
            page.select_option(seletor, label=opcao)
            return True
    return False


def preencher_formulario_gnre(page, linha, receita, valor, data_vencimento=None):
    """
    Preenche o formulario de emissao individual da GNRE numa `page` do
    Playwright ja aberta. Para exatamente antes/no reCAPTCHA - nao
    resolve o captcha nem clica em nenhum botao final de geracao.

    `linha` e o dict de uma nota processada (ver src/processor.py).
    `receita` e "100102" (DIFAL) ou "100129" (FCP) - sao guias separadas.
    `valor` e o valor numerico dessa guia especifica.

    Retorna um dict com avisos (ex.: se o município do destinatário não
    foi encontrado na lista, o que precisa ser preenchido manualmente).
    """
    avisos = []
    uf_destino = linha["uf_destino"]

    if data_vencimento is None:
        data_vencimento = (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y")

    page.goto(URL_GERAR_GUIA, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(500)

    # Passo 1: UF favorecida + tipo de GNRE
    page.select_option("#ufFavorecida", uf_destino)
    page.wait_for_timeout(400)
    page.check("#optGnreSimples", force=True)
    page.click("#validar")
    page.wait_for_timeout(1000)

    # Passo 2: emitente (Sebem) + receita
    page.check("#optNaoInscrito", force=True)
    page.wait_for_timeout(400)
    page.check("#tipoCNPJ", force=True)
    page.fill("#documentoEmitente", DADOS_EMITENTE["cnpj"])
    page.fill("#razaoSocialEmitente", DADOS_EMITENTE["razao_social"])
    page.fill("#enderecoEmitente", DADOS_EMITENTE["endereco"])
    page.select_option("#ufEmitente", DADOS_EMITENTE["uf"])
    page.wait_for_timeout(600)
    if not _selecionar_municipio_por_nome(page, "#municipioEmitente", DADOS_EMITENTE["municipio"]):
        avisos.append(f"Município do emitente '{DADOS_EMITENTE['municipio']}' não encontrado na lista - confirme manualmente.")
    page.fill("#cepEmitente", DADOS_EMITENTE["cep"])
    if DADOS_EMITENTE.get("telefone"):
        page.fill("#telefoneEmitente", DADOS_EMITENTE["telefone"])
    page.select_option("#receita", receita)
    page.wait_for_timeout(400)
    page.click("#validar")
    page.wait_for_timeout(1000)

    # Passo 3: documento de origem, valor, destinatário
    page.select_option("#tipoDocOrigem", "10")  # Nota Fiscal
    page.fill("#numeroDocumentoOrigem", linha["numero_nf"])
    page.check("#tipoValorPrincipal", force=True)
    page.fill("#valor", f"{valor:.2f}".replace(".", ","))
    page.fill("#dataVencimento", data_vencimento)

    page.check("#optNaoInscritoDest", force=True)
    page.wait_for_timeout(600)

    doc_destinatario = (linha.get("doc_destinatario") or "").strip()
    if len(doc_destinatario) == 14:
        page.check("#tipoCNPJDest", force=True)
    else:
        page.check("#tipoCPFDest", force=True)
    page.fill("#documentoDestinatario", doc_destinatario)
    page.fill("#razaoSocialDestinatario", linha.get("nome_destinatario", ""))

    municipio_destinatario = linha.get("municipio_destinatario", "")
    if municipio_destinatario:
        if not _selecionar_municipio_por_nome(page, "#municipioDestinatario", municipio_destinatario):
            avisos.append(f"Município do destinatário '{municipio_destinatario}' não encontrado na lista - selecione manualmente.")
    else:
        avisos.append("XML não trouxe o município do destinatário - selecione manualmente.")

    # Dispara a validacao final - normalmente e aqui que o reCAPTCHA aparece.
    page.click("#validar")
    page.wait_for_timeout(1500)

    avisos.append(
        "Formulário preenchido. Resolva o reCAPTCHA e confira todos os dados antes de "
        "clicar no botão final de gerar a guia - o sistema não faz isso sozinho."
    )

    return {"avisos": avisos}
