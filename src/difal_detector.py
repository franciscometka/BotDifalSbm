"""
Regra de deteccao de DIFAL.

Regra inicial (simples, de proposito): se o valor de ICMS UF destino
(vICMSUFDest) for maior que zero, a nota precisa de DIFAL.
"""


def precisa_difal(dados_nfe):
    """Recebe o dict retornado por xml_reader.ler_nfe e diz se precisa DIFAL."""
    return dados_nfe.get("valor_icms_uf_dest", 0.0) > 0
