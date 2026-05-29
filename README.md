# Urban Carbon Sink

Quantifies monthly CO₂ absorption by urban vegetation using the **CASA model** applied to Sentinel-2 / Sentinel-3 imagery and Google Earth Engine Dynamic World, with results served as Cloud-Optimized GeoTIFFs (COG) and JSON via GitHub Releases.

Status: **under construction** (refactor of a prior academic prototype). See [`docs/`](docs/) for architecture decisions and scientific basis.

## What it does

1. Pulls Sentinel-2/-3 imagery for the previous month for each configured region (Oeiras, Lisboa, Flores, …).
2. Computes the CASA terms — FPAR, WSC, Tε₁/Tε₂, SOL, ε_max — over a common Sentinel-2 grid (10 m).
3. Multiplies them into a Net Primary Productivity raster (g C / m² / month), converts to CO₂.
4. Aggregates per region, compares against per-capita emissions budget.
5. Publishes COG + JSON as GitHub Release assets; frontend reads directly from public URLs.

The pipeline runs autonomously as a **GitHub Actions Cron** on the 1st of each month.

## Quickstart

```sh
uv sync
uv run casa --help
```

## Documentation

- [`docs/casa-model.md`](docs/casa-model.md) — mathematical derivation, units, formulas
- [`docs/literatura.md`](docs/literatura.md) — annotated bibliography
- [`docs/decisoes-arquitetura.md`](docs/decisoes-arquitetura.md) — Architecture Decision Records
- [`docs/pipeline.md`](docs/pipeline.md) — operational pipeline spec

## License

MIT — see [`LICENSE`](LICENSE).
