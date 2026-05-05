import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. إعداد واجهة التطبيق (Clean Layout)
st.set_page_config(page_title="Stock Analysis", layout="wide")
st.title("📈 Stock Market Analysis System")

# 2. إدخال رمز السهم (Input Field)
symbol = st.sidebar.text_input("Enter Stock Symbol (e.g. AAPL):", "AAPL").upper()
period = st.sidebar.selectbox("Select Period:", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"])

if symbol:
    try:
        # 3. جلب البيانات (Fetch from API)
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)

        if not df.empty:
            st.subheader(f"Displaying data for: {symbol}")

            # 4. الرسم البياني (Visualization)
            fig = go.Figure(data=[go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price')])
            fig.update_layout(
                title=f"{symbol} Price Trends",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

            # 5. عرض البيانات (Historical Data)
            with st.expander("View Raw Data"):
                st.write(df)
            
            # 6. إحصائيات سريعة
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Price", f"${df['Close'].iloc[-1]:.2f}")
            price_change = df['Close'].iloc[-1] - df['Close'].iloc[0]
            col2.metric("Period Change", f"${price_change:.2f}", f"{(price_change/df['Close'].iloc[0])*100:.2f}%")
            col3.metric("High (Period)", f"${df['High'].max():.2f}")

        else:
            st.error("Invalid Symbol or no data found! Please try again.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")
