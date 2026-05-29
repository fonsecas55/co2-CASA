# CLAUDE.md — urban-carbon-sink

## Visão Geral

- **Repo**: `urban-carbon-sink` — refactor profissional da prova de conceito académica em `../PROJETO/CODE/PFC_V3.1/`.
- **Descrição**: pipeline mensal autónomo que quantifica a captura de CO₂ pela vegetação urbana usando o modelo CASA aplicado a imagens Sentinel-2/Sentinel-3, com cobertura do solo via GEE Dynamic World. Outputs (COG + JSON) servidos por GitHub Releases; frontend estático na Vercel.
- **Stack**: Python 3.12, `rasterio`, `numpy`, `typer`, `earthengine-api`, `pydantic`. Sem `snappy` em runtime. Gestão de pacotes via `uv`.
- **Entrada de dados**: Sentinel-2 L2A (B4, B8, B11, B12), Sentinel-3 SLSTR LST (dia/noite), Global Solar Atlas GHI, CAMS solar time-series, GEE Dynamic World.
- **Saída / deployment**: COG + JSON em GitHub Releases (tag `YYYY-MM`); manifesto `releases.json` em branch órfã `data`; frontend Leaflet/MapLibre na Vercel consome via `raw.githubusercontent.com` + URLs determinísticas de release assets.
- **Execução**: GitHub Actions Cron `0 3 1 * *` (dia 1 de cada mês, 03:00 UTC).

## Contexto e Estilo (Vibe)

Sou engenheiro de telecomunicações e computadores. A apresentação do projeto e a arquitetura devem manter uma postura técnica e *lowkey*. O foco é puramente a qualidade da engenharia, o rigor dos dados e a fluidez da aplicação, sem parecer arrogante, "gabarolas" ou *showoff*.

## Ação Requerida e Planeamento Conjunto

- **Análise de diretoria**: acede e explora a diretoria local de trabalho. Presta especial atenção à forma como os ficheiros comunicam entre si (ex.: `main.py`, `calc_NPP.py`, `Param_FPAR.py`, `Param_WSC.py`, `Param_SOL.py`).
- **Plano antes de código**: antes de alterar ou escrever código, **o plano de projeto é feito passo-a-passo em conjunto**. Com base na leitura da diretoria, propõe um roteiro estruturado para a transição para web. Debater e validar em conjunto antes de implementar.

## Objetivos de Otimização (a refletir no plano)

1. **Estratégia para a Web** — definir a melhor arquitetura:
   - (A) Pré-processamento local com exportação de formatos otimizados (ex.: Cloud Optimized GeoTIFFs, JSON) para consumo por uma biblioteca web estática (ex.: Leaflet.js).
   - (B) Construção de uma API Python (FastAPI/Flask) super otimizada que calcule e sirva os dados a pedido.
2. **Fundamentação científica** — a otimização algorítmica (redução de carga no cálculo de FPAR, WSC, SOL, etc.) deve ser baseada em literatura científica validada. Procura ativamente esses estudos para justificar a refatoração do código, ou pede os documentos de validação caso necessário.
3. **Refatoração do código** — identificar gargalos de performance e substituir por processamento paralelo ou vetorização (`numpy`), adequando o sistema à web.
4. **Integração de Dados Dinâmicos (Dynamic World):** No ficheiro `Param_Emax.py`, o modelo utiliza atualmente um mapa estático de cobertura de solo (ESA WorldCover 2021) para mascarar a vegetação e aplicar as constantes de $\epsilon_{max}$. Quero substituir esta abordagem estática por uma chamada dinâmica à API do Google Earth Engine (dataset Dynamic World). O objetivo é que a máscara de vegetação e a atribuição do $\epsilon_{max}$ se adaptem automaticamente às mudanças reais no terreno para o mês e ano da análise, mantendo o sistema 100% atualizado e sem intervenção manual.

## Restrições de Output

- Apresenta o plano e o código de forma clara, modular e direta.
- Explicações estritamente profissionais e minimalistas.
- Sempre que o plano sugerir alterar a lógica matemática do modelo CASA original para ganhos de performance, **referencia a base teórica** que valida a decisão para garantir a precisão dos dados (t CO2).

## Comandos Essenciais

```
# Instalar dependências (cria .venv + resolve uv.lock)
uv sync --extra dev

# Correr testes
uv run pytest -q

# Lint / format
uv run ruff check src tests
uv run ruff format src tests

# Type-check (strict)
uv run mypy

# CLI
uv run casa --help

# Build / Deploy / preview (Vercel)
# <preencher — Fase frontend>
```

Nota: `uv` cria o `.venv` com o Python do sistema se satisfizer `>=3.12`
(aqui 3.14). O código mantém sintaxe-alvo 3.12 (ruff/mypy `target=py312`).

## Padrões a Evitar

- Correr bibliotecas pesadas (`snappy`, `rasterio` em modo full) directamente no runtime web.
- Alterar lógica matemática do modelo CASA sem referência científica que valide o trade-off precisão/performance.
- Tom de comunicação *showoff* ou autopromocional na UI ou em comentários públicos.
- Avançar para implementação antes de o plano estar validado em conjunto.
- Usar PIL para manipular GeoTIFFs (perde CRS/transform).
- Calcular NDVI_min/max ou SIMI_min/max globais por imagem para normalizar FPAR/WSC — introduz drift temporal.
- Hardcode de constantes específicas de Oeiras (população, shapefile, WKT) espalhadas pelo código — central como configuração.
- Caminhos relativos hardcoded (`../NPP_CALC_PROJ/...`) em cada script — usar um único módulo de configuração / variáveis de ambiente.
- Scripts top-level sem `if __name__ == "__main__":` — corre I/O ao simples `import`, quebra testes e composição.
- `input()` interactivo dentro de módulos de cálculo (`SOL_CALC.PY:43`) — inviável serverless e em pipelines.
- CRS / transform hardcoded em `WSC_CALC.py` (`EPSG:4326`, origem 0,0). Tem de vir do produto de origem.
- Calcular `Topt = mean(LST atual)` (`T1_T2_CALC.py`) — Topt é climatológico, não a média da cena do mês.
- Redimensionar GeoTIFFs *out-of-band* depois de gravar (`NPP_CALC.redimensionar_imagens`). Os módulos a montante devem produzir matrizes já na grade-alvo (transform + shape comuns). Sem etapa de "ajustar tamanho" no fim.
- Hack do "último pixel" (`Param_FPAR.py:80-82` — `fpar[fpar == fpar[-1,-1]] = 0`) para mascarar fundo. Frágil; pode apagar pixels válidos. A máscara tem de vir da geometria (WKT/shapefile), não do valor de um pixel.
- Iterar SNAP linha-a-linha para operações vectorizáveis em NumPy (`NDVI_CALC.py`, `Param_FPAR.py::calcular_ndvi`). Ordens de magnitude mais lento sem motivo.
- Commitar `tempCodeRunnerFile.py`, `.idea/`, `.venv/` no repositório.

## Padrões Preferidos

- Vetorização com `numpy` em vez de loops Python puros.
- Formatos otimizados para web (COG, JSON pré-calculado) quando viável.
- Decisões de arquitetura justificadas por literatura ou medições, não por intuição.
- Código modular: separação clara entre cálculo científico (`calc_NPP`, `Param_*`) e camada de apresentação.

## Regras Aprendidas

Atualizada quando pedido. Formato: `data — o que aprendeu — porquê importa`.

- **2026-05-27 — Nunca usar PIL para redimensionar GeoTIFFs** — PIL não preserva CRS, transform nem nodata, e ao gravar sobre o ficheiro destrói a georreferenciação. Usar sempre `rasterio.warp.reproject` ou `rasterio.warp.calculate_default_transform`. Bug presente em `parametros/calc_NPP.py::redimensionar_imagens` corrompia toda a cadeia a jusante (análise por área, sumatórios).
- **2026-05-27 — Não importar `logger` de `venv`** — `venv` é o módulo do builder de virtualenvs, não tem `logger`. Erro tipo: `from venv import logger` em `parametros/Param_SOL.py`. Cada módulo deve fazer `import logging; logger = logging.getLogger(__name__)`.
- **2026-05-27 — FPAR/WSC: usar NDVImin/max e SIMImin/max FIXOS, não por imagem** — calcular min/max sobre a imagem actual destrói a coerência temporal numa série dinâmica (FPAR de Jan 2024 não comparável a Jan 2025). Decidido (2026-05-27) usar parametrização fixa: NDVI 0.05/0.95 inicial (a confirmar contra GMD 2022 [30]); SIMI percentis 2/98 sobre amostra histórica grande. Confronto com o relatório: o Relatório Final-P33 (eq. 2 p.15; eq. 5 p.18) usa min/max por imagem — esta escolha foi validada vs Qinghai num único momento mas é inviável para aplicação web que serve qualquer mês via API. **Trade-off aceite**: invalidar parcialmente a comparação directa com o relatório a favor de rigor temporal.
- **2026-05-27 — Origem dos ε_max do relatório é desconhecida** — relatório atribui Tree=1.0, Shrub=0.7, Grass=1.04, Crop=0.9, Bare=0.25 [g C/MJ] a Papale 2011 [41], mas (i) o DOI da [41] aponta na verdade para Horn & Schulz 2011, paper diferente; (ii) nem Horn & Schulz nem Papale et al. 2011 (BG vol. 8) tabulam ε_max por bioma; (iii) os valores também não batem com o BPLUT MODIS (Xu et al. 2023, *Atmosphere* 14:1161 — Shrub=1.061, Grass=0.86, Crop=1.044). **Decisão (2026-05-27)**: parametrizar ε_max como configuração; default = Xu 2023/BPLUT MODIS (rastreável), override disponível para reproduzir resultados do relatório. Ficheiros: `config/epsilon_max/{xu2023,relatorio}.yml`, com mapeamento para classes Dynamic World (`trees`, `shrub_and_scrub`, `grass`, `crops`, `flooded_vegetation`).
- **2026-05-27 — `download_sentinel_data` usa `authenticate_oidc()` interactivo** — bloqueia execução serverless/web. Para deploy Vercel há de migrar para client credentials flow ou pré-processar localmente.
- **2026-05-27 — A percentagem CAMS em `Param_SOL.py` aplica-se uniformemente a todos os pixels** — funciona para Oeiras (zona pequena, ~46 km²) mas é fisicamente incorrecta para regiões grandes (Açores, Lisboa). É um ajuste temporal, não espacial. Limitação reconhecida no relatório final.
- **2026-05-27 — Hack do "último pixel" para mascarar fundo** — `fpar[fpar == fpar[-1,-1]] = 0` em `Param_FPAR.py:80-82` assume que o pixel inferior-direito é background. Frágil: apaga **todos** os pixels com o mesmo valor, mesmo válidos. A máscara correcta vem da geometria (WKT Oeiras) via `rasterio.mask`, não do valor de um pixel.
- **2026-05-27 — `WSC_CALC.py` perde a georreferenciação por hardcode** — `transform = from_origin(0,0,10,10)` + `crs="EPSG:4326"` (linhas 44-53). Tem de vir do produto Sentinel-2 de origem via `rasterio` (após conversão `.dim` → GeoTIFF) ou via SNAP `getGeoCoding()`.
- **2026-05-27 — `Topt = nanmean(T_mean)` da cena actual é cientificamente errado** — `T1_T2_CALC.py:67-71`. Na literatura CASA, Topt é a temperatura óptima de crescimento *climatológica* da vegetação local (Potter 1993; mapeada a partir de séries longas de NPP histórico ou tabulada por bioma). Usar a média LST do mês actual reduz T1 quase a 1 (sempre próximo do óptimo da cena), eliminando o sinal de stress térmico que o modelo deveria capturar.
- **2026-05-27 — NDVI calculado linha-a-linha via SNAP em `NDVI_CALC.py` e `Param_FPAR.py::calcular_ndvi`** — operação trivialmente vectorizável `(NIR-RED)/(NIR+RED)`. Após o subset SNAP (ou exportação directa para GeoTIFF), todo o resto é `rasterio.read` + `numpy` em massa. Remove dependência de `esa_snappy` no pipeline de cálculo.
- **2026-05-27 — Suspeita de erro de unidades em `NPP_RESULT.py:54`** — `soma_C_t = npp_clean.sum() / 1e6`. NPP em g C/m²/mês × pixel 10×10 m (S2) deveria multiplicar pela área (100 m²) antes de g→t. Possível subestimação por factor 100. **Confirmar contra valores do Relatório Final** antes de assumir que está errado — pode haver normalização implícita nas constantes upstream.
- **2026-05-27 — `esa_snappy` está no caminho crítico (NDVI, FPAR, WSC)** — inviável para Vercel/serverless e pesado em local. Toda a leitura de bandas Sentinel-2 deve passar a `rasterio` após uma única conversão `.SAFE`/`.dim` → GeoTIFF (a fazer no STEP1 com SNAP CLI). A partir daí, zero SNAP em runtime.
- **2026-05-27 — `NPP_RESULT.py:12` tem `EMISSOES_CO2_hab = 0.6` desactualizado** — Relatório Final usa **0.8917 t CO₂/hab/mês** (= 10.7004/ano, Eurostat 2025 [55]). Código ficou para trás. Na refatoração: parametrizar `emissoes_per_capita` como configuração por região (Oeiras, Lisboa, Flores podem ter perfis distintos), default ao valor Eurostat europeu.
- **2026-05-27 — `main.py`, `Download.py`, `analise_NPP.py`, `Param_T1_T2.py` referidos no relatório não existem em `PFC_V3.1/`** — a versão entregue ficou em "scripts soltos sem orquestrador". A refatoração tem de reconstruir o pipeline coerente (CLI ou módulo `__main__`), não copiar os scripts standalone.
- **2026-05-27 — Suspeita não confirmada de bug de unidades em `NPP_RESULT.py:54`** (`sum/1e6`) — estimativa back-of-envelope para Oeiras dá ~15 t C/mês, relatório reporta média ~4521 t C/mês (factor ~300 de diferença). Pode ser área implícita que ainda não localizei OU bug. **Reproduzir o cálculo passo-a-passo com raster real e área Oeiras antes de afirmar erro**. Não tocar nas constantes do relatório até reproduzir.

## Workflow de Git

- Branch principal: _<a confirmar — `main` por defeito>_
- Convenção de commits: _<livre, a definir>_
- PR checklist:
  - [ ] Testes passam
  - [ ] Lint sem erros
  - [ ] CLAUDE.md atualizado se necessário (Regras Aprendidas e/ou Notas por Sessão)

## Estrutura

```
urban-carbon-sink/
├── pyproject.toml                    # uv + PEP 517, deps + entrypoint `casa`
├── README.md / LICENSE / CLAUDE.md / .gitignore
│
├── docs/                             # documentação científica e arquitectural
│   ├── casa-model.md                 # derivação matemática operacional
│   ├── literatura.md                 # bibliografia anotada
│   ├── decisoes-arquitetura.md       # ADRs 001-016
│   └── pipeline.md                   # spec operacional do Cron mensal
│
├── src/casa/                         # pacote Python instalável
│   ├── __init__.py / __main__.py / cli.py
│   ├── config.py                     # YAML → Pydantic
│   ├── geometry.py / grid.py
│   ├── inputs/                       # sentinel2, sentinel3, dynamic_world,
│   │                                 # esa_worldcover, solar_atlas, cams
│   ├── landcover.py                  # ADR-011: dw/esa_to_canonical
│   ├── ndvi.py / fpar.py / wsc.py    # núcleo matemático puro
│   ├── tstress.py / sol.py / emax.py # idem
│   ├── npp.py                        # multiplicação final, windowed
│   ├── pipeline.py / reports.py      # orquestrador + agregação
│
├── config/
│   ├── pipeline.yml                  # tabela ε_max activa, source landcover, window size
│   ├── regions/{oeiras,lisboa,flores}.yml
│   ├── epsilon_max/{xu2023,relatorio}.yml
│   ├── fpar_percentiles.yml / wsc_percentiles.yml / t_opt_by_biome.yml
│
├── data/                             # baseline data
│   ├── geometry/                     # WKT/shapefile por região
│   ├── sol/ghi_base.tif              # Global Solar Atlas baseline
│   └── fallback/                     # stub ESA WorldCover enquanto GEE não aprovado
│
├── tests/{unit,integration,fixtures}/
├── tools/                            # extract_pdf, literature/
├── .github/workflows/ci.yml + monthly_npp.yml
└── frontend/                         # site Vercel (Leaflet + georaster)
```

**Código de referência matemática** (legacy, consultar mas não tocar):
`../PROJETO/CODE/PFC_V3.1/NPP_CALC_PROJ/*_CALC/` — versão entregue do PFC. Bugs documentados nas "Regras Aprendidas" abaixo e em `docs/`.

**Relatório Final-P33** (texto extraído): `tools/relatorio_final.txt` (gerado por `tools/extract_pdf.py`, gitignored).

## Decisões de Arquitectura (confirmadas 2026-05-27)

- **Arquitectura escolhida: (A) Pré-processamento offline → COG/JSON estáticos**, servidos pela Vercel só como ficheiros. Sem Python em runtime. Mantém `snappy` e GDAL/rasterio fora do bundle Vercel.
- **Documentação científica em `docs/` separado** (`docs/casa-model.md`, `docs/literatura.md`, `docs/decisoes-arquitetura.md`); CLAUDE.md fica operacional (regras, padrões, comandos, estrutura). Não despejar derivações ou bibliografia neste ficheiro.
- **Refactor é rewrite, não patch**: o código actual em `CODE/PFC_V3.1/NPP_CALC_PROJ/*_CALC/` é fonte de referência matemática apenas. Versão refactorizada nasce numa árvore nova (a definir).
- **Dynamic World resolvido via automação assíncrona (GitHub Actions Cron mensal)**: pipeline 100% autónomo sem servidor sempre-ligado. Cron mensal chama GEE (`GOOGLE/DYNAMICWORLD/V1`) + Sentinel Hub APIs, corre CASA, gera COG + JSON, commita os outputs. Vercel só serve estáticos. Frontend (Leaflet/MapLibre + georaster) consome COG browser-side. Sem custos de infra runtime, sem manutenção manual, dados frescos automaticamente. Decisões pendentes de Fase 4: (i) onde guardar COGs grandes (LFS, Vercel Blob, Cloudflare R2 ou repo principal); (ii) autenticação GEE em CI (service account JSON em GitHub secret).
- **Parametrização por região**: emissões per capita, geometria (WKT/shapefile), população, e potencialmente `VAR_PCT_MES` (CAMS) viram configuração por zona em `config/regions/{oeiras,lisboa,flores,...}.yml`. Não hardcoded no código.
- **Parametrização ε_max**: duas tabelas em `config/epsilon_max/` — `xu2023.yml` (default, BPLUT MODIS rastreável) e `relatorio.yml` (override para reproduzir resultados publicados). Pipeline lê a tabela apontada por config global. Mapeamento explícito para as 9 classes Dynamic World; classes não-vegetação (`built`, `water`, `bare`, `snow_and_ice`) atribuem 0.

## Referências científicas-chave

Detalhe em `docs/literatura.md`. Referências load-bearing para a refatoração:
- **Xu, Wang, Li 2023** — *NPP and Vegetation Carbon Sink Capacity Estimation of Urban Green Space Using the Optimized CASA Model: A Case Study of Five Chinese Cities*, Atmosphere 14:1161. Forné fórmula FPAR (NDVI + SR, percentis 5/95, eq. 3-6) e tabela ε_max (MOD17 BPLUT, Table 1). É o paper-fonte mais próximo do relatório do utilizador.
- **Dong et al. 2025** — *Assessing Spatiotemporal Dynamics of NPP in Shandong Province Using the CASA Model and Google Earth Engine*, Remote Sens. 17:488. Pipeline análogo (CASA + GEE) — referência para o desenho técnico do GHA Cron.
- **Wu et al. 2022 (GMD)** — *Improved CASA model based on satellite remote sensing*, GMD 15:6919. Definição original do WSC com SIMI (B11, B12).
- **Potter et al. 1993** — modelo CASA original (εmax uniforme 0.389 g C/MJ). Base teórica.

## Contexto Externo

- Deploy: Vercel (portefólio profissional).
- Dados: missões Sentinel-2 / Sentinel-3 (Copernicus).
- Modelo de referência: CASA (Carnegie-Ames-Stanford Approach).
- Docs / Issues / Slack: _<a definir>_

## Notas por Sessão / PR

Atualizada quando pedido. Formato: `data — tarefa — o que ficou por fazer`.

### >>> RETOMAR AQUI (2026-05-29, fim do dia) <<<

**Estado**: Blocos 0→3 concluídos, verdes e no remoto (`origin/main`, último commit `e382907`). 78 testes passam; ruff + mypy limpos sobre `src`/`tests`. Ambiente: `uv sync` em Python 3.12.9 (`.python-version` pinado).

**Arranque amanhã**: `cd urban-carbon-sink` → `uv sync` (se preciso) → `python -m uv run pytest -q` para confirmar verde.

**Decisão pendente (eu perguntei, falta resposta tua)**: próximo passo é
- (A) camada `inputs/` com **fixtures sintéticas** — WarpedVRT resample S3 LST, export GEE Dynamic World, rasterização da geometria (WKT→máscara); ou
- (B) **calibrar a config real de Oeiras** primeiro (geometria/WKT, população, emissões per capita, percentis FPAR/WSC, t_opt) — hoje são placeholders TODO, por isso `offset_fraction`/`net_co2_balance_t` ainda não têm significado físico.

**Dívida menor**: `tools/` (extractor PDF legacy) tem lint ruff pendente, deixado fora de scope. Decidir: corrigir ou adicionar ao `exclude` do ruff.

### 2026-05-29 — Bloco 3 (orquestração + pipeline windowed) [concluído]

**Feito**: `grid.py` + `pipeline.py` + `reports.py` implementados e verdes (78 testes no total; ruff + mypy limpos sobre `src`/`tests`).
- `grid.py`: `utm_epsg_from_lonlat` + `target_grid_from_bbox(bbox_lonlat) -> TargetGrid` (UTM, north-up, snap outward a 10 m). 7 testes.
- `pipeline.py`: `iter_windows`, `run_region(inputs, cfg, month, out)` lê a grade do raster de referência (red), valida shape dos outros (`ValueError "pre-aligned"`), itera janelas, acumula `total_npp_c_t`/`total_npp_co2_t`/`valid_pixels`/`vegetation_pixels`, escreve COG float32 deflate tiled. Teste-chave `test_windowed_accumulation_is_block_invariant` (ADR-012: totais independentes de `window_size`, block 256 vs 16, `rel=1e-9`). 8 testes.
- `reports.py`: `build_report` → `RegionReport` (totais, `CarbonBalance` emissões−absorvido + `offset_fraction`, `Provenance`), `write_report` JSON indent=2. 8 testes.
- mypy: alinhado `FloatArray` do pipeline a `NDArray[np.floating]` (era `float64`); tuplos de config para `fpar` via `np.asarray`. ruff: removidos `int()` redundantes em `grid.py` (RUF046). Nota: `tools/` (extractor PDF legacy) ainda tem lint pendente, fora de scope.

**Por fazer** (camada `inputs/`, bloco posterior): WarpedVRT resample S3 LST, export GEE Dynamic World, rasterização da geometria (WKT→máscara). Calibrar placeholders (percentis FPAR/WSC, t_opt, geometria/população reais de Oeiras).

**Plano** (aprovado): infraestrutura de I/O que gere memória do servidor doméstico.
- `grid.py`: grade-alvo comum a partir do bbox da região → CRS UTM da zona + resolução 10 m. `target_grid_from_bbox(bbox_lonlat) -> TargetGrid(crs, transform, width, height, resolution)`. Puro (pyproj/rasterio.warp, sem ficheiros).
- `pipeline.py`: orquestrador. Loop de janelas (`window_size`, ex. 1024²), lê pedaços com `rasterio` (`window=`), alimenta as funções puras do Bloco 1 com os parâmetros imutáveis do Bloco 2 (`config.load`), acumula somas parciais de NPP-C/CO₂ (× área via `npp.density_to_tonnes`), escreve COG de saída windowed.
- `reports.py`: agrega metadados + totais → JSON estruturado para a Vercel (totais t C/t CO₂, balanço vs emissões da população, proveniência da config, grid/CRS/bbox).

**Duas decisões de engenharia (ver ADR-017)**:
1. **Sequencial, não assíncrono** — trabalho é CPU/GDAL-bound; `asyncio` não traz ganho. Paralelismo (`ProcessPoolExecutor` sobre janelas) adiado por ADR-012. Costura limpa deixada para depois.
2. **Inputs pré-alinhados à grade-alvo** — resample S3 LST (WarpedVRT) e export GEE vivem na camada `inputs/` (offline, bloco posterior). `pipeline.py` lê a grade do raster de referência (red) e valida que os outros batem. `grid.py` define a grade-alvo que a camada de prep usará.

**Isolamento mantido**: janelas e geo-referências morrem no orquestrador; Bloco 1 continua a receber só arrays puros.

### 2026-05-29 — Ponte GitHub + Bloco 2 (config layer)

**Feito**:
- Ambiente pinado a Python 3.12 (`.python-version`, commit `101156c`); `.venv` recriado em 3.12.9.
- **Remoto GitHub ligado**: chave Ed25519 gerada no DFDesk (`~/.ssh/id_ed25519`, sem passphrase). Atenção: registada como **deploy key** do repo `co2-CASA` (não chave de conta) — só serve este repo. Remoto `git@github.com:fonsecas55/co2-CASA.git`; `main` pushed e a fazer track de `origin/main`. Conta: **@fonsecas55**.
- **Bloco 2 — config layer**: `src/casa/config.py` (Pydantic v2, todos os modelos `frozen=True`). Tabelas numéricas guardadas como **tuplos** indexados por código canónico (imutabilidade real, não só anti-reatribuição). `RegionConfig.bbox` = `computed_field` que deriva (minx,miny,maxx,maxy) do WKT via shapely (para Bloco 3 alimentar Sentinel Hub/GEE). Loaders fail-fast; `load(config_dir, region)` resolve a árvore toda e seleciona a tabela ε_max por `pipeline.epsilon_max`.
- Ficheiros `config/`: `pipeline.yml`, `epsilon_max/{xu2023,relatorio}.yml`, `fpar_percentiles.yml`, `wsc_percentiles.yml`, `t_opt_by_biome.yml`, `regions/oeiras.yml`.
- `types-PyYAML` adicionado às dev deps (mypy strict).
- 55 testes (14 novos de config, incl. end-to-end que carrega os YAML reais e alimenta `emax`); ruff + mypy strict limpos.

**Placeholders explícitos (TODO, calibrar com dados reais em bloco posterior)**:
- `fpar_percentiles.yml`: NDVI 0.05/0.95 genérico (falta percentis 5/95 por classe sobre amostra histórica).
- `wsc_percentiles.yml`: SIMI 0/1 (falta percentis 2/98).
- `t_opt_by_biome.yml`: valores aproximados (falta climatologia por bioma).
- `regions/oeiras.yml`: WKT quadrado placeholder + população a confirmar (geometria real fica para a migração de binários).

**Retomar por aqui**:
1. **Bloco 3 — camada de I/O + orquestrador windowed**: `grid.py` (grade-alvo comum S2 10 m), leitura `rasterio` por janela, `pipeline.py` que itera janelas, chama o núcleo do Bloco 1 com os parâmetros do `config.load(...)`, e **acumula** somas parciais (× área via `npp.density_to_tonnes`). `reports.py` para o JSON de totais.
2. Migrar dados binários (Oeiras WKT real, `data/sol/ghi_base.tif`, ESA WorldCover fallback) — ainda adiado.

### 2026-05-29 — Bloco 1 (núcleo matemático puro) concluído

**Feito**:
- Ambiente destravado: `uv` instalado (0.11.17), `uv sync --extra dev` OK, smoke test 3/3.
- `git init` + commit `76eeb8d` (Bloco 0); branch renomeado `master` → `main`; identidade git **local** ao repo (Diogo Fonseca / fonsecacdiogo@gmail.com).
- 8 módulos puros em `src/casa/`: `ndvi`, `landcover` (ADR-011 adapters DW/ESA), `fpar` (Xu 2023, percentis por classe injetados), `wsc` (Wu 2022, percentis injetados), `tstress` (T_opt climatológico como argumento), `sol`, `emax` (tabela canónico→ε_max injetada), `npp`.
- **Fronteira validada com utilizador**: módulos puros são array→array sem `window` (windowing é I/O, fica no `pipeline.py` — desvia do ADR-012 só para os módulos puros). `npp.density_to_tonnes` faz × área_pixel ao nível do array (corrige o `/1e6` sem área do legacy); pipeline só acumula somas entre janelas.
- 41 testes unitários (fixtures sintéticas) + smoke; ruff e mypy strict limpos.

**Ponto onde parámos / retomar por aqui**:
1. **Remoto GitHub pendente**: `gh` não instalado. Falta instalar/autenticar `gh` (ou dar URL de repo vazio) → `git remote add origin … && git push -u origin main`.
2. **Bloco 2** — config layer: `config.py` (YAML→Pydantic), ficheiros `config/regions/{oeiras,…}.yml`, `config/epsilon_max/{xu2023,relatorio}.yml`, `config/fpar_percentiles.yml`, `config/wsc_percentiles.yml`, `config/t_opt_by_biome.yml`. Wiring dos parâmetros que os módulos puros recebem hoje como argumentos.
3. Migrar dados binários (Oeiras WKT, `data/sol/ghi_base.tif`, ESA WorldCover fallback) — adiado do Bloco 0.

### 2026-05-28 — Bootstrap do refactor (Bloco 0), pausa para retomar amanhã

**Feito nesta sessão (2026-05-27 + 2026-05-28)**:
- Auditoria do código legacy em `../PROJETO/CODE/PFC_V3.1/` (12+ bugs identificados, documentados em "Padrões a Evitar" e "Regras Aprendidas").
- Leitura do Relatório Final-P33 (52 páginas) + 4 PDFs científicos + WebFetch GMD 2022 e MOD17 BPLUT.
- Decisões científicas e arquitecturais registadas como 16 ADRs em `docs/decisoes-arquitetura.md`.
- `docs/` criado e validado: `casa-model.md`, `literatura.md`, `decisoes-arquitetura.md`, `pipeline.md`.
- Bloco 0 (bootstrap repo `urban-carbon-sink/`) concluído: 26 ficheiros — `pyproject.toml` (uv + Typer + rasterio + GEE), `LICENSE` MIT, `README.md`, `.gitignore`, `src/casa/` skeleton com CLI Typer, `tests/unit/test_smoke.py`, `.github/workflows/ci.yml`, todos os docs migrados.

**Ponto exacto onde parámos**:
- Tudo escrito mas **`git init` ainda não foi feito** — utilizador queria validar `uv sync` + smoke test localmente antes do primeiro commit.
- Decisão tomada de migrar dados binários (Oeiras WKT, GHI.tif, ESA WorldCover fallback) só no **Bloco 2** (não agora).

**Retomar amanhã, por esta ordem**:
1. Utilizador corre `uv sync` em `urban-carbon-sink/`; se faltar `uv`, instalar via `pip install uv` ou `winget install astral-sh.uv`.
2. Utilizador corre `uv run pytest tests/unit/test_smoke.py` — 3 testes devem passar (import, `--help`, `version`).
3. Se passa: `git init`, primeiro commit; criar remoto GitHub (vazio, sem README inicial); `git remote add origin … && git push -u`.
4. Avançar para **Bloco 1** (núcleo matemático puro): implementar `ndvi.py`, `landcover.py` (com adaptadores defensivos), `fpar.py` (percentis 5/95 por classe canónica), `wsc.py` (percentis 2/98), `tstress.py` (T_opt climatológico, não `mean(LST cena)`), `sol.py`, `emax.py`, `npp.py`. Cada um vectorizado, com `window` parameter, e teste unitário com fixture sintética.

**Dependências externas pendentes**:
- Criar conta Google Cloud Platform.
- Submeter pedido de acesso Earth Engine non-commercial (research/portfolio). Tempo de aprovação: dias a semanas.
- Enquanto não há GEE, pipeline corre em modo `--use-fallback-mask` com ESA WorldCover 2021 estático (Bloco 6 troca o stub pela chamada real).

## Instruções de Comportamento

- **Plano antes de implementação**: para qualquer alteração não-trivial, apresentar plano e esperar aprovação. Reforça a secção "Ação Requerida e Planeamento Conjunto".
- Se algo correr mal a meio da execução, voltar ao modo de planeamento antes de continuar.
- Após cada erro corrigido, atualizar "Regras Aprendidas".
- Após cada PR, atualizar "Notas por Sessão / PR".
- Preferir soluções simples. Se a primeira solução for mediana, dizer.
- Questionar mudanças que pareçam arriscadas antes de as implementar — especialmente as que mexem na lógica matemática do CASA.
