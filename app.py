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
    .main {
        background-color: #f5f7f9;
    }
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
show_sma20 = st.sidebar.checkbox("SMA 20")
show_sma50 = st.sidebar.checkbox("SMA 50")

# --- Data Fetching Function ---
@st.cache_data(ttl=3600)
def load_data(ticker, period):
    data = yf.download(ticker, period=period)
    info = yf.Ticker(ticker).info
    return data, info

# --- Main Logic ---
st.title("📊 Stock Market Analysis Pro")

if symbol:
    try:
        with st.spinner(f"Loading data for {symbol}..."):
            df, info = load_data(symbol, period_map[selected_period])

        if not df.empty:
            # --- Header Section ---
            col_logo, col_title = st.columns([1, 5])
            with col_title:
                st.header(f"{info.get('longName', symbol)}")
                st.caption(f"{info.get('sector', 'N/A')} | {info.get('industry', 'N/A')} | {info.get('currency', 'USD')}")

            # --- Metrics ---
            m1, m2, m3, m4 = st.columns(4)
            current_price = df['Close'].iloc[-1]
            open_price = df['Open'].iloc[-1]
            high_price = df['High'].max()
            low_price = df['Low'].min()
            
            # Use item() to get scalar values if df is MultiIndex (yfinance v0.2.x behavior)
            if isinstance(current_price, pd.Series):
                current_price = current_price.iloc[0]
                open_price = open_price.iloc[0]
                high_price = high_price.iloc[0]
                low_price = low_price.iloc[0]

            price_change = current_price - df['Close'].iloc[0]
            if isinstance(price_change, pd.Series): price_change = price_change.iloc[0]
            
            pct_change = (price_change / df['Close'].iloc[0]) * 100
            if isinstance(pct_change, pd.Series): pct_change = pct_change.iloc[0]

            m1.metric("Current Price", f"${current_price:,.2f}")
            m2.metric("Period Change", f"${price_change:,.2f}", f"{pct_change:+.2f}%")
            m3.metric("Period High", f"${high_price:,.2f}")
            m4.metric("Period Low", f"${low_price:,.2f}")

            # --- Charting ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.1, subplot_titles=('Price Action', 'Volume'), 
                               row_width=[0.3, 0.7])

            # Main Price Chart
            if chart_type == "Candlestick":
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'], name="Price"
                ), row=1, col=1)
            else:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['Close'], mode='lines', name="Close Price"
                ), row=1, col=1)

            # Moving Averages
            if show_sma20:
                sma20 = df['Close'].rolling(window=20).mean()
                fig.add_trace(go.Scatter(x=df.index, y=sma20, name="SMA 20", line=dict(color='orange')), row=1, col=1)
            if show_sma50:
                sma50 = df['Close'].rolling(window=50).mean()
                fig.add_trace(go.Scatter(x=df.index, y=sma50, name="SMA 50", line=dict(color='blue')), row=1, col=1)

            # Volume Chart
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='silver'), row=2, col=1)

            fig.update_layout(
                height=700,
                xaxis_rangeslider_visible=False,
                hovermode="x unified",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- Data & Info ---
            tab1, tab2 = st.tabs(["📋 Historical Data", "🏢 Company Profile"])
            
            with tab1:
                st.dataframe(df.sort_index(ascending=False), use_container_width=True)
            
            with tab2:
                st.write(info.get('longBusinessSummary', 'No summary available.'))
                col_i1, col_i2 = st.columns(2)
                col_i1.write(f"**Market Cap:** {info.get('marketCap', 'N/A'):,}")
                col_i1.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
                col_i2.write(f"**Website:** {info.get('website', 'N/A')}")
                col_i2.write(f"**Employees:** {info.get('fullTimeEmployees', 'N/A')}")

        else:
            st.error("No data found for this ticker. Please check the symbol.")
            
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        st.info("Check if the ticker symbol is correct or your internet connection.")
else:
    st.info("Enter a stock ticker (e.g., MSFT, GOOGL, NVDA) in the sidebar to start.")
