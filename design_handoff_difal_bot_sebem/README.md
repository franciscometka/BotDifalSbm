# Handoff: DIFAL Bot Sebem — tela de controle fiscal (dashboard interno)

## Overview
Tela interna única (uso do setor fiscal/financeiro da Sebem, 1–2 usuários) para processar XMLs de NF-e e conferir quais notas exigem recolhimento de DIFAL (EC 87/2015). Layout: sidebar fixa de ingestão de arquivos + área principal com resumo do lote, indicadores, abas e tabela de notas com detalhes fiscais expansíveis.

## About the Design Files
Os arquivos deste pacote são **referências de design feitas em HTML** — protótipos que mostram aparência e comportamento pretendidos, **não** código de produção para copiar. A tarefa é **recriar este design no ambiente existente do codebase alvo** (React/Vue/etc.) usando seus padrões e bibliotecas. Se ainda não houver ambiente, escolher o framework mais adequado e implementar lá. O arquivo `.dc.html` é um formato de protótipo próprio: template + uma classe de lógica (estado de aba, linha expandida, filtros) — leia-o como especificação, não como fonte.

## Fidelity
**Hi-fi.** Cores, tipografia, espaçamentos, estados e copy são finais. Recriar com fidelidade, usando componentes equivalentes do design system do codebase quando existirem.

## Screens / Views

### 1. Dashboard "DIFAL Bot Sebem" (tela única)
**Purpose:** subir XMLs, processar o lote e auditar nota por nota.

**Layout geral:** `display:flex`, `min-height:100vh`, fundo `#f4f4f2`.
- Sidebar: `flex: 0 0 304px`, fundo `#ffffff`, `border-right: 1px solid #e2e2dd`, padding `22px 20px 20px`, `flex-direction: column`, `gap: 28px`.
- Main: `flex: 1 1 auto; min-width: 0`, padding `26px 32px 48px`, `flex-direction: column`, `gap: 22px`.

#### Sidebar
1. **Marca**: quadrado 30×30, `border-radius: 7px`, fundo `#14548c`, texto "DB" branco 12px/700. Ao lado: "DIFAL Bot Sebem" 14px/600, `letter-spacing:-0.01em`; subtítulo "Controle fiscal interno" 11px `#82837b`.
2. **Bloco de upload**: label de seção "ENTRADA DE ARQUIVOS" (11px/600, `letter-spacing:.07em`, uppercase, `#82837b`). Dropzone: `border: 1px dashed #cfcfc7`, `radius 8px`, fundo `#fafaf8`, padding `22px 16px`, centralizado, cursor pointer; ícone 26×26 (borda `#cfcfc7`, radius 6, fundo branco, glifo "↑"); título "Arraste os XMLs aqui" 12.5px/500 `#3c3d36`; hint "ou clique para selecionar · .xml, .zip" 11px `#92938a`. Hover/drag-over: borda `#14548c`, fundo `#f5f8fb`. Aceita drop de arquivos (dragover/dragleave/drop) e clique para abrir file picker.
3. **Fila de arquivos**: itens `border:1px solid #e9e9e3`, radius 6, padding `6px 8px`, nome em mono 11px truncado com ellipsis + tamanho 10.5px `#92938a`.
4. **Botão principal "Processar XMLs"** — único elemento de destaque forte: fundo e borda `#14548c`, texto branco 13px/600, padding `10px 14px`, radius 7; hover `#0e3d68`. Em processamento troca o rótulo para "Processando…" (mock: 1400ms).
5. Nota de rodapé do bloco: "Somente NF-e de saída interestadual são avaliadas." 10.5px `#92938a`.
6. **Último lote** (`margin-top:auto`, `border-top:1px solid #e9e9e3`, padding-top 14): label uppercase + linhas rótulo/valor 12px (rótulo `#6f7068`, valor em mono `#23241f`): Arquivos 44 · Processado às 14:32 · Data 31/07/2026. Rodapé "Lote #2026-0731-03 · usuário fiscal.sebem" 11px `#92938a`.

#### Main — cabeçalho
Título `h1` "Resumo do lote" 21px/600 `letter-spacing:-0.015em` `#23241f`; subtítulo 12.5px `#82837b`: "44 XMLs recebidos · apuração de DIFAL por UF de destino · competência 07/2026". À direita, link discreto "Baixar Excel do lote" 12.5px/500 `#14548c` com selo 17×17 (borda `#b9c9d8`, radius 4, glifo "↓").

#### Main — 4 cards de indicador
Grid `repeat(auto-fit, minmax(184px, 1fr))`, gap 12. Card padrão: fundo `#fff`, `border:1px solid #e2e2dd`, radius 8, padding `14px 16px 15px`, coluna com gap 8. Label uppercase 11px/600 `#82837b`; número em IBM Plex Mono 27px/500 `letter-spacing:-0.02em`, `line-height:1`; legenda 11.5px `#92938a`.
- Processados — 42 — "de 44 arquivos enviados"
- **Com DIFAL — 11 — "notas exigem recolhimento"** → estado de alerta quando valor > 0: fundo `#fffaf5`, borda `#e8c9a4`, label `#9a6321`, número `#8a4f13`, legenda `#a1743f`
- Com erro — 2 — "XML inválido ou incompleto"
- Valor total de DIFAL — 3.482,17 — "em reais, somando as 11 notas"

#### Main — abas
Linha com `border-bottom: 1px solid #e2e2dd`, gap 22. Botões-texto 13px/500 `#6f7068` (hover `#23241f`), padding-bottom 9px. Aba ativa: cor `#14548c` + `border-bottom: 2px solid #14548c` (aba inativa: underline transparente). À direita, hint 11.5px `#92938a`: "Ordenado por número da NF" (aba 1) / "Agrupado por UF de destino" (aba 2). Abas: **Notas processadas** (default) e **DIFAL por UF**.

#### Aba "Notas processadas"
Card `#fff`, borda `#e2e2dd`, radius 8, `overflow-x: auto`. Grade de 7 colunas idêntica em cabeçalho, linhas, rodapé e painel de detalhe: `grid-template-columns: 76px 108px minmax(120px,1fr) 48px 104px 104px 36px; gap: 12px; min-width: 660px` (min-width garante que bordas/hover/fundos acompanhem a rolagem horizontal).
- **Cabeçalho**: fundo `#fafaf8`, `border-bottom:1px solid #e9e9e3`, padding `10px 16px`, 10.5px/600 uppercase `#82837b`: Status · Número NF · Cliente · UF · Valor da NF (dir.) · DIFAL (dir.) · (vazio).
- **Linha**: wrapper com `border-bottom: 1px solid #f0f0ea`; grade clicável (toggle do detalhe), padding `12px 16px` (densidade confortável) ou `8px 16px` (compacta), hover `background:#fbfbf9`.
  - Status = badge: 11px/600, padding `3px 8px 3px 7px`, radius 4, ponto 5×5 circular. OK → fundo `#f1f8f3`, texto `#256b41`, borda `#c9e3d3`, ponto `#2f8b52`. Erro → `#fdf2f2` / `#a02222` / `#f0cccc` / ponto `#c23434`.
  - Número NF, UF, Valor, DIFAL em IBM Plex Mono 12.5px, `font-variant-numeric: tabular-nums`, valores alinhados à direita. Cliente 13px `#23241f` truncado.
  - DIFAL: `#8a4f13` quando > 0; `#92938a` quando 0,00 ou linha com erro.
  - Coluna final: botão 22×22, borda `#e2e2dd`, radius 5, glifo "▾" / "▴" quando aberto.
- **Painel de detalhe** (linha expandida, só uma por vez): fundo `#fafaf8`, `border-top:1px solid #f0f0ea`, padding `16px 16px 18px 92px`, coluna gap 16.
  - "Chave de acesso": label uppercase 10.5px + valor mono 12px `letter-spacing:.02em` (formatada em blocos de 4).
  - Grid `repeat(4, minmax(0,1fr))`, gap `14px 20px`, cada item label uppercase 10.5px `#82837b` + valor mono 12.5px: CFOPs, NCMs, Base de cálculo ICMS, Alíquota interestadual, ICMS origem, ICMS destino, FCP destino, DIFAL a recolher (na cor do DIFAL).
  - Rodapé do painel em flex space-between: observação 11.5px `#82837b` (motivo do DIFAL ou mensagem de erro) e, **somente quando a nota é OK e DIFAL > 0**, link "Baixar guia GNRE desta nota" 12.5px/500 `#14548c` com selo 17×17 (borda `#b9c9d8`, radius 4, texto "PDF" 9px).
- **Rodapé da tabela**: fundo `#fafaf8`, padding `11px 16px`, 11.5px `#82837b`: "Exibindo N de 9 notas" (+ " · filtro: apenas com DIFAL ou erro" quando o filtro está ativo) e, à direita, "Clique em uma linha para ver os detalhes fiscais".

#### Aba "DIFAL por UF"
Mesmo card. Grade: `56px 68px minmax(110px,1fr) 110px 110px; gap:12px; min-width:600px`. Colunas: UF · Notas · Participação no lote · Base total (dir.) · DIFAL (dir.). Participação = barra 6px de altura, trilha `#f0f0ea`, preenchimento `#14548c`, radius 3, com percentual mono 11.5px `#82837b` à direita (largura fixa 42px). Linha de total no fim com fundo `#fafaf8` (11 notas · 58.204,90 · 3.482,17).

## Interactions & Behavior
- Clique na linha (ou no botão de caret) abre/fecha o detalhe fiscal; apenas uma linha aberta por vez (default: primeira nota).
- Troca de abas é client-side, sem recarregar dados.
- Dropzone: dragover destaca (borda accent + fundo azul claro), dragleave/drop limpam o destaque; clique abre o file picker. Aceita .xml e .zip.
- "Processar XMLs": estado de carregamento com rótulo "Processando…" enquanto o lote roda; no real, desabilitar e mostrar progresso do lote.
- Link do Excel: baixa a planilha do lote. Link GNRE: baixa o PDF da guia daquela nota (visível só em notas OK com DIFAL > 0).
- Erros por nota não interrompem o lote: a nota entra com badge "Erro", campos "—" e a mensagem no detalhe.
- Sem breakpoints mobile (ferramenta desktop). Responsividade necessária: cards de indicador quebram via `auto-fit`; tabelas rolam na horizontal.

## State Management
- `tab`: "notas" | "uf"
- `open`: número da NF expandida | null
- `drag`: boolean (dropzone destacada)
- `processing`: boolean (lote em execução)
- Props/preferências: `density` ("confortável" | "compacta"), `onlyDifal` (boolean — filtra para notas com DIFAL > 0 ou com erro)
- Dados: lote atual (lista de notas com campos fiscais), agregação por UF, resumo do último lote. No real: POST dos XMLs → job de processamento → GET do lote; endpoints de download (xlsx do lote, pdf/GNRE por nota).

### Modelo de dados por nota (como no protótipo)
`numero, cliente, uf, valor, difal, ok (bool), chave, cfops, ncms, base, aliqInter, icmsOrigem, icmsDestino, fcp, obs` — valores monetários já formatados pt-BR no protótipo; no real, enviar numérico e formatar na view.

## Design Tokens
- Fundo app `#f4f4f2`; superfície `#ffffff`; superfície sutil `#fafaf8`; hover de linha `#fbfbf9`
- Bordas: `#e2e2dd` (container), `#e9e9e3` (interna), `#f0f0ea` (divisor de linha), `#cfcfc7` (dashed)
- Texto: `#23241f` (primário), `#3c3d36`, `#6f7068`, `#82837b` (secundário), `#92938a` (terciário)
- Accent (único): `#14548c`; hover `#0e3d68`; borda leve de selo `#b9c9d8`
- Alerta/DIFAL: fundo `#fffaf5`, borda `#e8c9a4`, texto `#8a4f13` / `#9a6321` / `#a1743f`
- Sucesso: `#f1f8f3` / `#c9e3d3` / `#256b41` / ponto `#2f8b52`
- Erro: `#fdf2f2` / `#f0cccc` / `#a02222` / ponto `#c23434`
- Tipografia: "IBM Plex Sans" (400/500/600/700) para UI; "IBM Plex Mono" (400/500) para todo dado numérico, chave, CFOP/NCM. Escala: 21 (h1), 27 (valor de KPI), 13/12.5 (corpo e tabela), 11.5 (legenda), 11/10.5 (labels uppercase, `letter-spacing:.07em`)
- Radius: 4 (badge/selo), 5–6 (botão pequeno/item), 7 (botão principal, mark), 8 (cards)
- Espaçamento: 12 (gap de grid), 16 (padding horizontal de tabela), 20–22 (padding da sidebar / gap de main), 26–32 (padding do main)
- Sem sombras, sem gradientes, sem ilustração — hierarquia só por tipografia, borda fina e espaço em branco.

## Assets
Nenhuma imagem. Ícones são glifos de texto (↑ ↓ ▾ ▴) e devem ser substituídos por ícones do design system do codebase (upload, download, chevron). Fontes via Google Fonts (IBM Plex Sans / IBM Plex Mono).

## Files
- `DIFAL Bot Sebem.dc.html` — protótipo completo (template + lógica de aba/expansão/filtros)
