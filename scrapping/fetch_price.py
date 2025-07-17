# fetch_price_int.py  – versión corregida y con histórico completo
import datetime as dt, os, pandas as pd, yfinance as yf

TICKER = "KC=F"
CSV_PATH = "coffee_int.csv"

def bootstrap():
    hist = yf.download(TICKER, start="2010-01-01", interval="1d", progress=False)[["Close"]]
    hist = (hist.dropna()
                .reset_index()
                .rename(columns={"Date": "date", "Close": "price"}))
    hist["ticker"] = TICKER
    hist.to_csv(CSV_PATH, index=False)
    print(f"▶  Histórico guardado: {len(hist)} filas")

def append_today():
    today = dt.date.today()
    df = yf.download(TICKER, start=today, end=today+dt.timedelta(days=1),
                     interval="1d", progress=False)[["Close"]]
    if df.empty:
        print("• Aún no hay precio para hoy; nada que agregar.")
        return
    precio = round(df["Close"].iloc[0], 4)   # ← valor escalar
    nuevo  = pd.DataFrame({"date":[today], "price":[precio], "ticker":[TICKER]})

    viejo = pd.read_csv(CSV_PATH, parse_dates=["date"])
    out   = pd.concat([viejo, nuevo]).drop_duplicates("date").sort_values("date")
    out.to_csv(CSV_PATH, index=False)
    print(f"✔  Añadido {today}  →  {precio} USD/lb")

if __name__ == "__main__":
    if not os.path.exists(CSV_PATH):
        bootstrap()
    else:
        append_today()
