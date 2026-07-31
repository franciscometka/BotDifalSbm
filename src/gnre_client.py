"""
Cliente do webservice da GNRE, autenticado com o certificado e-CNPJ.

Baseado no Manual de Integração - Contribuintes GNRE v2.15 (baixado
direto do portal oficial em gnre.pe.gov.br/gnre/v/downloads/index,
com os XSDs reais inclusos) - não é mais um schema adivinhado.

Estado atual:
  - `obter_wsdl` / `testar_conexao`: leitura pura do WSDL, só pra
    confirmar que o certificado autentica.
  - `consultar_config_uf`: chamada real, também só-leitura, que
    devolve os códigos de receita e regras de preenchimento de uma UF
    direto da GNRE (schema confirmado contra consulta_config_uf_v1.00.xsd
    e config_uf_v1.00.xsd).
  - `enviar_lote`: AINDA NÃO IMPLEMENTADO. O schema do lote
    (TLote_GNRE, em lote_gnre_v2.00.xsd/dados_gnre_v2.00.xsd) já foi
    conferido, mas enviar guia de verdade é uma ação com consequência
    real - só vale implementar depois que `consultar_config_uf`
    confirmar que o CNPJ está habilitado, e testando bem em
    homologação antes de cogitar produção.

Endpoints (confirmados batendo o certificado TLS do servidor):
  - Produção: https://www.gnre.pe.gov.br/gnreWS/services/<Servico>
  - Homologação: https://testegnre.sefaz.pe.gov.br/gnreWS/services/<Servico>

IMPORTANTE: mesmo com o certificado correto, a GNRE exige que o CNPJ
seja habilitado antes (pedido por e-mail a gnre@sefaz.pe.gov.br). Sem
isso, `consultar_config_uf` responde com o código de situação "102"
("CNPJ não habilitado para uso do serviço").
"""

import xml.etree.ElementTree as ET

from requests import Session
from requests_pkcs12 import Pkcs12Adapter

from src.config import ambiente_gnre, certificado_configurado, certificado_path, certificado_senha

SERVICOS = [
    "GnreConfigUF",
    "GnreLoteRecepcao",
    "GnreResultadoLote",
    "GnreLoteRecepcaoConsulta",
    "GnreResultadoLoteConsulta",
]

BASES_POR_AMBIENTE = {
    "producao": "https://www.gnre.pe.gov.br/gnreWS/services",
    "homologacao": "https://testegnre.sefaz.pe.gov.br/gnreWS/services",
}

# "1" = produção, "2" = homologação (confirmado no schema consulta_config_uf_v1.00.xsd)
CODIGO_AMBIENTE = {"producao": "1", "homologacao": "2"}

NS_GNRE = "http://www.gnre.pe.gov.br"


class GnreClient:
    """Cliente HTTPS autenticado com o certificado e-CNPJ configurado no .env."""

    def __init__(self):
        if not certificado_configurado():
            raise RuntimeError(
                "Certificado não configurado. Defina GNRE_CERT_PATH e GNRE_CERT_PASSWORD "
                "no arquivo .env antes de usar o GnreClient."
            )

        self.ambiente = ambiente_gnre()
        self.base_url = BASES_POR_AMBIENTE[self.ambiente]

        self._sessao = Session()
        self._sessao.mount(
            "https://",
            Pkcs12Adapter(
                pkcs12_filename=str(certificado_path()),
                pkcs12_password=certificado_senha(),
            ),
        )

    def obter_wsdl(self, servico, timeout=15):
        """
        Busca o WSDL real do serviço informado (ex.: "GnreConfigUF").

        Chamada somente de leitura - não envia nem altera nada. Serve
        pra confirmar que o certificado autentica e pra obter o schema
        oficial antes de implementar o envio de lote de verdade.
        """
        if servico not in SERVICOS:
            raise ValueError(f"Serviço desconhecido: {servico}. Opções: {SERVICOS}")

        url = f"{self.base_url}/{servico}?wsdl"
        resposta = self._sessao.get(url, timeout=timeout)
        resposta.raise_for_status()
        return resposta.text

    def testar_conexao(self):
        """
        Testa se o certificado autentica corretamente, buscando o WSDL
        de GnreConfigUF (o serviço mais simples e só-leitura).

        Retorna um dict {"ok": bool, "mensagem": str, "detalhe": str|None}.
        Nunca inclui a senha do certificado na mensagem.
        """
        try:
            wsdl = self.obter_wsdl("GnreConfigUF")
            return {
                "ok": True,
                "mensagem": f"Conexão OK no ambiente '{self.ambiente}'. WSDL recebido ({len(wsdl)} caracteres).",
                "detalhe": wsdl[:500],
            }
        except Exception as erro:
            return {
                "ok": False,
                "mensagem": f"Falha ao conectar no ambiente '{self.ambiente}': {erro}",
                "detalhe": None,
            }

    def consultar_config_uf(self, uf, timeout=20):
        """
        Consulta as regras de preenchimento da GNRE para uma UF (código
        de receita, se exige documento de origem, data de vencimento
        etc.) - somente leitura, não envia nem altera nada.

        Retorna um dict:
          - codigo_situacao / descricao_situacao: retorno da GNRE (ex.:
            "102" = CNPJ não habilitado para uso do serviço).
          - receitas: lista de {"codigo": str, "descricao": str} (vazia
            se a consulta não retornou receitas, ex.: por falta de
            habilitação do CNPJ).
        """
        ambiente_codigo = CODIGO_AMBIENTE[self.ambiente]
        envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap12:Envelope xmlns:soap12="http://schemas.xmlsoap.org/soap/envelope/">
  <soap12:Header>
    <gnreCabecMsg xmlns="http://www.gnre.pe.gov.br/webservice/GnreConfigUF">
      <versaoDados>2.00</versaoDados>
    </gnreCabecMsg>
  </soap12:Header>
  <soap12:Body>
    <gnreDadosMsg xmlns="http://www.gnre.pe.gov.br/webservice/GnreConfigUF">
      <TConsultaConfigUf xmlns="{NS_GNRE}">
        <ambiente>{ambiente_codigo}</ambiente>
        <uf>{uf.strip().upper()}</uf>
      </TConsultaConfigUf>
    </gnreDadosMsg>
  </soap12:Body>
</soap12:Envelope>"""

        url = f"{self.base_url}/GnreConfigUF"
        headers = {
            "Content-Type": (
                'application/soap+xml; charset=utf-8; '
                'action="http://www.gnre.pe.gov.br/webservice/GnreConfigUF/consultar"'
            )
        }
        resposta = self._sessao.post(url, data=envelope.encode("utf-8"), headers=headers, timeout=timeout)
        resposta.raise_for_status()

        ns = {"g": NS_GNRE}
        raiz = ET.fromstring(resposta.text)

        situacao = raiz.find(".//g:situacaoConsulta", ns)
        codigo_situacao = situacao.findtext("g:codigo", default="", namespaces=ns) if situacao is not None else ""
        descricao_situacao = situacao.findtext("g:descricao", default="", namespaces=ns) if situacao is not None else ""

        receitas = [
            {"codigo": el.get("codigo", ""), "descricao": el.get("descricao", "")}
            for el in raiz.findall(".//g:receitas/g:receita", ns)
        ]

        return {
            "codigo_situacao": codigo_situacao,
            "descricao_situacao": descricao_situacao,
            "receitas": receitas,
            "xml_bruto": resposta.text,
        }
