"""
Testa a conexao com o webservice da GNRE usando o certificado configurado
no .env. NAO envia nenhuma guia - so confirma que o certificado autentica
e consulta as regras de uma UF (tambem so leitura).

Uso:
    python testar_gnre.py [UF]

Se a UF nao for informada, usa "PI" como exemplo.
"""

import sys

from src.config import descrever_status, certificado_configurado
from src.gnre_client import GnreClient


def main():
    uf = sys.argv[1].upper() if len(sys.argv) > 1 else "PI"

    print("Status da configuração:", descrever_status())

    if not certificado_configurado():
        print(
            "\nConfigure o arquivo .env antes de testar (copie .env.example para "
            ".env e preencha GNRE_CERT_PATH e GNRE_CERT_PASSWORD)."
        )
        return

    print("\n1) Testando conexão (WSDL, só leitura)...")
    cliente = GnreClient()
    resultado = cliente.testar_conexao()
    print("Resultado:", "OK" if resultado["ok"] else "FALHOU")
    print(resultado["mensagem"])

    if not resultado["ok"]:
        return

    print(f"\n2) Consultando configuração da UF {uf} (só leitura)...")
    config = cliente.consultar_config_uf(uf)
    print(f"Situação: {config['codigo_situacao']} - {config['descricao_situacao']}")

    if config["codigo_situacao"] == "102":
        print(
            "\n[ATENÇÃO] O CNPJ do certificado ainda não está habilitado para usar "
            "o webservice da GNRE. Isso precisa ser resolvido com a própria GNRE "
            "(e-mail para gnre@sefaz.pe.gov.br informando o CNPJ), não é algo "
            "que dá pra contornar no código."
        )
    elif config["receitas"]:
        print(f"\n{len(config['receitas'])} código(s) de receita encontrados para {uf}:")
        for receita in config["receitas"]:
            print(f"  {receita['codigo']} - {receita['descricao']}")
    else:
        print("\nNenhum código de receita retornado (ver 'situação' acima).")


if __name__ == "__main__":
    main()
