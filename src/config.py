"""
Configuracao sensivel (certificado digital, ambiente GNRE).

Tudo aqui vem de variaveis de ambiente / arquivo .env local (nunca
commitado - ver .gitignore). Nada de caminho de certificado ou senha
deve ser hardcoded em codigo ou aparecer em logs/mensagens de erro.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # le o arquivo .env na raiz do projeto, se existir

AMBIENTES_VALIDOS = {"homologacao", "producao"}


def certificado_path():
    """Caminho do arquivo .pfx, ou None se nao configurado."""
    valor = os.environ.get("GNRE_CERT_PATH", "").strip()
    return Path(valor) if valor else None


def certificado_senha():
    """Senha do certificado. Nunca logar/exibir este valor."""
    return os.environ.get("GNRE_CERT_PASSWORD", "").strip() or None


def ambiente_gnre():
    """'homologacao' (padrao) ou 'producao'."""
    valor = os.environ.get("GNRE_AMBIENTE", "homologacao").strip().lower()
    return valor if valor in AMBIENTES_VALIDOS else "homologacao"


def automacao_habilitada():
    """True somente se GNRE_HABILITAR_AUTOMACAO=true E certificado configurado."""
    flag = os.environ.get("GNRE_HABILITAR_AUTOMACAO", "false").strip().lower() == "true"
    return flag and certificado_configurado()


def certificado_configurado():
    """True se caminho do certificado existe no disco e senha foi informada."""
    caminho = certificado_path()
    senha = certificado_senha()
    return bool(caminho and senha and caminho.exists())


def descrever_status():
    """Resumo legivel do estado da configuracao, sem nunca expor a senha."""
    caminho = certificado_path()
    if not caminho:
        return "Certificado não configurado (defina GNRE_CERT_PATH no .env)."
    if not caminho.exists():
        return f"Arquivo de certificado não encontrado em: {caminho}"
    if not certificado_senha():
        return "Caminho do certificado configurado, mas a senha (GNRE_CERT_PASSWORD) está vazia."
    return (
        f"Certificado configurado ({caminho.name}). "
        f"Ambiente: {ambiente_gnre()}. "
        f"Automação: {'habilitada' if automacao_habilitada() else 'desabilitada'}."
    )
