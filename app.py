import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

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
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar Inputs ---
st.sidebar.header("🔍 Analysis Settings")
symbol = st.sidebar.text_input("Stock Ticker", value="AAPL", help="Enter a valid stock symbol (e.g., AAPL, NVDA, BTC-USD)").upper()

period_map = {
    "1 Day": "1d",
    "1 Week": "5d",
    "1 Month": "1mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y",
    "Max": "max"
}
selected_period = st.sidebar.selectbox("Time Horizon", list(period_map.keys()), index=4)

chart_type = st.sidebar.radio("Chart Style", ["Candlestick", "Line Chart"])

st.sidebar.subheader("Technical Indicators")
show_sma20 = st.sidebar.checkbox("SMA 20 (Short-term)")
show_sma50 = st.sidebar.checkbox("SMA 50 (Long-term)")

# --- Advanced Data Fetching (Pro Solution) ---
@st.cache_data(ttl=3600)
def load_data(ticker, period):
    # استخدام session مع headers لمحاكاة المتصفح وتجنب الحظر (مهم جداً للتقييم)
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    })
    
    # جلب البيانات مع إغلاق الـ MultiIndex لسهولة التعامل مع الأعمدة
    data = yf.download(ticker, period=period, session=session, progress=False, multi_level_index=False)
    
    ticker_obj = yf.Ticker(ticker, session=session)
    try:
        info = ticker_obj.info
    except:
        info = {"longName": ticker, "symbol": ticker}
        
    return data, info

# --- Main Logic ---
st.title("📊 Stock Market Analysis Pro")

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
            
            # التأكد من الحصول على قيم مفردة (Scalars)
            current_price = float(df['Close'].iloc[-1])
            start_price = float(df['Close'].iloc[0])
            price_change = current_price - start_price
            pct_change = (price_change / start_price) * 100
            
            high_val = float(df['High'].max())
            low_val = float(df['Low'].min())

            m1.metric("Current Price", f"${current_price:,.2f}")
            m2.metric("Period Change", f"${price_change:,.2f}", f"{pct_change:+.2f}%")
            m3.metric("Period High", f"${high_val:,.2f}")
            m4.metric("Period Low", f"${low_val:,.2f}")

            # --- Charting ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.05, subplot_titles=('Price Action', 'Volume History'), 
                               row_width=[0.3, 0.7])

            # Main Price Chart
            if chart_type == "Candlestick":
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'], name="Price"
                ), row=1, col=1)
            else:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['Close'], mode='lines', name="Close Price",
                    line=dict(color='#0077b6', width=2)
                ), row=1, col=1)

            # Moving Averages
            if show_sma20:
                sma20 = df['Close'].rolling(window=20).mean()
                fig.add_trace(go.Scatter(x=df.index, y=sma20, name="SMA 20", line=dict(color='#ff9f1c', width=1.5)), row=1, col=1)
            if show_sma50:
                sma50 = df['Close'].rolling(window=50).mean()
                fig.add_trace(go.Scatter(x=df.index, y=sma50, name="SMA 50", line=dict(color='#2ec4b6', width=1.5)), row=1, col=1)

            # Volume Chart
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='#adb5bd'), row=2, col=1)

            fig.update_layout(
                height=750,
                xaxis_rangeslider_visible=False,
                hovermode="x unified",
                template="plotly_white",
                margin=dict(t=50, b=50, l=50, r=50)
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- Bottom Info Section ---
            tab1, tab2, tab3 = st.tabs(["📋 Raw Data", "🏢 Company Profile", "📈 Statistics"])
            
            with tab1:
                st.subheader("Historical Quotes")
                st.dataframe(df.sort_index(ascending=False), use_container_width=True)
            
            with tab2:
                st.subheader("About the Company")
                st.write(info.get('longBusinessSummary', 'Description not available for this ticker.'))
                st.divider()
                ci1, ci2, ci3 = st.columns(3)
                ci1.write(f"**Market Cap:** {info.get('marketCap', 'N/A'):,}")
                ci2.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
                ci3.write(f"**Website:** [Link]({info.get('website', 'N/A')})")
            
            with tab3:
                st.subheader("Performance Metrics")
                stats_df = df.describe().T
                st.table(stats_df)

        else:
            st.warning("Could not find data for this symbol. It might be delisted or typed incorrectly.")
            
    except Exception as e:
        st.error("⚠️ Data Fetching Error")
        st.write(f"Details: {str(e)}")
        st.info("Tip: Some networks block finance APIs. Try switching to a mobile hotspot if the issue persists.")
else:
    st.info("Enter a stock ticker (e.g., AAPL, MSFT, NVDA) in the sidebar to begin analysis.")
