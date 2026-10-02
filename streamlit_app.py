import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="GUZIMO Cañón v10", layout="wide")
st.title("🍐 GUZIMO - Scalper Chiquito v10 - TimesFM 200M")

@st.cache_resource
def load_timesfm():
    import timesfm
    # Usamos el de 200M que si cabe en Streamlit Cloud
    model = timesfm.TimesFm(
        hparams=timesfm.TimesFmHparams(
            backend="gpu" if False else "cpu",
            per_core_batch_size=32,
            horizon_len=10,
            input_patch_len=32,
            context_len=128,
            num_layers=20,
            model_dims=1280,
            use_positional_embedding=False,
        ),
        checkpoint=timesfm.TimesFmCheckpoint(
            huggingface_repo_id="google/timesfm-1.0-200m-pytorch",
        ),
    )
    return model

st.sidebar.header("Config Alpaca")
API_KEY = st.sidebar.text_input("API KEY", type="password")
SECRET_KEY = st.sidebar.text_input("SECRET KEY", type="password")
SYMBOL = st.sidebar.selectbox("Símbolo", ["AAPL", "TSLA", "NVDA", "SPY", "MSFT"])

if st.sidebar.button("Cargar Cañón 🔫"):
    with st.spinner("Cargando TimesFM... 1 min"):
        try:
            model = load_timesfm()
            st.session_state['model'] = model
            st.sidebar.success("¡Cañón cargado!")
        except Exception as e:
            st.sidebar.error(f"Error cargando: {e}")

if st.button("Predecir Ahora"):
    if not API_KEY or not SECRET_KEY:
        st.warning("Pon tus keys de Alpaca a la izquierda, Pera")
    else:
        try:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame
            from datetime import datetime, timedelta

            client = StockHistoricalDataClient(API_KEY, SECRET_KEY)
            request = StockBarsRequest(
                symbol_or_symbols=[SYMBOL],
                timeframe=TimeFrame.Minute,
                start=datetime.now() - timedelta(days=2)
            )
            bars = client.get_stock_bars(request).df
            df = bars.xs(SYMBOL).tail(200)

            st.subheader(f"Precio {SYMBOL}")
            st.line_chart(df['close'])

            context = df['close'].values[-128:].astype(np.float32)

            if 'model' in st.session_state:
                model = st.session_state['model']
                # Forecast
                point_forecast, _ = model.forecast(
                    [context],
                    freq=[0]
                )
                forecast = point_forecast[0]
                st.subheader(f"Predicción próximas 10 velas de {SYMBOL}:")
                st.metric("Último cierre", f"${context[-1]:.2f}", f"Pred: ${forecast[-1]:.2f}")

                future_df = pd.DataFrame({
                    "real": list(context[-30:]) + [None]*10,
                    "predicción TimesFM": [None]*30 + list(forecast)
                })
                st.line_chart(future_df)

                if forecast[-1] > context[-1] * 1.001:
                    st.success("🚀 SEÑAL: LONG - Compra")
                elif forecast[-1] < context[-1] * 0.999:
                    st.error("🔻 SEÑAL: SHORT - Venta")
                else:
                    st.info("⏸️ LATERAL - No entrar")
            else:
                st.warning("Primero carga el cañón a la izquierda")

        except Exception as e:
            st.error(f"Error: {e}")
            st.exception(e)

