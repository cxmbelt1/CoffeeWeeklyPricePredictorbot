# forecast_plot.py  –  Coffee C: precio real vs pronóstico híbrido
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import statsmodels.api as sm, lightgbm as lgb

PRICE_CSV = "coffee_int.csv"    # date,price
EXOG_CSV  = "exog.csv"          # date,dxy
ORDER     = (1, 1, 1)
TEST_WEEKS = 52                 # 1 año

# 1) Serie semanal
price = (pd.read_csv(PRICE_CSV, parse_dates=["date"])
           .set_index("date")["price"]
           .pipe(pd.to_numeric, errors="coerce")
           .dropna()
           .resample("W-MON").mean())

dxy = (pd.read_csv(EXOG_CSV, parse_dates=["date"])
         .rename(columns={"DX-Y.NYB": "dxy"})
         .assign(dxy=lambda d: pd.to_numeric(d["dxy"], errors="coerce"))
         .set_index("date")["dxy"]
         .dropna()
         .resample("W-MON").mean()
         .reindex(price.index).ffill())

df = pd.concat({"price": price, "dxy": dxy}, axis=1)

# 2) Modelo híbrido (ARIMA + GBM) entrenado
train = df.iloc[:-TEST_WEEKS].copy()
arima = sm.tsa.SARIMAX(train["price"], exog=train[["dxy"]],
                       order=ORDER).fit(disp=False)
train["resid"] = arima.resid

for k in range(1, 13):
    train[f"lag{k}"] = train["price"].shift(k)
    train[f"dxy_lag{k}"] = train["dxy"].shift(k)
train = train.dropna()

X_tr = train[[c for c in train if c.startswith(("lag", "dxy_lag"))]]
y_tr = train["resid"]
gbm = lgb.LGBMRegressor(
        n_estimators=300, learning_rate=0.05,
        num_leaves=15, subsample=0.8, colsample_bytree=0.8,
        random_state=42).fit(X_tr, y_tr)

# 3) Rolling forecast (52 semanas)
hist_y = price.iloc[:-TEST_WEEKS].tolist()
hist_x = dxy.iloc[:-TEST_WEEKS].tolist()
dates  = df.index[-TEST_WEEKS:]
preds  = []

for i in range(TEST_WEEKS):
    d_now = dxy.iloc[-TEST_WEEKS + i]
    model = sm.tsa.SARIMAX(hist_y, exog=hist_x,
                           order=ORDER).fit(disp=False)
    pred = model.forecast(1, exog=[d_now])[0]

    feats = {**{f"lag{k}": hist_y[-k] for k in range(1, 13)},
             **{f"dxy_lag{k}": hist_x[-k] for k in range(1, 13)}}
    pred += gbm.predict(pd.DataFrame([feats]))[0]

    preds.append(pred)
    # update history
    hist_y.append(price.iloc[-TEST_WEEKS + i])
    hist_x.append(d_now)

# 4) Plot
plt.figure(figsize=(9, 4))
plt.plot(dates, price.iloc[-TEST_WEEKS:], label="Precio real")
plt.plot(dates, preds, label="Pronóstico híbrido")
plt.title("Coffee  – Precio real vs pronóstico ")
plt.xlabel("Fecha"); plt.ylabel("USD/lb"); plt.legend()
plt.tight_layout()
plt.savefig("forecast_vs_real.png", dpi=300)
plt.show()
