import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame

st.set_page_config(page_title="Chiquito V9 - JO2-P F1", layout="wide")
st.title("Scalper Chiquito V9 - JO2-P FASE 1 FIX 1")

try:
    API_KEY = st.secrets["ALPACA_API_KEY"]
    SECRET_KEY = st.secrets["ALPACA_SECRET_KEY"]
except:
    st.error("Ve a Streamlit Cloud > Settings > Secrets y pega tus keys")
    st.stop()

stock_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)
crypto_client = CryptoHistoricalDataClient()

symbol = st.sidebar.selectbox("Símbolo", ["BTC/USD", "ETH/USD", "AAPL", "TSLA", "SPY"])
tf_str = st.sidebar.selectbox("Timeframe", ["1Min", "5Min", "15Min"])

def get_data(sym, tf):
    end = datetime.now()
    start = end - timedelta(days=2)
    timeframe = TimeFrame.Minute
    if "/" in sym:
        req = CryptoBarsRequest(symbol_or_symbols=sym, timeframe=timeframe, start=start, end=end)
        bars = crypto_client.get_crypto_bars(req).df
        if bars.empty: return pd.DataFrame()
        df = bars.xs(sym) if sym in bars.index.get_level_values(0) else bars
    else:
        req = StockBarsRequest(symbol_or_symbols=sym, timeframe=timeframe, start=start, end=end)
        bars = stock_client.get_stock_bars(req).df
        if bars.empty: return pd.DataFrame()
        df = bars.xs(sym) if sym in bars.index.get_level_values(0) else bars
    df = df.reset_index()
    if tf == "5Min":
        df = df.set_index('timestamp').resample('5Min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().reset_index()
    elif tf == "15Min":
        df = df.set_index('timestamp').resample('15Min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().reset_index()
    return df

df = get_data(symbol, tf_str)
if df.empty:
    st.warning("Alpaca no devolvió datos.")
    st.stop()

df['EMA9'] = df['close'].ewm(span=9).mean()
df['EMA21'] = df['close'].ewm(span=21).mean()
df['VOL_AVG20'] = df['volume'].rolling(20).mean()
df['RVOL'] = df['volume'] / df['VOL_AVG20']
score = 0
if df['EMA9'].iloc[-1] > df['EMA21'].iloc[-1]: score += 35
if df['RVOL'].iloc[-1] >= 1.5: score += 35
if df['close'].iloc[-1] > df['open'].iloc[-1]: score += 15
contexto_apertura = df['close'].iloc[-1] > df['EMA21'].iloc[-1]
senal = "NEUTRAL"
if contexto_apertura and score >= 65:
    senal = "COMPRA DIRECTA - Score " + str(int(score))
elif score >= 50:
    senal = "COMPRA" if df['EMA9'].iloc[-1] > df['EMA21'].iloc[-1] else "VENTA"

st.metric(f"{symbol} {tf_str}", senal, f"Score: {score:.0f} | RVOL: {df['RVOL'].iloc[-1]:.2f}x")
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name=symbol))
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA9'], name="EMA9", line=dict(color='#FFD700')))
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA21'], name="EMA21", line=dict(color='#00BFFF')))
fig.update_layout(height=650, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)
st.dataframe(df.tail(30), use_container_width=True)
