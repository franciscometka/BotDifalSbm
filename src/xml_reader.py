"""
Leitura de XMLs de NF-e.

Extrai os dados fiscais que interessam pro controle de DIFAL a partir
de um arquivo XML de NF-e (modelo 55, layout 4.0).
"""

import xml.etree.ElementTree as ET

# Namespace padrao da NF-e. Todos os elementos do XML vivem dentro dele.
NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


def _texto(elemento, caminho, raiz=None):
    """Busca um texto dentro de `elemento` usando o caminho com namespace nfe:."""
    alvo = elemento.find(caminho, NS)
    if alvo is not None and alvo.text is not None:
        return alvo.text.strip()
    return ""


def _numero(valor):
    """Converte string em float, tratando vazio/None como 0.0."""
    if not valor:
        return 0.0
    try:
        return float(valor)
    except ValueError:
        return 0.0


def ler_nfe(caminho_xml):
    """
    Le um arquivo XML de NF-e e retorna um dicionario com os dados fiscais.

    Levanta ValueError se o XML nao tiver a estrutura esperada de NF-e
    (por exemplo, se for outro tipo de documento).
    """
    tree = ET.parse(caminho_xml)
    root = tree.getroot()

    inf_nfe = root.find(".//nfe:infNFe", NS)
    if inf_nfe is None:
        raise ValueError("Estrutura infNFe nao encontrada no XML")

    # Chave de acesso: vem do atributo Id, no formato "NFe" + 44 digitos.
    chave = inf_nfe.get("Id", "")
    if chave.startswith("NFe"):
        chave = chave[3:]

    ide = inf_nfe.find("nfe:ide", NS)
    emit = inf_nfe.find("nfe:emit", NS)
    dest = inf_nfe.find("nfe:dest", NS)
    total = inf_nfe.find("nfe:total/nfe:ICMSTot", NS)

    numero_nf = _texto(ide, "nfe:nNF") if ide is not None else ""
    serie = _texto(ide, "nfe:serie") if ide is not None else ""
    data_emissao = _texto(ide, "nfe:dhEmi") if ide is not None else ""
    if not data_emissao and ide is not None:
        # Layouts antigos usavam dEmi em vez de dhEmi.
        data_emissao = _texto(ide, "nfe:dEmi")

    cnpj_emitente = _texto(emit, "nfe:CNPJ") if emit is not None else ""

    nome_destinatario = ""
    doc_destinatario = ""
    uf_destino = ""
    municipio_destinatario = ""
    if dest is not None:
        nome_destinatario = _texto(dest, "nfe:xNome")
        doc_destinatario = _texto(dest, "nfe:CNPJ") or _texto(dest, "nfe:CPF")
        uf_destino = _texto(dest, "nfe:enderDest/nfe:UF")
        municipio_destinatario = _texto(dest, "nfe:enderDest/nfe:xMun")

    valor_total_nf = _numero(_texto(total, "nfe:vNF")) if total is not None else 0.0

    # Os itens (det) trazem CFOP/NCM e os valores de ICMS UF destino (DIFAL),
    # que sao somados quando ha mais de um item na nota.
    cfops = []
    ncms = []
    valor_icms_uf_dest = 0.0
    valor_fcp_uf_dest = 0.0
    valor_icms_uf_remet = 0.0
    base_calculo_icms_uf_dest = 0.0
    aliquota_icms_uf_dest = ""

    for det in inf_nfe.findall("nfe:det", NS):
        prod = det.find("nfe:prod", NS)
        if prod is not None:
            cfop = _texto(prod, "nfe:CFOP")
            ncm = _texto(prod, "nfe:NCM")
            if cfop:
                cfops.append(cfop)
            if ncm:
                ncms.append(ncm)

        icms_uf_dest = det.find("nfe:imposto/nfe:ICMSUFDest", NS)
        if icms_uf_dest is not None:
            valor_icms_uf_dest += _numero(_texto(icms_uf_dest, "nfe:vICMSUFDest"))
            valor_fcp_uf_dest += _numero(_texto(icms_uf_dest, "nfe:vFCPUFDest"))
            valor_icms_uf_remet += _numero(_texto(icms_uf_dest, "nfe:vICMSUFRemet"))
            base_calculo_icms_uf_dest += _numero(_texto(icms_uf_dest, "nfe:vBCUFDest"))
            # A aliquota e a mesma pra todos os itens na pratica - guarda a ultima encontrada.
            aliquota_icms_uf_dest = _texto(icms_uf_dest, "nfe:pICMSUFDest") or aliquota_icms_uf_dest

    return {
        "numero_nf": numero_nf,
        "serie": serie,
        "chave_acesso": chave,
        "data_emissao": data_emissao,
        "cnpj_emitente": cnpj_emitente,
        "nome_destinatario": nome_destinatario,
        "doc_destinatario": doc_destinatario,
        "uf_destino": uf_destino,
        "municipio_destinatario": municipio_destinatario,
        "valor_total_nf": valor_total_nf,
        "valor_icms_uf_dest": valor_icms_uf_dest,
        "valor_fcp_uf_dest": valor_fcp_uf_dest,
        "valor_icms_uf_remet": valor_icms_uf_remet,
        "base_calculo_icms_uf_dest": base_calculo_icms_uf_dest,
        "aliquota_icms_uf_dest": aliquota_icms_uf_dest,
        "cfops": cfops,
        "ncms": ncms,
    }
