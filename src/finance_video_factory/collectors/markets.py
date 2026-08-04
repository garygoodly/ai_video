from __future__ import annotations
from datetime import datetime, timezone
import yfinance as yf
from finance_video_factory.models import MarketSnapshot

class MarketCollector:
    def collect(self, symbols: list[str]) -> list[MarketSnapshot]:
        result=[]
        for symbol in symbols:
            try:
                hist=yf.Ticker(symbol).history(period="5d", interval="1d", auto_adjust=False)
                closes=hist["Close"].dropna()
                last=float(closes.iloc[-1]) if len(closes) else None
                change=float((closes.iloc[-1]/closes.iloc[-2]-1)*100) if len(closes)>1 else None
                result.append(MarketSnapshot(symbol=symbol,last=last,change_pct=change,as_of=datetime.now(timezone.utc).isoformat()))
            except Exception:
                result.append(MarketSnapshot(symbol=symbol,as_of=datetime.now(timezone.utc).isoformat()))
        return result
