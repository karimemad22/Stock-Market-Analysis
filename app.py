import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. إعدادات الصفحة (تنسيق احترافي) ---
st.set_page_config(
    page_title="AI Stock Pro Analyzer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. إضافة لمسات جمالية (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px; background: white; }
    .recommendation-box { padding: 20px; border-radius: 10px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. دالة جلب البيانات (مُحدثة لحل مشاكل Yahoo) ---
@st.cache_data(ttl=3600)
def load_data(ticker, period):
    try:
        data = yf.download(ticker, period=period, progress=False, multi_level_index=False)
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        return data, info
    except:
        return pd.DataFrame(), {}

# --- 4. دالة حساب المؤشرات الفنية ---
def add_indicators(df):
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

# --- 5. القائمة الجانبية (Sidebar) ---
st.sidebar.header("🛠️ Dashboard Control")
# تم وضع Apple كقيمة افتراضية بناءً على نصيحتك
symbol = st.sidebar.text_input("Enter Ticker Symbol", value="AAPL").upper()
period = st.sidebar.selectbox("Timeframe", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2)
chart_style = st.sidebar.radio("Chart Type", ["Candlesticks", "Line"])

st.sidebar.subheader("Technical Layers")
show_ma = st.sidebar.checkbox("Moving Averages (20/50)", value=True)
show_rsi = st.sidebar.checkbox("RSI Indicator", value=True)
show_macd = st.sidebar.checkbox("MACD Indicator", value=False)

# --- 6. الواجهة الرئيسية ---
st.title("🚀 Professional AI Stock Analyzer")

if symbol:
    with st.spinner(f'Analyzing {symbol} market data...'):
        df, info = load_data(symbol, period)

    if not df.empty:
        df = add_indicators(df)

        # معلومات الشركة العلوية
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header(f"{info.get('longName', symbol)} ({symbol})")
            st.write(f"**Sector:** {info.get('sector', 'N/A')} | **Industry:** {info.get('industry', 'N/A')}")

        with col2:
            current_price = df['Close'].iloc[-1]
            change = current_price - df['Close'].iloc[-2]
            st.metric("Live Price", f"${current_price:,.2f}", f"{change:+.2f}")

        # --- 7. رسم الشارت الاحترافي ---
        rows = 2
        row_heights = [0.6, 0.2]
        if show_rsi:
            rows += 1
            row_heights.append(0.2)
        if show_macd:
            rows += 1
            row_heights.append(0.2)

        fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=row_heights)

        # شارت السعر
        if chart_style == "Candlesticks":
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Market"), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Price", line=dict(color="#2962FF", width=2)), row=1, col=1)

        # المتوسطات المتحركة
        if show_ma:
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'].rolling(20).mean(), name="SMA 20", line=dict(color="#FF9800", width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'].rolling(50).mean(), name="SMA 50", line=dict(color="#4CAF50", width=1)), row=1, col=1)

        # الحجم
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color="#cfd8dc"), row=2, col=1)

        # مؤشر RSI
        curr_row = 3
        if show_rsi:
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color="#9C27B0")), row=curr_row, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=curr_row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=curr_row, col=1)
            curr_row += 1

        # مؤشر MACD
        if show_macd:
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name="MACD", line=dict(color="blue")), row=curr_row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], name="Signal", line=dict(color="red")), row=curr_row, col=1)

        fig.update_layout(height=400 + (rows*120), template="plotly_white", showlegend=False, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # --- 8. تبويبات المعلومات والتحليل ---
        t1, t2, t3 = st.tabs(["📊 Technical Analysis", "🏢 About Company", "🔢 Raw Data"])

        with t1:
            st.subheader("Smart Analysis Report")
            last_rsi = df['RSI'].iloc[-1]
            col_a, col_b = st.columns(2)

            with col_a:
                if last_rsi > 70:
                    st.error(f"🔴 Overbought Condition: RSI is {last_rsi:.2f}. The stock might be overvalued.")
                elif last_rsi < 30:
                    st.success(f"🟢 Oversold Condition: RSI is {last_rsi:.2f}. Potential buying opportunity.")
                else:
                    st.info(f"🔵 Neutral Condition: RSI is {last_rsi:.2f}. Market is stable.")

            with col_b:
                price_vs_ma = "Above" if current_price > df['Close'].rolling(20).mean().iloc[-1] else "Below"
                st.write(f"**Current Trend:** Price is {price_vs_ma} 20-Day Moving Average.")

        with t2:
            st.write(info.get('longBusinessSummary', 'Information not available.'))

        with t3:
            st.dataframe(df.tail(20), use_container_width=True)

    else:
        st.error("Could not fetch data. Please check the ticker symbol or your internet connection.")

# --- التذييل ---
st.markdown("---")
st.caption("Powered by Streamlit & Yahoo Finance API | Final Project Version")