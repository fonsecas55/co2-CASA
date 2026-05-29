"""Aggregate run totals + metadata into the structured JSON the Vercel frontend reads."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from casa.config import AppConfig
from casa.pipeline import RegionResult


class Totals(BaseModel):
    npp_c_t: float  # tonnes of carbon / month
    npp_co2_t: float  # tonnes of CO2 absorbed / month


class CarbonBalance(BaseModel):
    population: int
    emissions_per_capita_t_co2_month: float
    total_emissions_t_co2: float
    co2_absorbed_t: float
    net_co2_balance_t: float  # emissions - absorbed; > 0 means net emitter
    offset_fraction: float  # absorbed / emissions, clamped at 0 if no emissions


class Provenance(BaseModel):
    model: str
    epsilon_max_table: str
    landcover_source: str
    generated_at: str


class RegionReport(BaseModel):
    region: str
    month: str
    crs: str
    bbox_lonlat: tuple[float, float, float, float] | None
    resolution_m: float
    width: int
    height: int
    valid_pixels: int
    vegetation_pixels: int
    vegetation_area_ha: float
    totals: Totals
    balance: CarbonBalance
    provenance: Provenance
    output_cog: str


def build_report(
    result: RegionResult,
    cfg: AppConfig,
    generated_at: str | None = None,
) -> RegionReport:
    """Assemble the JSON-serialisable report from a pipeline result and its config."""
    pixel_area = result.resolution * result.resolution
    veg_area_ha = result.vegetation_pixels * pixel_area / 1e4

    population = cfg.region.population
    per_capita = cfg.region.emissions_per_capita
    total_emissions = population * per_capita
    absorbed = result.total_npp_co2_t
    offset = absorbed / total_emissions if total_emissions > 0 else 0.0

    return RegionReport(
        region=result.region,
        month=result.month,
        crs=result.crs,
        bbox_lonlat=cfg.region.bbox,
        resolution_m=result.resolution,
        width=result.width,
        height=result.height,
        valid_pixels=result.valid_pixels,
        vegetation_pixels=result.vegetation_pixels,
        vegetation_area_ha=veg_area_ha,
        totals=Totals(npp_c_t=result.total_npp_c_t, npp_co2_t=absorbed),
        balance=CarbonBalance(
            population=population,
            emissions_per_capita_t_co2_month=per_capita,
            total_emissions_t_co2=total_emissions,
            co2_absorbed_t=absorbed,
            net_co2_balance_t=total_emissions - absorbed,
            offset_fraction=offset,
        ),
        provenance=Provenance(
            model="CASA",
            epsilon_max_table=cfg.pipeline.epsilon_max,
            landcover_source=cfg.pipeline.landcover_source,
            generated_at=generated_at or datetime.now(UTC).isoformat(),
        ),
        output_cog=Path(result.output_path).name,
    )


def write_report(report: RegionReport, path: Path) -> None:
    """Write the report as pretty-printed JSON."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report.model_dump(), fh, indent=2)
        fh.write("\n")
