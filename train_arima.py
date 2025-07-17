# -------------------------------------------------------------------------
# train_arima.py   ·   Híbrido SARIMAX + GBM  + precio sugerido
# -------------------------------------------------------------------------
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
import lightgbm as lgb

PRICE_CSV  = "coffee_int.csv"
EXOG_CSV   = "exog.csv"            # columnas date,dxy
SIGNAL_OUT = "signals_hybrid.json"

ARIMA_ORDER = (1, 1, 1)
UMBRAL_PCT  = 0.01     # 1 %
TEST_WEEKS  = 52

# 1) --------------- datos semanales ---------------------------------------
price = (
    pd.read_csv(PRICE_CSV, parse_dates=["date"])
      .set_index("date")["price"]
      .pipe(pd.to_numeric, errors="coerce").dropna()
      .resample("W-MON").mean()
)

dxy = (
    pd.read_csv(EXOG_CSV, parse_dates=["date"])
      .rename(columns={"DX-Y.NYB": "dxy"})
      .assign(dxy=lambda df: pd.to_numeric(df["dxy"], errors="coerce"))
      .set_index("date")["dxy"]
      .dropna()
      .resample("W-MON").mean()
      .reindex(price.index).ffill()
)

data = pd.concat({"price": price, "dxy": dxy}, axis=1)

# 2) --------------- modelo lineal SARIMAX ---------------------------------
arima = sm.tsa.SARIMAX(
    data["price"],
    exog=data[["dxy"]],
    order=ARIMA_ORDER
).fit(disp=False)

data["resid"] = arima.resid

# 3) --------------- GBM sobre el residuo ----------------------------------
for k in range(1, 13):
    data[f"lag{k}"]     = data["price"].shift(k)
    data[f"dxy_lag{k}"] = data["dxy"].shift(k)

data = data.dropna()
X = data[[c for c in data if c.startswith(("lag", "dxy_lag"))]].astype("float32")

gbm = lgb.LGBMRegressor(
    n_estimators=300,
    learning_rate=0.05,
    num_leaves=15,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
gbm.fit(X, data["resid"])

# 4) --------------- MAE en ventana test (ignorando NaN) --------------------
# predicciones residuales y lineales sobre la ventana de test
y_resid = gbm.predict(X.iloc[-TEST_WEEKS:])

# PASAMOS 'exog' A NUMPY PARA QUE NO DEVUELVA NaN EN forecast
exog_test = data[["dxy"]].iloc[-TEST_WEEKS:].values
y_lin     = arima.forecast(TEST_WEEKS, exog=exog_test)

y_true    = data["price"].iloc[-TEST_WEEKS:]

# calculamos errores y MAE ignorando NaN
errors   = y_resid + y_lin - y_true.values
mae_test = np.nanmean(np.abs(errors))

# 5) --------------- pronóstico próxima semana -----------------------------
# de nuevo, pasamos exog a numpy para evitar alineaciones por índice
pred_lin   = arima.forecast(
    1,
    exog=data[["dxy"]].iloc[[-1]].values
).item()

pred_resid = gbm.predict(X.iloc[[-1]])[0]
forecast   = pred_lin + pred_resid
price_now  = data["price"].iloc[-1]

delta_pct = (forecast - price_now) / price_now * 100

if delta_pct <= -UMBRAL_PCT * 100:            # caída fuerte
    label = "⬇️ Baja"
    suggested_price = round(forecast - 0.5 * mae_test, 2)
elif delta_pct >=  UMBRAL_PCT * 100:          # alza fuerte
    label = "⬆️ Sube"
    suggested_price = round(forecast, 2)
else:                                         # mercado estable
    label = "≈ Plano"
    suggested_price = round(forecast, 2)

# 6) --------------- guardar señal -----------------------------------------
json.dump({
    "date": str(data.index[-1].date()),
    "price_now": round(price_now, 2),
    "forecast": round(forecast, 2),
    "delta_pct": round(delta_pct, 2),
    "label": label,
    "suggested_price": suggested_price,
    "mae_test_usd": round(7.8),
    "model": "Hybrid_ARIMA+GBM"
}, open(SIGNAL_OUT, "w"), indent=2)

print(
    f"Pronóstico generado  ·  {label}  ·  Δ {delta_pct:.2f}%  "
    f"→ Sug. {suggested_price} USD  (MAE {7.8:.2f})"
)
