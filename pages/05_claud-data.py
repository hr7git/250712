import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import io

# 페이지 설정
st.set_page_config(
    page_title="ETF 시가상위 10위 데이터 다운로드",
    page_icon="📊",
    layout="wide"
)

st.title("📊 ETF 시가상위 10위 데이터 다운로드")
st.markdown("---")

# 주요 ETF 리스트 (시가총액 기준 상위 ETF들)
TOP_ETFS = [
    {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust"},
    {"symbol": "IVV", "name": "iShares Core S&P 500 ETF"},
    {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF"},
    {"symbol": "IEMG", "name": "iShares Core MSCI Emerging Markets ETF"},
    {"symbol": "VEA", "name": "Vanguard FTSE Developed Markets ETF"},
    {"symbol": "VWO", "name": "Vanguard FTSE Emerging Markets ETF"},
    {"symbol": "GLD", "name": "SPDR Gold Trust"},
    {"symbol": "VTV", "name": "Vanguard Value ETF"},
    {"symbol": "IWM", "name": "iShares Russell 2000 ETF"}
]

def get_etf_data(symbol, period="1y"):
    """ETF 데이터를 가져오는 함수"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        info = ticker.info
        
        # 기본 정보 추가
        data['Symbol'] = symbol
        data['Name'] = info.get('longName', 'N/A')
        data['Market_Cap'] = info.get('totalAssets', 'N/A')
        
        return data, info
    except Exception as e:
        st.error(f"{symbol} 데이터를 가져오는 중 오류가 발생했습니다: {str(e)}")
        return None, None

def format_market_cap(value):
    """시가총액을 포맷팅하는 함수"""
    if value == 'N/A' or value is None:
        return 'N/A'
    try:
        if value >= 1e12:
            return f"${value/1e12:.2f}T"
        elif value >= 1e9:
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:
            return f"${value/1e6:.2f}M"
        else:
            return f"${value:,.0f}"
    except:
        return 'N/A'

# 사이드바 설정
st.sidebar.header("설정")
period = st.sidebar.selectbox(
    "데이터 기간 선택",
    options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3,
    help="데이터를 가져올 기간을 선택하세요"
)

# 데이터 가져오기 버튼
if st.sidebar.button("데이터 가져오기", type="primary"):
    st.info("데이터를 가져오는 중입니다...")
    
    # 프로그레스 바
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_data = []
    etf_info = []
    
    for i, etf in enumerate(TOP_ETFS):
        status_text.text(f"처리 중: {etf['symbol']} ({i+1}/{len(TOP_ETFS)})")
        progress_bar.progress((i + 1) / len(TOP_ETFS))
        
        data, info = get_etf_data(etf['symbol'], period)
        
        if data is not None:
            all_data.append(data)
            etf_info.append({
                'Symbol': etf['symbol'],
                'Name': etf['name'],
                'Market_Cap': format_market_cap(info.get('totalAssets')),
                'Expense_Ratio': f"{info.get('annualReportExpenseRatio', 'N/A')}%",
                'Yield': f"{info.get('yield', 'N/A')}%",
                'Beta': info.get('beta', 'N/A')
            })
    
    status_text.text("완료!")
    progress_bar.empty()
    
    if all_data:
        st.session_state.all_data = all_data
        st.session_state.etf_info = etf_info
        st.success("데이터를 성공적으로 가져왔습니다!")

# 데이터 표시 및 다운로드
if 'all_data' in st.session_state:
    
    # ETF 기본 정보 표시
    st.subheader("📋 ETF 기본 정보")
    info_df = pd.DataFrame(st.session_state.etf_info)
    st.dataframe(info_df, use_container_width=True)
    
    # 각 ETF 데이터 표시
    st.subheader("📈 가격 데이터")
    
    # 탭으로 각 ETF 데이터 표시
    tabs = st.tabs([etf['symbol'] for etf in TOP_ETFS])
    
    for i, tab in enumerate(tabs):
        with tab:
            if i < len(st.session_state.all_data):
                data = st.session_state.all_data[i]
                
                # 차트 표시
                st.line_chart(data[['Close']])
                
                # 최근 데이터 표시
                st.write("최근 10일 데이터:")
                display_data = data.tail(10)[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                display_data.index = display_data.index.strftime('%Y-%m-%d')
                st.dataframe(display_data)
    
    # 전체 데이터 합치기
    st.subheader("💾 데이터 다운로드")
    
    # 모든 데이터를 하나의 DataFrame으로 합치기
    combined_data = pd.concat(st.session_state.all_data, ignore_index=True)
    combined_data = combined_data.reset_index()
    
    # 날짜 컬럼 포맷팅
    combined_data['Date'] = pd.to_datetime(combined_data['Date']).dt.strftime('%Y-%m-%d')
    
    # 컬럼 순서 정렬
    columns_order = ['Date', 'Symbol', 'Name', 'Open', 'High', 'Low', 'Close', 'Volume', 'Market_Cap']
    combined_data = combined_data[columns_order]
    
    # 데이터 미리보기
    st.write("다운로드할 데이터 미리보기:")
    st.dataframe(combined_data.head(20), use_container_width=True)
    
    # CSV 다운로드 버튼
    csv_buffer = io.StringIO()
    combined_data.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_data = csv_buffer.getvalue()
    
    current_date = datetime.now().strftime('%Y%m%d')
    filename = f"top10_etf_data_{current_date}.csv"
    
    st.download_button(
        label="📥 CSV 파일 다운로드",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        type="primary"
    )
    
    # 통계 정보
    st.subheader("📊 통계 정보")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("총 데이터 수", len(combined_data))
    
    with col2:
        st.metric("ETF 개수", len(TOP_ETFS))
    
    with col3:
        date_range = f"{combined_data['Date'].min()} ~ {combined_data['Date'].max()}"
        st.metric("데이터 기간", date_range)

else:
    st.info("👈 왼쪽 사이드바에서 '데이터 가져오기' 버튼을 클릭하여 시작하세요!")
    
    # 사용법 안내
    st.markdown("""
    ## 사용법
    
    1. **왼쪽 사이드바**에서 데이터 기간을 선택하세요
    2. **'데이터 가져오기'** 버튼을 클릭하세요
    3. 데이터를 확인하고 **CSV 파일로 다운로드**하세요
    
    ## 포함된 ETF
    """)
    
    # ETF 리스트 표시
    etf_df = pd.DataFrame(TOP_ETFS)
    st.dataframe(etf_df, use_container_width=True)

# 푸터
st.markdown("---")
st.markdown("⚠️ 이 애플리케이션은 교육 목적으로만 사용하세요. 투자 결정은 전문가와 상담하세요.")
