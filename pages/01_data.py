import streamlit as st
import yfinance as yf
import sqlite3
import pandas as pd
import os

# --- Configuration ---
DATABASE_FILE = "etf_data.db"
# A selection of broad market and sector-specific global ETFs.
# Note: yfinance doesn't directly provide "global market cap Top 10 ETFs" rankings.
# This list is a curated selection of commonly traded and significant global ETFs.
# You might need to adjust this list based on your definition of "Top 10 Global Market Cap ETFs".
GLOBAL_ETFS = [
    "SPY",  # SPDR S&P 500 ETF Trust (US Large Cap)
    "IVV",  # iShares Core S&P 500 ETF (US Large Cap)
    "VOO",  # Vanguard S&P 500 ETF (US Large Cap)
    "QQQ",  # Invesco QQQ Trust (US Tech-heavy)
    "DIA",  # SPDR Dow Jones Industrial Average ETF Trust (US Blue Chip)
    "GRN",  # iShares Global Clean Energy ETF (Global Clean Energy)
    "VXUS", # Vanguard Total International Stock Index Fund ETF (Ex-US Developed & Emerging Markets)
    "VEA",  # Vanguard FTSE Developed Markets ETF (Developed Markets ex-US)
    "VWO",  # Vanguard FTSE Emerging Markets ETF (Emerging Markets)
    "GLD",  # SPDR Gold Shares (Gold) - often considered a global asset
    "SLV",  # iShares Silver Trust (Silver) - often considered a global asset
    "BND",  # Vanguard Total Bond Market ETF (US Bonds - for portfolio diversification example)
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

# --- Streamlit App ---
st.set_page_config(layout="wide", page_title="Global ETF Data")

st.title("🌎 글로벌 시총 ETF 데이터")
st.markdown("yfinance를 사용하여 글로벌 주요 ETF 정보를 가져와 SQLite 데이터베이스에 저장하고 표시합니다.")

if st.button("데이터 업데이트 및 저장"):
    st.info("ETF 데이터를 가져와 데이터베이스에 저장 중입니다. 잠시만 기다려 주세요...")

    # Connect to SQLite database
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
            
            # Extract relevant information. Handle missing keys gracefully.
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

st.subheader("저장된 ETF 데이터")
# Display data from the database
if os.path.exists(DATABASE_FILE):
    conn = sqlite3.connect(DATABASE_FILE)
    df_etfs = fetch_all_etfs(conn)
    conn.close()

    if not df_etfs.empty:
        st.dataframe(df_etfs)
    else:
        st.info("데이터베이스에 ETF 데이터가 없습니다. '데이터 업데이트 및 저장' 버튼을 눌러 데이터를 가져오세요.")
else:
    st.info("데이터베이스 파일이 없습니다. '데이터 업데이트 및 저장' 버튼을 눌러 생성하세요.")

st.markdown("""
---
**참고:**
* `yfinance`는 실시간 시가총액 순위를 직접 제공하지 않습니다. 위의 ETF 목록은 **글로벌 주요 ETF 예시**입니다.
* 특정 시점의 "글로벌 시총 Top 10"을 정확히 얻으려면 다른 API나 데이터 소스가 필요할 수 있습니다.
* 데이터는 `etf_data.db` 파일에 저장됩니다. Streamlit Cloud에서는 앱이 재배포될 때마다 데이터가 초기화될 수 있으므로, 영구적인 데이터 저장이 필요하면 Streamlit 외부 저장소(예: Google Sheets, S3, PostgreSQL)를 사용하는 것을 고려해야 합니다.
""")
