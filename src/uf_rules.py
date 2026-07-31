"""
Regras de recolhimento de DIFAL por UF de destino.

Quais UFs usam GNRE foi CONFIRMADO consultando ao vivo o endpoint
oficial do proprio portal da GNRE (gnre.pe.gov.br/gnre/v/guia/getDisponibilidadeUFsv1),
que lista as UFs participantes. SP e ES nao aparecem nessa lista -
ou seja, tem sistema proprio, fora da GNRE. Todas as outras 25 UFs
(incluindo DF) usam GNRE.

Mesmo assim, aliquota e codigo de receita por UF ainda precisam ser
confirmados antes de gerar guia de verdade (ver `codigo_receita`,
que fica None ate ser validado - dá pra obter isso via
`src/gnre_client.py:consultar_config_uf`, uma vez que o CNPJ estiver
habilitado na GNRE).

Campos de cada UF:
- nome_portal: nome do portal onde a guia e emitida.
- url: endereco oficial do portal.
- tipo_guia: "GNRE", "DARE", "DAR", "DUA" ou "Outro".
- aceita_automacao: True quando ja existe uma automacao implementada
  para essa UF em `src/guia_generator.py` (nenhuma ainda no MVP).
- codigo_receita: codigo de receita usado na guia, quando ja
  validado. None quando ainda precisa ser confirmado no portal.
- observacao: texto livre pra qualquer ressalva.
"""

_PADRAO_GNRE = {
    "nome_portal": "GNRE Online",
    "url": "https://www.gnre.pe.gov.br/",
    "tipo_guia": "GNRE",
    "aceita_automacao": False,
    "codigo_receita": None,
    "observacao": "Confirmar aliquota e codigo de receita no portal antes de emitir a guia.",
}

# SP e ES nao aderiram a GNRE (confirmado via getDisponibilidadeUFsv1) - tem sistema proprio.
_SISTEMA_PROPRIO = {
    "nome_portal": "Sistema próprio do estado (não usa GNRE)",
    "url": "",
    "tipo_guia": "Verificar sistema próprio do estado",
    "aceita_automacao": False,
    "codigo_receita": None,
    "observacao": "Esta UF não aderiu à GNRE - confirmar o portal/guia próprio do estado.",
}

REGRAS_UF = {
    "AC": dict(_PADRAO_GNRE),
    "AL": dict(_PADRAO_GNRE),
    "AP": dict(_PADRAO_GNRE),
    "AM": dict(_PADRAO_GNRE),
    "BA": dict(_PADRAO_GNRE),
    "CE": dict(_PADRAO_GNRE),
    "DF": dict(_PADRAO_GNRE),
    "ES": dict(_SISTEMA_PROPRIO),
    "GO": dict(_PADRAO_GNRE),
    "MA": dict(_PADRAO_GNRE),
    "MT": dict(_PADRAO_GNRE),
    "MS": dict(_PADRAO_GNRE),
    "MG": dict(_PADRAO_GNRE),
    "PA": dict(_PADRAO_GNRE),
    "PB": dict(_PADRAO_GNRE),
    "PR": dict(_PADRAO_GNRE),
    "PE": dict(_PADRAO_GNRE),
    "PI": dict(_PADRAO_GNRE),
    "RJ": dict(_PADRAO_GNRE),
    "RN": dict(_PADRAO_GNRE),
    "RS": dict(_PADRAO_GNRE),
    "RO": dict(_PADRAO_GNRE),
    "RR": dict(_PADRAO_GNRE),
    "SC": dict(_PADRAO_GNRE),
    "SP": dict(_SISTEMA_PROPRIO),
    "SE": dict(_PADRAO_GNRE),
    "TO": dict(_PADRAO_GNRE),
}

REGRA_DESCONHECIDA = {
    "nome_portal": "Verificar manualmente",
    "url": "",
    "tipo_guia": "Verificar manualmente",
    "aceita_automacao": False,
    "codigo_receita": None,
    "observacao": "UF nao reconhecida - conferir manualmente.",
}


def obter_regra_uf(uf: str) -> dict:
    """Retorna o dict de regras da UF informada (copia, seguro pra alterar)."""
    if not uf:
        return dict(REGRA_DESCONHECIDA)
    regra = REGRAS_UF.get(uf.strip().upper())
    return dict(regra) if regra else dict(REGRA_DESCONHECIDA)


def portal_sugerido(uf: str) -> str:
    """Retorna apenas o nome do portal sugerido para a UF (compatibilidade)."""
    return obter_regra_uf(uf)["nome_portal"]
