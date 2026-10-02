import streamlit as st
import pandas as pd
import numpy as np
import timesfm
import torch
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

st.set_page_config(page_title="GUZIMO Cañón v10", layout="wide")
st.title("🍐 GUZIMO - Scalper Chiquito v10 - TimesFM")

# --- CONFIG ---
st.sidebar.header("Config Alpaca")
API_KEY = st.sidebar.text_input("API KEY", type="password")
SECRET_KEY = st.sidebar.text_input("SECRET KEY", type="password")
SYMBOL = st.sidebar.selectbox("Símbolo", ["AAPL", "TSLA", "NVDA", "SPY", "MSFT"])
TIMEFRAME = st.sidebar.selectbox("Temporalidad", ["1Min", "5Min", "15Min"])

# --- FUNCION TIMESFM ---
@st.cache_resource
def load_timesfm():
    # Cargamos el cañón de Google
    model = timesfm.TimesFM_2p0_500M_torch.from_pretrained("google/timesfm-2.0-500m-torch")
    return model

if st.sidebar.button("Cargar Cañón"):
    with st.spinner("Cargando TimesFM 500M... tarda 1 min la primera vez..."):
        model = load_timesfm()
        st.success("Cañón cargado! 🔫")
        st.session_state['model'] = model

# --- DATOS ---
if API_KEY and SECRET_KEY:
    if st.button("Predecir con TimesFM"):
        try:
            client = StockHistoricalDataClient(API_KEY, SECRET_KEY)
            request = StockBarsRequest(
                symbol_or_symbols=[SYMBOL],
                timeframe=TimeFrame.Minute if TIMEFRAME=="1Min" else TimeFrame.Hour,
                start=datetime.now() - timedelta(days=5)
            )
            bars = client.get_stock_bars(request).df
            df = bars.xs(SYMBOL)

            st.line_chart(df['close'].tail(100))

            # Preparar datos para TimesFM
            context = df['close'].tail(128).values.tolist()

            if 'model' in st.session_state:
                model = st.session_state['model']
                # Predicción de 10 velas futuras
                forecast, _ = model.forecast([context], horizon=10)
                st.subheader("Predicción próximas 10 velas:")
                st.write(forecast[0])
                st.line_chart(pd.DataFrame({"real": context[-30:], "pred": [None]*20 + list(forecast[0][:10])}))

                # Señal simple
                if forecast[0][-1] > context[-1]:
                    st.success("SEÑAL: COMPRA LONG 📈")
                else:
                    st.error("SEÑAL: VENTA SHORT 📉")
            else:
                st.warning("Primero carga el cañón en la barra lateral")

        except Exception as e:
            st.error(f"Error: {e}")
else:
    st.info("Pon tus keys de Alpaca a la izquierda, Pera")



