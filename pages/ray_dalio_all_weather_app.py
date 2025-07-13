import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import io
import plotly.graph_objects as go
import plotly.express as px

# 페이지 설정
st.set_page_config(
    page_title="레이달리오 올웨더 포트폴리오 ETF 데이터",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ 레이달리오 올웨더 포트폴리오 ETF 데이터 다운로드")
st.markdown("---")

# 올웨더 포트폴리오 ETF 구성
ALL_WEATHER_ETFS = [
    {
        "symbol": "TLT",
        "name": "iShares 20+ Year Treasury Bond ETF",
        "allocation": 40.0,
        "category": "장기 채권",
        "description": "20년 이상 만기 미국 국채"
    },
    {
        "symbol": "SPY",
        "name": "SPDR S&P 500 ETF Trust",
        "allocation": 30.0,
        "category": "주식",
        "description": "S&P 500 지수 추종"
    },
    {
        "symbol": "IEI",
        "name": "iShares 3-7 Year Treasury Bond ETF",
        "allocation": 15.0,
        "category": "중기 채권",
        "description": "3-7년 만기 미국 국채"
    },
    {
        "symbol": "GLD",
        "name": "SPDR Gold Trust",
        "allocation": 7.5,
        "category": "귀금속",
        "description": "금 현물 추종"
    },
    {
        "symbol": "DBC",
        "name": "Invesco DB Commodity Index Tracking Fund",
        "allocation": 7.5,
        "category": "상품",
        "description": "상품 지수 추종"
    }
]

# 사이드바 - 포트폴리오 정보
st.sidebar.header("📊 올웨더 포트폴리오 구성")

# 포트폴리오 구성 시각화
allocation_data = {
    "ETF": [etf["symbol"] for etf in ALL_WEATHER_ETFS],
    "비중": [etf["allocation"] for etf in ALL_WEATHER_ETFS],
    "카테고리": [etf["category"] for etf in ALL_WEATHER_ETFS]
}

allocation_df = pd.DataFrame(allocation_data)
st.sidebar.dataframe(allocation_df, use_container_width=True)

# 포트폴리오 철학 설명
st.sidebar.markdown("""
### 🧠 올웨더 포트폴리오 철학

**4계절 대응 전략:**
- **성장 시기**: 주식이 주도
- **침체 시기**: 채권이 방어
- **인플레이션**: 상품과 금이 보호
- **디플레이션**: 장기 채권이 수익

**리스크 패리티 접근:**
- 각 자산이 동등한 리스크 기여
- 변동성 조정된 포트폴리오
- 모든 경제 환경에서 안정적 수익
""")

# 메인 설정
st.sidebar.header("⚙️ 데이터 설정")
period = st.sidebar.selectbox(
    "데이터 기간 선택",
    options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y"],
    index=3,
    help="백테스트 기간을 선택하세요"
)

# 벤치마크 비교 옵션
show_benchmark = st.sidebar.checkbox("벤치마크 비교 (60/40 포트폴리오)", value=True)

def get_etf_data(symbol, period="1y"):
    """ETF 데이터를 가져오는 함수"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        info = ticker.info
        
        # 기본 정보 추가
        data['Symbol'] = symbol
        data['Name'] = info.get('longName', 'N/A')
        data['Expense_Ratio'] = info.get('annualReportExpenseRatio', 0)
        data['Yield'] = info.get('yield', 0)
        data['Beta'] = info.get('beta', 1.0)
        
        return data, info
    except Exception as e:
        st.error(f"{symbol} 데이터를 가져오는 중 오류가 발생했습니다: {str(e)}")
        return None, None

def calculate_portfolio_performance(data_dict, allocations):
    """포트폴리오 성과 계산"""
    portfolio_returns = None
    
    for symbol, allocation in allocations.items():
        if symbol in data_dict:
            returns = data_dict[symbol]['Close'].pct_change().fillna(0)
            weighted_returns = returns * (allocation / 100)
            
            if portfolio_returns is None:
                portfolio_returns = weighted_returns
            else:
                portfolio_returns += weighted_returns
    
    # 누적 수익률 계산
    cumulative_returns = (1 + portfolio_returns).cumprod() - 1
    
    return portfolio_returns, cumulative_returns

# 데이터 가져오기 버튼
if st.sidebar.button("📈 데이터 가져오기", type="primary"):
    st.info("올웨더 포트폴리오 데이터를 가져오는 중입니다...")
    
    # 프로그레스 바
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_data = []
    etf_info = []
    data_dict = {}
    
    # 올웨더 포트폴리오 ETF 데이터 가져오기
    for i, etf in enumerate(ALL_WEATHER_ETFS):
        status_text.text(f"처리 중: {etf['symbol']} - {etf['name']} ({i+1}/{len(ALL_WEATHER_ETFS)})")
        progress_bar.progress((i + 1) / len(ALL_WEATHER_ETFS))
        
        data, info = get_etf_data(etf['symbol'], period)
        
        if data is not None:
            # 포트폴리오 비중 정보 추가
            data['Allocation'] = etf['allocation']
            data['Category'] = etf['category']
            
            all_data.append(data)
            data_dict[etf['symbol']] = data
            
            etf_info.append({
                'Symbol': etf['symbol'],
                'Name': etf['name'],
                'Allocation': f"{etf['allocation']}%",
                'Category': etf['category'],
                'Expense_Ratio': f"{info.get('annualReportExpenseRatio', 0)*100:.2f}%",
                'Yield': f"{info.get('yield', 0)*100:.2f}%",
                'Beta': f"{info.get('beta', 1.0):.2f}",
                'Description': etf['description']
            })
    
    # 벤치마크 데이터 (60/40 포트폴리오)
    if show_benchmark:
        status_text.text("벤치마크 데이터 처리 중...")
        
        # 60/40 포트폴리오를 위한 AGG (채권) 데이터 추가
        agg_data, agg_info = get_etf_data("AGG", period)
        if agg_data is not None:
            data_dict["AGG"] = agg_data
    
    status_text.text("포트폴리오 성과 계산 중...")
    
    # 올웨더 포트폴리오 성과 계산
    allocations = {etf['symbol']: etf['allocation'] for etf in ALL_WEATHER_ETFS}
    portfolio_returns, portfolio_cumulative = calculate_portfolio_performance(data_dict, allocations)
    
    # 60/40 벤치마크 성과 계산
    if show_benchmark and "SPY" in data_dict and "AGG" in data_dict:
        benchmark_allocations = {"SPY": 60, "AGG": 40}
        benchmark_returns, benchmark_cumulative = calculate_portfolio_performance(data_dict, benchmark_allocations)
        st.session_state.benchmark_returns = benchmark_returns
        st.session_state.benchmark_cumulative = benchmark_cumulative
    
    status_text.text("완료!")
    progress_bar.empty()
    
    if all_data:
        st.session_state.all_data = all_data
        st.session_state.etf_info = etf_info
        st.session_state.data_dict = data_dict
        st.session_state.portfolio_returns = portfolio_returns
        st.session_state.portfolio_cumulative = portfolio_cumulative
        st.success("올웨더 포트폴리오 데이터를 성공적으로 가져왔습니다!")

# 데이터 표시 및 분석
if 'all_data' in st.session_state:
    
    # 포트폴리오 구성 요약
    st.subheader("📋 올웨더 포트폴리오 구성 요약")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 자산 배분 파이 차트
        fig_pie = px.pie(
            values=[etf['allocation'] for etf in ALL_WEATHER_ETFS],
            names=[f"{etf['symbol']}\n({etf['category']})" for etf in ALL_WEATHER_ETFS],
            title="자산 배분 비중"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # 카테고리별 배분
        category_allocation = {}
        for etf in ALL_WEATHER_ETFS:
            category = etf['category']
            if category in category_allocation:
                category_allocation[category] += etf['allocation']
            else:
                category_allocation[category] = etf['allocation']
        
        fig_category = px.bar(
            x=list(category_allocation.keys()),
            y=list(category_allocation.values()),
            title="카테고리별 배분",
            labels={'x': '자산 카테고리', 'y': '비중 (%)'}
        )
        st.plotly_chart(fig_category, use_container_width=True)
    
    # ETF 상세 정보
    st.subheader("📊 ETF 상세 정보")
    info_df = pd.DataFrame(st.session_state.etf_info)
    st.dataframe(info_df, use_container_width=True)
    
    # 포트폴리오 성과 분석
    st.subheader("📈 포트폴리오 성과 분석")
    
    # 성과 차트
    fig_performance = go.Figure()
    
    # 올웨더 포트폴리오 성과
    fig_performance.add_trace(
        go.Scatter(
            x=st.session_state.portfolio_cumulative.index,
            y=st.session_state.portfolio_cumulative.values * 100,
            mode='lines',
            name='올웨더 포트폴리오',
            line=dict(color='blue', width=2)
        )
    )
    
    # 벤치마크 성과 (60/40)
    if show_benchmark and 'benchmark_cumulative' in st.session_state:
        fig_performance.add_trace(
            go.Scatter(
                x=st.session_state.benchmark_cumulative.index,
                y=st.session_state.benchmark_cumulative.values * 100,
                mode='lines',
                name='60/40 포트폴리오',
                line=dict(color='red', width=2)
            )
        )
    
    fig_performance.update_layout(
        title="포트폴리오 누적 수익률 비교",
        xaxis_title="날짜",
        yaxis_title="누적 수익률 (%)",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_performance, use_container_width=True)
    
    # 성과 지표
    st.subheader("📊 성과 지표")
    
    # 성과 계산
    total_return = st.session_state.portfolio_cumulative.iloc[-1] * 100
    annual_return = ((1 + st.session_state.portfolio_cumulative.iloc[-1]) ** (252 / len(st.session_state.portfolio_returns)) - 1) * 100
    volatility = st.session_state.portfolio_returns.std() * (252 ** 0.5) * 100
    sharpe_ratio = annual_return / volatility if volatility > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 수익률", f"{total_return:.2f}%")
    
    with col2:
        st.metric("연간 수익률", f"{annual_return:.2f}%")
    
    with col3:
        st.metric("변동성", f"{volatility:.2f}%")
    
    with col4:
        st.metric("샤프 비율", f"{sharpe_ratio:.2f}")
    
    # 개별 ETF 성과
    st.subheader("💹 개별 ETF 성과")
    
    # 각 ETF 별 탭
    tabs = st.tabs([etf['symbol'] for etf in ALL_WEATHER_ETFS])
    
    for i, tab in enumerate(tabs):
        with tab:
            if i < len(st.session_state.all_data):
                data = st.session_state.all_data[i]
                etf_info = ALL_WEATHER_ETFS[i]
                
                # 가격 차트
                fig_price = go.Figure()
                fig_price.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['Close'],
                        mode='lines',
                        name=f"{etf_info['symbol']} 종가",
                        line=dict(color='green')
                    )
                )
                
                fig_price.update_layout(
                    title=f"{etf_info['symbol']} - {etf_info['name']} (비중: {etf_info['allocation']}%)",
                    xaxis_title="날짜",
                    yaxis_title="가격 ($)"
                )
                
                st.plotly_chart(fig_price, use_container_width=True)
                
                # 최근 데이터
                st.write("**최근 10일 데이터:**")
                display_data = data.tail(10)[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                display_data.index = display_data.index.strftime('%Y-%m-%d')
                st.dataframe(display_data, use_container_width=True)
    
    # 데이터 다운로드
    st.subheader("💾 데이터 다운로드")
    
    # 모든 데이터를 하나의 DataFrame으로 합치기
    combined_data = pd.concat(st.session_state.all_data, ignore_index=False)
    combined_data = combined_data.reset_index()
    
    # 날짜 컬럼 처리
    if 'Date' in combined_data.columns:
        combined_data['Date'] = pd.to_datetime(combined_data['Date']).dt.strftime('%Y-%m-%d')
    elif 'index' in combined_data.columns:
        combined_data['Date'] = pd.to_datetime(combined_data['index']).dt.strftime('%Y-%m-%d')
        combined_data = combined_data.drop('index', axis=1)
    else:
        combined_data['Date'] = pd.to_datetime(combined_data.index).strftime('%Y-%m-%d')
    
    # 컬럼 순서 정렬
    available_columns = ['Date', 'Symbol', 'Name', 'Open', 'High', 'Low', 'Close', 'Volume', 'Allocation', 'Category']
    columns_order = [col for col in available_columns if col in combined_data.columns]
    combined_data = combined_data[columns_order]
    
    # 데이터 미리보기
    st.write("**다운로드할 데이터 미리보기:**")
    st.dataframe(combined_data.head(20), use_container_width=True)
    
    # CSV 다운로드 버튼
    csv_buffer = io.StringIO()
    combined_data.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_data = csv_buffer.getvalue()
    
    current_date = datetime.now().strftime('%Y%m%d')
    filename = f"ray_dalio_all_weather_portfolio_{current_date}.csv"
    
    st.download_button(
        label="📥 올웨더 포트폴리오 데이터 다운로드",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        type="primary"
    )
    
    # 포트폴리오 성과 데이터 다운로드
    if 'portfolio_returns' in st.session_state:
        performance_data = pd.DataFrame({
            'Date': st.session_state.portfolio_cumulative.index.strftime('%Y-%m-%d'),
            'Daily_Return': st.session_state.portfolio_returns.values,
            'Cumulative_Return': st.session_state.portfolio_cumulative.values
        })
        
        performance_csv = io.StringIO()
        performance_data.to_csv(performance_csv, index=False, encoding='utf-8-sig')
        performance_csv_data = performance_csv.getvalue()
        
        st.download_button(
            label="📊 포트폴리오 성과 데이터 다운로드",
            data=performance_csv_data,
            file_name=f"all_weather_performance_{current_date}.csv",
            mime="text/csv"
        )

else:
    st.info("👈 왼쪽 사이드바에서 '데이터 가져오기' 버튼을 클릭하여 시작하세요!")
    
    # 사용법 및 설명
    st.markdown("""
    ## 🎯 레이달리오 올웨더 포트폴리오란?
    
    **브리지워터 어소시에이츠**의 창립자 **레이 달리오**가 개발한 **"모든 날씨를 견딜 수 있는"** 포트폴리오입니다.
    
    ### 🧠 핵심 철학
    - **4계절 이론**: 경제는 성장/침체, 인플레이션/디플레이션의 4가지 상태를 순환
    - **리스크 패리티**: 각 자산이 포트폴리오에 동등한 리스크를 기여
    - **분산 투자**: 상관관계가 낮은 자산들의 조합으로 안정적 수익 추구
    
    ### 📊 포트폴리오 구성
    
    | 자산 | 비중 | 역할 |
    |------|------|------|
    | **장기 채권 (TLT)** | 40% | 경기 침체 시 방어 + 디플레이션 대응 |
    | **주식 (SPY)** | 30% | 경제 성장 시 수익 창출 |
    | **중기 채권 (IEI)** | 15% | 안정적 수익 + 금리 리스크 분산 |
    | **금 (GLD)** | 7.5% | 인플레이션 헤지 + 위기 시 안전자산 |
    | **상품 (DBC)** | 7.5% | 인플레이션 헤지 + 실물자산 |
    
    ### 🎯 투자 목표
    - **절대 수익**: 시장 상황에 관계없이 안정적 수익
    - **낮은 변동성**: 리스크 조정 수익률 극대화
    - **긴 투자 시계**: 장기적 관점에서 복리 효과 추구
    
    ### ⚠️ 주의사항
    - 이 포트폴리오는 **보수적**이고 **안정적**인 투자 전략입니다
    - 단기적으로는 주식 시장 대비 저조한 성과를 보일 수 있습니다
    - 개인의 투자 목표와 리스크 성향을 고려하여 투자하세요
    """)

# 푸터
st.markdown("---")
st.markdown("""
⚠️ **면책 조항**: 이 애플리케이션은 교육 및 연구 목적으로만 사용하세요. 
투자 결정은 항상 전문가와 상담 후 본인의 판단에 따라 하시기 바랍니다.
""")
