import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- 1. إعدادات الصفحة الاحترافية ---
st.set_page_config(
    page_title="AI Stock Pro | Advanced Dashboard",
    page_icon="🚀",
    layout="wide"
)

# تحسين مظهر الواجهة عبر CSS متقدم
st.markdown("""
    <style>
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #eef2f6;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 25px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007bff !important;
        color: white !important;
    }
    h1 { color: #1e293b; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. وظائف معالجة البيانات ---
@st.cache_data(ttl=3600)
def fetch_stock_data(ticker_symbol, period_selected):
    try:
        ticker_obj = yf.Ticker(ticker_symbol)
        df = ticker_obj.history(period=period_selected)
        if df.empty:
            return None, None

        # جلب معلومات الشركة بأمان
        try:
            info = ticker_obj.info
        except:
            info = {"longName": ticker_symbol}

        return df, info
    except Exception as e:
        return None, None

def apply_indicators(df):
    # حساب RSI (14 period)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()

    # تجنب القسمة على صفر
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # المتوسطات المتحركة (SMA)
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()

    # مستويات الدعم والمقاومة (20 يوم)
    df['Resistance'] = df['High'].rolling(window=20).max()
    df['Support'] = df['Low'].rolling(window=20).min()

    return df

# --- 3. الهيكل الرئيسي للتطبيق ---
st.title("🚀 AI Stock Market Intelligence")
st.markdown("Professional-grade technical analysis and real-time market data.")

# القائمة الجانبية
st.sidebar.header("📊 Market Selector")
symbol = st.sidebar.text_input("Enter Ticker Symbol", value="NVDA").upper().strip()
time_frame = st.sidebar.selectbox("Timeframe", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2)
chart_type = st.sidebar.radio("Visualization", ["Candlesticks", "Line Chart"])

if symbol:
    with st.spinner(f"🔍 Analyzing {symbol}..."):
        df, info = fetch_stock_data(symbol, time_frame)

    if df is not None and len(df) > 1:
        df = apply_indicators(df)

        # صف المقاييس (KPIs)
        curr_price = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        price_diff = curr_price - prev_close
        pct_diff = (price_diff / prev_close) * 100

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Price", f"${curr_price:,.2f}", f"{price_diff:+.2f}")
        m2.metric("Day Change (%)", f"{pct_diff:+.2f}%")
        m3.metric("24h High", f"${df['High'].iloc[-1]:,.2f}")
        m4.metric("Volume", f"{df['Volume'].iloc[-1]:,.0f}")

        st.markdown("---")

        # --- 4. الرسم البياني المتطور ---
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.07,
            row_heights=[0.5, 0.2, 0.2],
            subplot_titles=("Price Action & Moving Averages", "RSI Momentum", "Trading Volume")
        )

        # 1. رسم السعر
        if chart_type == "Candlesticks":
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name="Candlestick"
            ), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Price", line=dict(color='#007bff', width=2)), row=1, col=1)

        # إضافة المتوسطات المتحركة
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="SMA 20", line=dict(color='#ff9f43', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name="SMA 50", line=dict(color='#10ac84', width=1.5)), row=1, col=1)

        # 2. رسم RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='#5f27cd', width=2)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ee5253", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#1dd1a1", row=2, col=1)

        # 3. رسم الحجم
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='#b2bec3'), row=3, col=1)

        # تعديل خصائص الرسم
        fig.update_layout(height=850, template="plotly_white", xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # --- 5. التبويبات السفلية للتحليل ---
        tab_tech, tab_info, tab_data = st.tabs(["🎯 AI Technical Analysis", "🏢 Company Info", "📋 Historical Data"])

        with tab_tech:
            st.subheader("Technical Health Check")
            c1, c2, c3 = st.columns(3)

            rsi_now = df['RSI'].iloc[-1]
            with c1:
                st.write(f"**RSI (14):** `{rsi_now:.2f}`")
                if rsi_now > 70:
                    st.error("🚨 Overbought (Potential Pullback)")
                elif rsi_now < 30:
                    st.success("✅ Oversold (Potential Rebound)")
                else:
                    st.info("⚖️ Neutral Momentum")

            with c2:
                # التحقق من الاتجاه بناءً على المتوسط 50 يوم
                sma50_last = df['SMA50'].iloc[-1]
                trend_status = "BULLISH" if curr_price > sma50_last else "BEARISH"
                st.write(f"**Trend Status:** `{trend_status}`")
                if trend_status == "BULLISH":
                    st.write("📈 Price is holding above 50-day average.")
                else:
                    st.write("📉 Price is struggling below 50-day average.")

            with c3:
                st.write(f"**Resistance (20D High):** `${df['Resistance'].iloc[-1]:,.2f}`")
                st.write(f"**Support (20D Low):** `${df['Support'].iloc[-1]:,.2f}`")
                st.caption("Based on last 20 trading sessions.")

        with tab_info:
            if info:
                st.subheader(info.get('longName', symbol))
                st.markdown(f"**Sector:** {info.get('sector', 'N/A')} | **Industry:** {info.get('industry', 'N/A')}")
                st.write(info.get('longBusinessSummary', 'No description available for this ticker.'))
            else:
                st.info("No detailed company info found.")

        with tab_data:
            st.write("Recent Trading Data (Last 100 Days)")
            st.dataframe(df.tail(100).sort_index(ascending=False), use_container_width=True)

    else:
        st.error(f"❌ Error: Could not retrieve data for '{symbol}'. Please ensure the ticker is correct (e.g., AAPL, TSLA, BTC-USD).")

# تذييل الصفحة
st.sidebar.markdown("---")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")