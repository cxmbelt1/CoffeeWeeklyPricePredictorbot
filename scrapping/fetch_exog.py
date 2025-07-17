import pandas as pd, yfinance as yf

OUT = "exog.csv"

def load_yf(ticker, colname):
    s = yf.download(
        ticker,
        start="2010-01-01",
        interval="1d",
        progress=False
    )["Close"]
    s.name = colname      # ← nombre correcto de la serie
    s.index.name = "date" # ← nombre correcto del índice
    return s

dxy = load_yf("DX-Y.NYB", "dxy")

# Escribe encabezados explícitos: date,dxy
dxy.to_csv(OUT, index_label="date", header=True)
print(f"Guardadas {len(dxy)} filas en {OUT}")
