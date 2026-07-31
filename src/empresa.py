"""
Dados fixos da Sebem (emitente), usados para preencher automaticamente
o campo "Contribuinte Emitente" do formulário de emissão de guia da GNRE.

Nenhum desses dados e sigiloso (CNPJ, razao social e endereco sao
publicos), entao ficam direto no codigo - diferente do certificado
digital, que fica so no .env.
"""

DADOS_EMITENTE = {
    "cnpj": "02324478000100",
    "razao_social": "SBM Equipamentos Ltda",
    "endereco": "Rua Rodolf Wolff, 214, Jardim Dona Herminia",
    "municipio": "SAO MATEUS DO SUL",
    "uf": "PR",
    "cep": "83900055",
    "telefone": "",
}
