"""
Evalúa el LSTM entrenado con Coffee_Price_Weather.csv
Necesita:
  • models/scaler_univ.pkl
  • models/lstm_univ.h5
  • Coffee_Price_Weather.csv
"""
import numpy as np, pandas as pd, joblib, tensorflow as tf

DATA   = "Coffee_Price_Weather.csv"
SCALER = "models/scaler_univ.pkl"
MODEL  = "models/lstm_univ.h5"
WINDOW = 60
THRESH = 0.005
TEST_W = 52          # un año

df = (pd.read_csv(DATA, parse_dates=["Date"])
        .rename(columns={"Date": "date"})
        .set_index("date")
        .ffill()
        .resample("W-MON").mean()
        .dropna())

scaler = joblib.load(SCALER)
scaled = scaler.transform(df.values)

model = tf.keras.models.load_model(MODEL, compile=False)

preds, acts, signals, hits = [], [], 0, 0
for i in range(len(df) - TEST_W, len(df)):
    x = scaled[i-WINDOW:i].reshape((1, WINDOW, scaled.shape[1]))
    y_scaled = model.predict(x, verbose=0)[0][0]
    y_pred = scaler.inverse_transform([[y_scaled]+[0]*(scaled.shape[1]-1)])[0][0]

    price_now = df.iloc[i, 0]                 # primera columna = precio café
    if y_pred < price_now*(1-THRESH):
        signals += 1
        if i < len(df)-1 and df.iloc[i+1,0] < price_now*(1-THRESH):
            hits += 1

    preds.append(y_pred); acts.append(price_now)

mae  = np.mean(np.abs(np.array(acts) - np.array(preds)))
mape = np.mean(np.abs((np.array(acts) - np.array(preds))/np.array(acts)))*100
prec = hits/signals*100 if signals else 0

print("\nLSTM Universidad – últimas 52 semanas")
print(f"MAE  : {mae:.2f} USD/lb")
print(f"MAPE : {mape:.2f} %")
print(f"Señales VENDER: {signals}")
print(f"Aciertos      : {hits}")
print(f"Precisión     : {prec:.1f} %")
