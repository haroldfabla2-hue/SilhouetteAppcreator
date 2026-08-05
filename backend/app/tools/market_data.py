"""Datos de mercado reales.

Sustituye a `legacy/code/silhouettemcp_expanded_finance.py`, que inventaba las
cotizaciones:

    "current_price": round(random.uniform(10, 500), 2),
    "change_percent": round(random.uniform(-5, 5), 2),
    "volume": random.randint(100000, 10000000),

Un precio inventado es la clase de dato más peligrosa que puede devolver un
sistema: parece correcto, nadie lo verifica, y alguien podría decidir sobre él.

Aquí se usa `yfinance`, que consulta Yahoo Finance. Sin clave y sin coste, pero
con dos advertencias que se declaran en cada respuesta:

- Los datos llegan **con retardo** (típicamente 15 minutos); no sirven para
  operar en tiempo real.
- Es una fuente no oficial. Para uso profesional hace falta un proveedor con
  acuerdo de licencia.

Si `yfinance` no está instalado, el módulo lo dice. No hay modo de respaldo con
números plausibles: eso es exactamente lo que se retiró.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("MarketData")

try:
    import yfinance as yf

    YFINANCE_AVAILABLE = True
except ImportError:  # pragma: no cover - depende del entorno
    YFINANCE_AVAILABLE = False
    yf = None
    logger.info(
        "yfinance no está instalado; los datos de mercado quedan desactivados. "
        "Instale con: pip install -e '.[market]'"
    )

DISCLAIMER = (
    "Datos de Yahoo Finance con retardo (~15 min), fuente no oficial. "
    "No aptos para operar en tiempo real ni para uso profesional sin licencia."
)

MAX_SYMBOLS = 25


class MarketDataUnavailable(RuntimeError):
    """No se pudieron obtener datos reales. Nunca se sustituyen por estimaciones."""


@dataclass
class Quote:
    """Cotización real de un valor."""

    symbol: str
    name: str
    price: float
    currency: str
    previous_close: float | None
    change: float | None
    change_percent: float | None
    volume: int | None
    market_cap: int | None
    exchange: str
    retrieved_at: str
    delayed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "disclaimer": DISCLAIMER}


def _require() -> None:
    if not YFINANCE_AVAILABLE:
        raise MarketDataUnavailable(
            "yfinance no está instalado, así que no hay datos de mercado reales. "
            "Instale con: pip install yfinance"
        )


def _as_float(valor: Any) -> float | None:
    try:
        if valor is None:
            return None
        f = float(valor)
        return f if f == f else None  # descarta NaN
    except (TypeError, ValueError):
        return None


def _as_int(valor: Any) -> int | None:
    f = _as_float(valor)
    return int(f) if f is not None else None


def _build_quote(symbol: str, info: dict[str, Any]) -> Quote:
    precio = _as_float(
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("previousClose")
    )
    if precio is None:
        raise MarketDataUnavailable(
            f"Yahoo Finance no devolvió precio para '{symbol}'. "
            "¿Es un símbolo válido y cotiza actualmente?"
        )

    anterior = _as_float(info.get("previousClose") or info.get("regularMarketPreviousClose"))
    cambio = round(precio - anterior, 4) if anterior is not None else None
    pct = round((cambio / anterior) * 100, 4) if (cambio is not None and anterior) else None

    return Quote(
        symbol=symbol.upper(),
        name=str(info.get("longName") or info.get("shortName") or symbol.upper()),
        price=round(precio, 4),
        currency=str(info.get("currency") or ""),
        previous_close=anterior,
        change=cambio,
        change_percent=pct,
        volume=_as_int(info.get("volume") or info.get("regularMarketVolume")),
        market_cap=_as_int(info.get("marketCap")),
        exchange=str(info.get("exchange") or info.get("fullExchangeName") or ""),
        retrieved_at=datetime.now(timezone.utc).isoformat(),
    )


async def get_quote(symbol: str) -> Quote:
    """Cotización real de un símbolo."""
    _require()
    simbolo = (symbol or "").strip().upper()
    if not simbolo:
        raise ValueError("Debe indicar un símbolo.")

    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(None, lambda: dict(yf.Ticker(simbolo).info or {}))
    except Exception as exc:  # noqa: BLE001 - yfinance lanza excepciones variadas
        raise MarketDataUnavailable(
            f"No se pudo consultar '{simbolo}': {exc}"
        ) from None

    if not info:
        raise MarketDataUnavailable(
            f"Yahoo Finance no devolvió datos para '{simbolo}'. Compruebe el símbolo."
        )

    cotizacion = _build_quote(simbolo, info)
    logger.info("[Mercado] %s = %s %s", cotizacion.symbol, cotizacion.price, cotizacion.currency)
    return cotizacion


async def get_quotes(symbols: list[str]) -> dict[str, Any]:
    """Varias cotizaciones a la vez.

    Los símbolos que fallen se listan aparte con su motivo, en lugar de
    omitirse en silencio o rellenarse.
    """
    _require()
    limpios = [s.strip().upper() for s in symbols if s and s.strip()][:MAX_SYMBOLS]
    if not limpios:
        raise ValueError("No se indicó ningún símbolo válido.")

    resultados = await asyncio.gather(
        *(get_quote(s) for s in limpios), return_exceptions=True
    )

    cotizaciones: list[dict[str, Any]] = []
    fallos: dict[str, str] = {}
    for simbolo, resultado in zip(limpios, resultados, strict=True):
        if isinstance(resultado, BaseException):
            fallos[simbolo] = str(resultado)
        else:
            cotizaciones.append(resultado.to_dict())

    return {
        "quotes": cotizaciones,
        "failed": fallos,
        "requested": len(limpios),
        "retrieved": len(cotizaciones),
        "disclaimer": DISCLAIMER,
    }


async def get_history(
    symbol: str, *, period: str = "1mo", interval: str = "1d"
) -> dict[str, Any]:
    """Serie histórica real de precios.

    `period`: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    `interval`: 1m, 5m, 15m, 1h, 1d, 1wk, 1mo
    """
    _require()
    simbolo = (symbol or "").strip().upper()
    if not simbolo:
        raise ValueError("Debe indicar un símbolo.")

    loop = asyncio.get_running_loop()
    try:
        marco = await loop.run_in_executor(
            None, lambda: yf.Ticker(simbolo).history(period=period, interval=interval)
        )
    except Exception as exc:  # noqa: BLE001
        raise MarketDataUnavailable(f"No se pudo obtener el histórico de '{simbolo}': {exc}") from None

    if marco is None or marco.empty:
        raise MarketDataUnavailable(
            f"Sin datos históricos para '{simbolo}' (periodo={period}, intervalo={interval}). "
            "Compruebe el símbolo y que la combinación sea admitida."
        )

    puntos = [
        {
            "date": indice.isoformat(),
            "open": _as_float(fila.get("Open")),
            "high": _as_float(fila.get("High")),
            "low": _as_float(fila.get("Low")),
            "close": _as_float(fila.get("Close")),
            "volume": _as_int(fila.get("Volume")),
        }
        for indice, fila in marco.iterrows()
    ]

    return {
        "symbol": simbolo,
        "period": period,
        "interval": interval,
        "points": puntos,
        "count": len(puntos),
        "disclaimer": DISCLAIMER,
    }


def is_available() -> bool:
    return YFINANCE_AVAILABLE
