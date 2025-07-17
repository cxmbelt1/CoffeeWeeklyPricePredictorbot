import pandas as pd, numpy as np, statsmodels.api as sm

def weekly_series(csv="coffee_int.csv"):
    df = pd.read_csv(csv, parse_dates=["date"])
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    return (df.set_index("date")["price"]
              .resample("W-MON").mean().dropna())

y = weekly_series()
order = (0,1,1)
test_weeks = 52

def walk_forward(thresh):
    train = y.iloc[:-test_weeks]
    test  = y.iloc[-test_weeks:]

    h = train.tolist(); correct = total = 0
    for i, actual in enumerate(test):
        pred = sm.tsa.ARIMA(h, order=order).fit().forecast()[0]
        vender = pred < actual * (1 - thresh)
        if vender:
            total += 1
            # ¿cayó más que el umbral real la semana SIGUIENTE?
            if i < len(test)-1 and test[i+1] < actual * (1 - thresh):
                correct += 1
        h.append(actual)
    precision = correct / total * 100 if total else 0
    return total, precision

print("Umbral  Señales  Precisión (%)")
for pct in np.arange(0.005, 0.031, 0.005):
    total, prec = walk_forward(pct)
    print(f"{pct*100:4.1f}%     {total:3d}       {prec:5.1f}")
