import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Page Configuration ---
st.set_page_config(
    page_title="Pro Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar Inputs ---
st.sidebar.header("🔍 Analysis Settings")
symbol = st.sidebar.text_input("Stock Ticker", value="AAPL").upper()

period_map = {
    "1 Day": "1d", "1 Week": "5d", "1 Month": "1mo",
    "6 Months": "6mo", "1 Year": "1y", "5 Years": "5y", "Max": "max"
}
selected_period = st.sidebar.selectbox("Time Horizon", list(period_map.keys()), index=4)
chart_type = st.sidebar.radio("Chart Style", ["Candlestick", "Line Chart"])

st.sidebar.subheader("Technical Indicators")
show_sma20 = st.sidebar.checkbox("SMA 20 (Short-term)")
show_sma50 = st.sidebar.checkbox("SMA 50 (Long-term)")

# --- Fixed Data Fetching (الحل النهائي للمشكلة) ---
@st.cache_data(ttl=3600)
def load_data(ticker, period):
    # الحل هنا: تم حذف الـ session اليدوي وترك yfinance يتعامل تلقائياً
    # التحديث الجديد لـ yfinance يمنع تمرير session من مكتبة requests
    try:
        data = yf.download(ticker, period=period, progress=False, multi_level_index=False)
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        return data, info
    except Exception as e:
        # في حالة فشل الـ info (أمر شائع)، ننشئ معلومات أساسية
        return data, {"longName": ticker, "symbol": ticker}

# --- Main Logic ---
st.title("📈 Professional Stock Analysis System")

if symbol:
    try:
        with st.spinner(f"Fetching real-time data for {symbol}..."):
            df, info = load_data(symbol, period_map[selected_period])

        if not df.empty:
            # --- Header Section ---
            st.header(f"{info.get('longName', symbol)}")
            st.caption(f"{info.get('sector', 'N/A')} | {info.get('industry', 'N/A')} | Currency: {info.get('currency', 'USD')}")

            # --- Metrics ---
            m1, m2, m3, m4 = st.columns(4)

            # معالجة القيم لضمان أنها أرقام صحيحة للعرض
            current_price = float(df['Close'].iloc[-1])
            start_price = float(df['Close'].iloc[0])
            price_change = current_price - start_price
            pct_change = (price_change / start_price) * 100

            m1.metric("Current Price", f"${current_price:,.2f}")
            m2.metric("Period Change", f"${price_change:,.2f}", f"{pct_change:+.2f}%")
            m3.metric("Period High", f"${float(df['High'].max()):,.2f}")
            m4.metric("Period Low", f"${float(df['Low'].min()):,.2f}")

            # --- Charting ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                vertical_spacing=0.05, subplot_titles=('Price Action', 'Volume History'),
                                row_width=[0.3, 0.7])

            if chart_type == "Candlestick":
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'], name="Price"
                ), row=1, col=1)
            else:
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Close Price"), row=1, col=1)

            if show_sma20:
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'].rolling(20).mean(), name="SMA 20"), row=1, col=1)
            if show_sma50:
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'].rolling(50).mean(), name="SMA 50"), row=1, col=1)

            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='#adb5bd'), row=2, col=1)

            fig.update_layout(height=600, template="plotly_white", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # --- Tabs ---
            tab1, tab2 = st.tabs(["📋 Raw Data", "🏢 Company Profile"])
            with tab1:
                st.dataframe(df.sort_index(ascending=False), use_container_width=True)
            with tab2:
                st.write(info.get('longBusinessSummary', 'No description available.'))

        else:
            st.warning("No data found. Check the ticker symbol.")

    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")
else:
    st.info("Enter a stock ticker to begin.")