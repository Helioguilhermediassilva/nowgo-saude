"""Static reference data for the Distrito Federal Regiões Administrativas.

The Federal District has a single 7-digit IBGE municipality code (``5300108``)
so RA-level disaggregation is carried in ``TelemetryEvent.attributes.ra_id``
(plus ``ra_name`` for display). This module is the canonical mapping used by
the dashboard service layer and the demo seed.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegionAdmin:
    ra_id: str
    name: str
    population: int  # 2020 SEPLAN-DF estimate, kept simple for the MVP


DF_REGIONS: tuple[RegionAdmin, ...] = (
    RegionAdmin("RA-I", "Plano Piloto", 230_000),
    RegionAdmin("RA-II", "Gama", 145_000),
    RegionAdmin("RA-III", "Taguatinga", 220_000),
    RegionAdmin("RA-IV", "Brazlândia", 56_000),
    RegionAdmin("RA-V", "Sobradinho", 65_000),
    RegionAdmin("RA-VI", "Planaltina", 190_000),
    RegionAdmin("RA-VIII", "Núcleo Bandeirante", 27_000),
    RegionAdmin("RA-IX", "Ceilândia", 430_000),
    RegionAdmin("RA-X", "Guará", 145_000),
    RegionAdmin("RA-XII", "Samambaia", 260_000),
    RegionAdmin("RA-XIII", "Santa Maria", 130_000),
    RegionAdmin("RA-XV", "Recanto das Emas", 145_000),
    RegionAdmin("RA-XVI", "Lago Sul", 30_000),
    RegionAdmin("RA-XVII", "Riacho Fundo", 41_000),
    RegionAdmin("RA-XX", "Águas Claras", 161_000),
    RegionAdmin("RA-XXIX", "Sol Nascente / Pôr do Sol", 95_000),
)

REGION_BY_ID: dict[str, RegionAdmin] = {ra.ra_id: ra for ra in DF_REGIONS}

DF_TOTAL_POPULATION = sum(ra.population for ra in DF_REGIONS)


def region_name(ra_id: str) -> str:
    ra = REGION_BY_ID.get(ra_id)
    return ra.name if ra else ra_id
