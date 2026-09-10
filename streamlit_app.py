import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Revendedor Chiquito", layout="wide")
st.title("📈 Revendedor Chiquito - Scalper 5min")

ticker = st.text_input("Símbolo", "AAPL")

if ticker:
    data = yf.download(ticker, period="2d", interval="5m")
    st.line_chart(data['Close'])
    
    # Señal simple
    if len(data) > 20:
        sma20 = data['Close'].rolling(20).mean().iloc[-1]
        precio = data['Close'].iloc[-1]
        if precio > sma20:
            st.success(f"SEÑAL: COMPRAR - Precio {precio:.2f} > SMA20 {sma20:.2f}")
        else:
            st.error(f"SEÑAL: VENDER / ESPERAR - Precio {precio:.2f} < SMA20 {sma20:.2f}")
    
    st.dataframe(data.tail())
