# CoffeeWeeklyPricePredictorBot ☕🤖

Un bot de Telegram que utiliza machine learning para predecir el precio semanal del café y enviar notificaciones con las estimaciones.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)

---

## 📋 Descripción del Proyecto

Este proyecto consiste en un bot automatizado que analiza datos históricos del precio del café, entrena un modelo de Machine Learning para predecir la variación de precios para la siguiente semana y notifica a los usuarios a través de un bot de Telegram.

El objetivo principal es proporcionar una herramienta sencilla y accesible para obtener estimaciones sobre la tendencia del precio del café. Para ello, se implementa un **modelo híbrido** que combina **SARIMA** para capturar la estacionalidad de la serie temporal y **LightGBM** para mejorar la precisión de la predicción.

***

## ✨ Características Principales

* **Análisis de Series Temporales:** Utiliza datos históricos para identificar patrones y tendencias en el precio del café.
* **Modelo Predictivo Avanzado:** Implementa un modelo híbrido **SARIMA + LightGBM**. SARIMA modela las tendencias y estacionalidades, mientras que LightGBM corrige los errores residuales, resultando en un pronóstico más robusto.
* **Bot de Telegram Interactivo:** Permite a los usuarios solicitar la predicción más reciente a través de comandos simples.
* **Notificaciones Semanales:** Envía automáticamente la nueva predicción cada semana a los usuarios suscritos o a un canal específico.

***

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.9+
* **Análisis de Datos:** Pandas, NumPy
* **Machine Learning:** Statsmodels (para SARIMA), LightGBM, Scikit-learn
* **Bot de Telegram:** `python-telegram-bot`

***

## 🏃‍♂️ Cómo Usarlo

Una vez que el bot está en funcionamiento, puedes interactuar con él directamente en Telegram.

1.  Busca tu bot en Telegram por su nombre de usuario.
2.  Inicia una conversación y utiliza los siguientes comandos:
    * `/start` - Muestra un mensaje de bienvenida e información básica.
    * `/prediccion` - Devuelve la predicción de precio más reciente junto con un análisis breve.
    * `/info` - Proporciona detalles sobre el proyecto y el modelo utilizado.

***

## 📂 Estructura del Proyecto

```text

CoffeeWeeklyPricePredictorbot/
├── backtest/              # Contiene diferentes pruebas de los modelos y modelos desechados al tener peor rendimiento que el seleccionado
├── data/             # Almacena los datasets históricos de las diferentes variables
├── scrapping/             # Son los scripts que permiten obtener los datasets de interes
├── signals_hybrid.json  # Contiene la estructura del mensaje que envia el bot a telegram
├── bot.py     # Lógica del bot de Telegram
├── train_arima.py     # Es la logica con la cual se entreno el modelo final (SARIMA + LightGBM)
└── README.md         # Éste archivo
