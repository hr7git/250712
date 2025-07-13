import streamlit as st
import yfinance as yf
import sqlite3
import pandas as pd
import os
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Configuration ---
DATABASE_FILE = "etf_data.db"
GLOBAL_ETFS = [
    "SPY", "IVV", "VOO", "QQQ", "DIA", "GRN", "VXUS", "VEA", "VWO", "GLD", "SLV", "BND",
]

# --- Database Functions ---
def create_table(conn):
    """Creates the etfs table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS etfs (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            currency TEXT,
            market TEXT,
            exchange TEXT,
            longName TEXT,
            quoteType TEXT
        )
    ''')
    conn.commit()

def insert_etf_data(conn, etf_data):
    """Inserts or updates ETF data into the database."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO etfs (symbol, name, currency, market, exchange, longName, quoteType)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        etf_data.get('symbol'),
        etf_data.get('name'),
        etf_data.get('currency'),
        etf_data.get('market'),
        etf_data.get('exchange'),
        etf_data.get('longName'),
        etf_data.get('quoteType')
    ))
    conn.commit()

def fetch_all_etfs(conn):
    """Fetches all ETF data from the database."""
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM etfs')
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=[description[0] for description in cursor.description])
        return df
    return pd.DataFrame() # Return empty DataFrame if no data

# --- New Function for Historical Data and Returns Calculation ---
def get_historical_data(symbol, period="10y"):
    """Fetches historical 'Close' price for a given symbol."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if not hist.empty:
            initial_price = hist['Close'].iloc[0]
            hist['Cumulative Return (%)'] = ((hist['Close'] / initial_price) - 1) * 100
            return hist[['Close', 'Cumulative Return (%)']]
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching historical data for {symbol}: {e}")
        return pd.DataFrame()

# --- Streamlit App ---
st.set_page_config(layout="wide", page_title="Global ETF Data & Analysis")

st.title("📈 글로벌 ETF 데이터 및 분석")
st.markdown("`yfinance`를 사용하여 글로벌 주요 ETF 정보를 가져오고, SQLite 데이터베이스에 저장하며, 수익률을 분석하고, 데이터를 CSV로 내보냅니다.")

# --- ETF Data Fetching/Display Section ---
st.subheader("저장된 ETF 데이터 관리")
if st.button("ETF 데이터 업데이트 및 저장", key="update_db_button"):
    st.info("ETF 데이터를 가져와 데이터베이스에 저장 중입니다. 잠시만 기다려 주세요...")

    conn = sqlite3.connect(DATABASE_FILE)
    create_table(conn)

    fetched_count = 0
    total_etfs = len(GLOBAL_ETFS)
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, etf_symbol in enumerate(GLOBAL_ETFS):
        try:
            ticker = yf.Ticker(etf_symbol)
            info = ticker.info
            
            etf_info = {
                'symbol': info.get('symbol'),
                'name': info.get('shortName', 'N/A'),
                'currency': info.get('currency', 'N/A'),
                'market': info.get('market', 'N/A'),
                'exchange': info.get('exchange', 'N/A'),
                'longName': info.get('longName', 'N/A'),
                'quoteType': info.get('quoteType', 'N/A')
            }
            insert_etf_data(conn, etf_info)
            fetched_count += 1
            status_text.text(f"✅ {etf_symbol} 데이터 저장 완료.")
        except Exception as e:
            status_text.warning(f"⚠️ {etf_symbol} 데이터를 가져오지 못했습니다: {e}")
        
        progress = (i + 1) / total_etfs
        progress_bar.progress(progress)

    conn.close()
    st.success(f"데이터 업데이트 및 저장 완료! 총 {fetched_count}개의 ETF 데이터가 저장되었습니다.")
    st.balloons()

# Display current ETFs from DB
if os.path.exists(DATABASE_FILE):
    conn = sqlite3.connect(DATABASE_FILE)
    df_etfs_in_db = fetch_all_etfs(conn)
    conn.close()

    if not df_etfs_in_db.empty:
        st.dataframe(df_etfs_in_db)
        available_symbols = df_etfs_in_db['symbol'].tolist()
    else:
        st.info("데이터베이스에 ETF 데이터가 없습니다. 위의 버튼을 눌러 데이터를 가져오세요.")
        available_symbols = []
else:
    st.info("데이터베이스 파일이 없습니다. 위의 버튼을 눌러 생성하세요.")
    available_symbols = []

#---

## 2. CSV Export Section

st.subheader("데이터베이스를 CSV로 내보내기")
if not df_etfs_in_db.empty:
    csv_data = df_etfs_in_db.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 ETF 데이터 CSV 다운로드",
        data=csv_data,
        file_name="etf_data.csv",
        mime="text/csv",
        help="현재 데이터베이스에 저장된 ETF 정보를 CSV 파일로 다운로드합니다."
    )
else:
    st.warning("내보낼 데이터가 없습니다. 먼저 ETF 데이터를 업데이트하세요.")

#---

## 3. ETF Returns Graphing Section (from previous code)

st.subheader("ETF 수익률 그래프 그리기")

if available_symbols:
    selected_etfs = st.multiselect(
        "수익률을 비교할 ETF 3개를 선택하세요:",
        options=available_symbols,
        default=available_symbols[:min(3, len(available_symbols))],
        max_selections=3
    )

    if selected_etfs:
        st.info(f"선택된 ETF: {', '.join(selected_etfs)}")
        
        all_returns = pd.DataFrame()

        for etf_symbol in selected_etfs:
            st.write(f"⏳ {etf_symbol}의 10년치 데이터를 가져오는 중...")
            df_hist = get_historical_data(etf_symbol, period="10y")
            
            if not df_hist.empty:
                df_hist = df_hist.rename(columns={'Cumulative Return (%)': f'{etf_symbol} Cumulative Return (%)'})
                
                if all_returns.empty:
                    all_returns = df_hist[[f'{etf_symbol} Cumulative Return (%)']]
                else:
                    all_returns = all_returns.join(df_hist[[f'{etf_symbol} Cumulative Return (%)']], how='outer')
            else:
                st.warning(f"⚠️ {etf_symbol}의 10년치 데이터를 가져올 수 없습니다. 다른 ETF를 선택하거나 나중에 다시 시도하세요.")
        
        if not all_returns.empty:
            fig = go.Figure()

            for col in all_returns.columns:
                fig.add_trace(go.Scatter(x=all_returns.index, y=all_returns[col], mode='lines', name=col.replace(' Cumulative Return (%)', '')))

            fig.update_layout(
                title="선택된 ETF의 10년 누적 수익률",
                xaxis_title="날짜",
                yaxis_title="누적 수익률 (%)",
                hovermode="x unified",
                legend_title="ETF"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("선택된 ETF 중 유효한 데이터를 가져올 수 있는 ETF가 없습니다. 다른 ETF를 선택하세요.")
    else:
        st.info("위에서 수익률을 비교할 ETF를 선택해주세요.")
else:
    st.warning("데이터베이스에 ETF 데이터가 없습니다. 먼저 'ETF 데이터 업데이트 및 저장' 버튼을 클릭하여 데이터를 채우세요.")

st.markdown("""
---
**알림:**
* 수익률은 **시작점을 0%**로 하여 각 시점의 **누적 수익률**을 나타냅니다.
* 데이터는 `yfinance`에서 제공하는 종가(Close price)를 기준으로 합니다.
* Streamlit Cloud의 특성상 `etf_data.db` 파일이 재배포 시 초기화될 수 있으므로, 앱 실행 시 'ETF 데이터 업데이트 및 저장' 버튼을 눌러 데이터를 새로 가져오는 것이 좋습니다.
""")
