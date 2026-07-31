"""
Geracao da guia de DIFAL por UF.

Hoje nenhuma UF tem automacao pronta, entao o resultado sempre cai no
caminho manual: a tela mostra o link do portal oficial e os dados que
precisam ser digitados por uma pessoa. O ponto de extensao para
automatizar uma UF no futuro e o dict `AUTOMACOES_POR_UF` abaixo.

O sistema NUNCA paga a guia sozinho - na melhor das hipoteses (quando
uma UF tiver automacao), ele so gera/baixa o PDF em `guias/`.
"""

from pathlib import Path

from src.uf_rules import obter_regra_uf

PASTA_GUIAS = Path("guias")


def _exemplo_automacao_sp(dados_nota, pasta_guias):
    """
    Exemplo de assinatura que uma automacao de UF deveria seguir.

    Recebe os dados da nota (mesmo dict retornado por xml_reader.ler_nfe,
    com chave_acesso, uf_destino, valor_icms_uf_dest etc.) e a pasta onde
    o PDF deve ser salvo. Deve devolver o caminho do PDF gerado.

    Nao esta registrada em AUTOMACOES_POR_UF porque ainda nao existe de
    verdade - fica so como modelo para quando alguem implementar.
    """
    raise NotImplementedError("Automacao de SP ainda nao implementada")


# Registro de automacoes por UF. Adicionar aqui quando uma automacao de
# verdade for implementada (ex.: "SP": _automacao_sp).
AUTOMACOES_POR_UF = {}


def gerar_guia(uf, dados_nota):
    """
    Tenta gerar a guia de DIFAL para a UF da nota.

    Retorna um dict:
      - status: "gerado" (PDF criado em guias/), "manual" (sem
        automacao, preencher no portal) ou "erro".
      - caminho_pdf: caminho do PDF gerado, ou None.
      - mensagem: texto explicativo para mostrar na tela.
      - regra: o dict de regras da UF (portal, url, tipo_guia etc.).
    """
    regra = obter_regra_uf(uf)
    uf_norm = (uf or "").strip().upper()

    if regra["aceita_automacao"] and uf_norm in AUTOMACOES_POR_UF:
        PASTA_GUIAS.mkdir(exist_ok=True)
        try:
            caminho_pdf = AUTOMACOES_POR_UF[uf_norm](dados_nota, PASTA_GUIAS)
            return {
                "status": "gerado",
                "caminho_pdf": str(caminho_pdf),
                "mensagem": "Guia gerada automaticamente em guias/.",
                "regra": regra,
            }
        except Exception as erro:
            return {
                "status": "erro",
                "caminho_pdf": None,
                "mensagem": f"Falha ao gerar a guia automaticamente: {erro}",
                "regra": regra,
            }

    return {
        "status": "manual",
        "caminho_pdf": None,
        "mensagem": (
            f"Ainda não há automação para {uf_norm or 'essa UF'}. "
            "Abra o portal oficial e preencha a guia manualmente com os dados mostrados."
        ),
        "regra": regra,
    }
