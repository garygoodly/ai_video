from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
import yfinance as yf

class ChartService:
    def create(self, symbol: str, title: str, output: Path) -> Path:
        data=yf.download(symbol,period="6mo",interval="1d",progress=False,auto_adjust=True)
        output.parent.mkdir(parents=True,exist_ok=True)
        fig=plt.figure(figsize=(16,9))
        ax=fig.add_subplot(111)
        if data.empty:
            ax.text(.5,.5,f"No chart data for {symbol}",ha="center",va="center",fontsize=28)
        else:
            series=data["Close"]
            if getattr(series,"ndim",1)>1:
                series=series.iloc[:,0]
            ax.plot(series.index,series.values,linewidth=3)
            ax.set_title(title,fontsize=30,pad=20)
            ax.grid(alpha=.25)
        ax.set_xlabel("")
        fig.tight_layout()
        fig.savefig(output,dpi=120)
        plt.close(fig)
        return output
