import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="Bitcoin 회귀분석 연구",
    page_icon="₿",
    layout="wide"
)

# 제목 및 소개
st.title("₿ Bitcoin 가격 예측 회귀분석 연구")
st.markdown("---")

# 사이드바 설정
st.sidebar.title("분석 설정")
st.sidebar.markdown("### 데이터 설정")

# 데이터 수집 기간 설정
end_date = datetime.now()
start_date = st.sidebar.date_input(
    "시작 날짜",
    value=end_date - timedelta(days=365*2),
    max_value=end_date
)
end_date = st.sidebar.date_input(
    "종료 날짜",
    value=end_date,
    max_value=end_date
)

# 데이터 로딩 함수
@st.cache_data
def load_bitcoin_data(start, end):
    """Yahoo Finance에서 비트코인 데이터 로드"""
    try:
        btc_data = yf.download('BTC-USD', start=start, end=end)
        return btc_data
    except Exception as e:
        st.error(f"데이터 로딩 중 오류 발생: {e}")
        return None

# 기술적 지표 계산 함수
def calculate_technical_indicators(data):
    """기술적 지표 계산"""
    df = data.copy()
    
    # 이동평균
    df['MA_7'] = df['Close'].rolling(window=7).mean()
    df['MA_21'] = df['Close'].rolling(window=21).mean()
    df['MA_50'] = df['Close'].rolling(window=50).mean()
    
    # 변동성
    df['Volatility'] = df['Close'].rolling(window=21).std()
    
    # RSI 계산 (안전한 처리)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
    # 0으로 나누는 것을 방지
    rs = gain / loss.replace(0, np.nan)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50)  # NaN 값을 50으로 대체
    
    # 볼린저 밴드
    df['BB_Upper'] = df['MA_21'] + (df['Volatility'] * 2)
    df['BB_Lower'] = df['MA_21'] - (df['Volatility'] * 2)
    
    # 가격 변화율
    df['Price_Change'] = df['Close'].pct_change()
    df['Price_Change_7d'] = df['Close'].pct_change(periods=7)
    
    # 거래량 지표 (매우 안전한 처리)
    df['Volume_MA'] = df['Volume'].rolling(window=21).mean()
    # Volume_Ratio를 조건부로 계산
    try:
        volume_ratio = []
        for i in range(len(df)):
            if pd.isna(df['Volume_MA'].iloc[i]) or df['Volume_MA'].iloc[i] == 0:
                volume_ratio.append(1.0)
            else:
                volume_ratio.append(df['Volume'].iloc[i] / df['Volume_MA'].iloc[i])
        df['Volume_Ratio'] = volume_ratio
    except:
        # 계산에 실패하면 모든 값을 1.0으로 설정
        df['Volume_Ratio'] = 1.0
    
    # 무한대 값 처리 (매우 안전한 방법)
    try:
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
    except:
        # 개별 컬럼 처리
        columns_to_check = ['MA_7', 'MA_21', 'MA_50', 'Volatility', 'RSI', 'BB_Upper', 'BB_Lower', 
                           'Price_Change', 'Price_Change_7d', 'Volume_MA', 'Volume_Ratio']
        for col in columns_to_check:
            if col in df.columns:
                df[col] = df[col].replace([np.inf, -np.inf], np.nan)
    
    return df

# 데이터 로딩
with st.spinner("데이터를 로딩하는 중..."):
    btc_data = load_bitcoin_data(start_date, end_date)

if btc_data is not None:
    # 기술적 지표 계산
    btc_data = calculate_technical_indicators(btc_data)
    
    # 메인 대시보드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_price = btc_data['Close'].iloc[-1]
        st.metric("현재 가격", f"${current_price:,.2f}")
    
    with col2:
        price_change = btc_data['Close'].iloc[-1] - btc_data['Close'].iloc[-2]
        change_pct = (price_change / btc_data['Close'].iloc[-2]) * 100
        st.metric("일일 변화", f"${price_change:,.2f}", f"{change_pct:.2f}%")
    
    with col3:
        volatility = btc_data['Volatility'].iloc[-1]
        st.metric("변동성 (21일)", f"{volatility:.2f}")
    
    with col4:
        volume = btc_data['Volume'].iloc[-1]
        st.metric("거래량", f"{volume:,.0f}")
    
    st.markdown("---")
    
    # 탭 생성
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 데이터 탐색", "📈 가격 차트", "🔍 회귀분석", "📋 모델 성능", "📄 연구 결과"])
    
    with tab1:
        st.header("데이터 탐색 및 기초 통계")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("기초 통계량")
            stats_df = btc_data[['Open', 'High', 'Low', 'Close', 'Volume']].describe()
            st.dataframe(stats_df)
        
        with col2:
            st.subheader("상관관계 매트릭스")
            corr_vars = ['Close', 'Volume', 'MA_7', 'MA_21', 'RSI', 'Volatility']
            corr_matrix = btc_data[corr_vars].corr()
            
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax)
            st.pyplot(fig)
        
        st.subheader("최근 데이터 미리보기")
        display_cols = ['Close', 'Volume', 'MA_7', 'MA_21', 'RSI', 'Volatility', 'Price_Change']
        st.dataframe(btc_data[display_cols].tail(10))
    
    with tab2:
        st.header("비트코인 가격 차트 분석")
        
        # 가격 차트
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('가격 및 이동평균', 'RSI', '거래량'),
            vertical_spacing=0.08,
            row_heights=[0.6, 0.2, 0.2]
        )
        
        # 가격 및 이동평균
        fig.add_trace(
            go.Scatter(x=btc_data.index, y=btc_data['Close'], 
                      name='Close Price', line=dict(color='orange')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=btc_data.index, y=btc_data['MA_7'], 
                      name='MA 7', line=dict(color='blue')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=btc_data.index, y=btc_data['MA_21'], 
                      name='MA 21', line=dict(color='red')),
            row=1, col=1
        )
        
        # 볼린저 밴드
        fig.add_trace(
            go.Scatter(x=btc_data.index, y=btc_data['BB_Upper'], 
                      name='BB Upper', line=dict(color='gray', dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=btc_data.index, y=btc_data['BB_Lower'], 
                      name='BB Lower', line=dict(color='gray', dash='dash')),
            row=1, col=1
        )
        
        # RSI
        fig.add_trace(
            go.Scatter(x=btc_data.index, y=btc_data['RSI'], 
                      name='RSI', line=dict(color='purple')),
            row=2, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        # 거래량
        fig.add_trace(
            go.Bar(x=btc_data.index, y=btc_data['Volume'], 
                   name='Volume', marker_color='lightblue'),
            row=3, col=1
        )
        
        fig.update_layout(height=800, title_text="비트코인 기술적 분석")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("회귀분석 모델")
        
        # 특성 선택
        st.subheader("특성 변수 선택")
        feature_options = ['MA_7', 'MA_21', 'MA_50', 'RSI', 'Volatility', 'Volume', 'Volume_Ratio']
        selected_features = st.multiselect(
            "회귀분석에 사용할 특성을 선택하세요:",
            feature_options,
            default=['MA_7', 'MA_21', 'RSI', 'Volatility']
        )
        
        if selected_features:
            # 데이터 전처리
            model_data = btc_data.dropna()
            
            # 특성 변수와 타겟 변수 설정
            X = model_data[selected_features]
            y = model_data['Close']
            
            # 학습/테스트 데이터 분할
            test_size = st.slider("테스트 데이터 비율", 0.1, 0.4, 0.2, 0.05)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, shuffle=False
            )
            
            # 특성 스케일링
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # 모델 학습
            model = LinearRegression()
            model.fit(X_train_scaled, y_train)
            
            # 예측
            y_pred_train = model.predict(X_train_scaled)
            y_pred_test = model.predict(X_test_scaled)
            
            # 결과 표시
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("모델 계수")
                coef_df = pd.DataFrame({
                    'Feature': selected_features,
                    'Coefficient': model.coef_,
                    'Abs_Coefficient': np.abs(model.coef_)
                }).sort_values('Abs_Coefficient', ascending=False)
                st.dataframe(coef_df)
            
            with col2:
                st.subheader("모델 성능 지표")
                train_r2 = r2_score(y_train, y_pred_train)
                test_r2 = r2_score(y_test, y_pred_test)
                train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
                test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
                
                metrics_df = pd.DataFrame({
                    'Metric': ['R²', 'RMSE', 'MAE'],
                    'Train': [
                        train_r2,
                        train_rmse,
                        mean_absolute_error(y_train, y_pred_train)
                    ],
                    'Test': [
                        test_r2,
                        test_rmse,
                        mean_absolute_error(y_test, y_pred_test)
                    ]
                })
                st.dataframe(metrics_df)
            
            # 예측 vs 실제 차트
            st.subheader("예측 결과 시각화")
            
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('학습 데이터', '테스트 데이터'),
                vertical_spacing=0.1
            )
            
            # 학습 데이터
            fig.add_trace(
                go.Scatter(x=y_train.index, y=y_train, name='실제 (Train)', 
                          line=dict(color='blue')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=y_train.index, y=y_pred_train, name='예측 (Train)', 
                          line=dict(color='red')),
                row=1, col=1
            )
            
            # 테스트 데이터
            fig.add_trace(
                go.Scatter(x=y_test.index, y=y_test, name='실제 (Test)', 
                          line=dict(color='blue')),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(x=y_test.index, y=y_pred_test, name='예측 (Test)', 
                          line=dict(color='red')),
                row=2, col=1
            )
            
            fig.update_layout(height=600, title_text="실제 vs 예측 가격")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.header("모델 성능 분석")
        
        if 'model' in locals():
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("잔차 분석")
                residuals = y_test - y_pred_test
                
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
                
                # 잔차 히스토그램
                ax1.hist(residuals, bins=30, alpha=0.7, color='skyblue')
                ax1.set_title('잔차 히스토그램')
                ax1.set_xlabel('잔차')
                ax1.set_ylabel('빈도')
                
                # Q-Q 플롯
                stats.probplot(residuals, dist="norm", plot=ax2)
                ax2.set_title('Q-Q 플롯')
                
                st.pyplot(fig)
            
            with col2:
                st.subheader("예측 정확도 산점도")
                
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.scatter(y_test, y_pred_test, alpha=0.6, color='coral')
                ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
                ax.set_xlabel('실제 가격')
                ax.set_ylabel('예측 가격')
                ax.set_title('예측 vs 실제 가격')
                
                st.pyplot(fig)
            
            # 특성 중요도
            st.subheader("특성 중요도 분석")
            importance_df = pd.DataFrame({
                'Feature': selected_features,
                'Importance': np.abs(model.coef_)
            }).sort_values('Importance', ascending=True)
            
            fig = px.bar(importance_df, x='Importance', y='Feature', 
                        orientation='h', title='특성 중요도')
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("먼저 회귀분석 탭에서 모델을 학습시켜주세요.")
    
    with tab5:
        st.header("연구 결과 요약")
        
        st.markdown("""
        ### 📊 Bitcoin 가격 예측 회귀분석 연구 결과
        
        #### 연구 목적
        - Yahoo Finance 데이터를 활용한 Bitcoin 가격 예측 모델 개발
        - 기술적 지표들의 가격 예측력 분석
        - 회귀분석을 통한 주요 영향 요인 식별
        
        #### 사용된 특성 변수
        - 이동평균선 (MA_7, MA_21, MA_50)
        - 상대강도지수 (RSI)
        - 가격 변동성 (Volatility)
        - 거래량 지표 (Volume, Volume_Ratio)
        
        #### 주요 발견사항
        """)
        
        if 'model' in locals():
            st.markdown(f"""
            - **모델 성능**: 테스트 데이터 R² = {test_r2:.4f}
            - **예측 오차**: RMSE = ${test_rmse:,.2f}
            - **가장 영향력 있는 특성**: {coef_df.iloc[0]['Feature']}
            """)
        
        st.markdown("""
        #### 연구의 한계점
        - 선형 회귀모델의 단순성으로 인한 비선형 패턴 포착 제한
        - 시장 센티먼트, 뉴스 등 외부 요인 미반영
        - 단기 예측에 특화된 모델로 장기 예측 정확도 한계
        
        #### 향후 연구 방향
        - 딥러닝 모델 적용을 통한 성능 개선
        - 감성분석, 소셜미디어 데이터 통합
        - 앙상블 모델을 활용한 예측 안정성 향상
        """)
        
        # 데이터 다운로드
        st.subheader("데이터 다운로드")
        
        col1, col2 = st.columns(2)
        with col1:
            csv_data = btc_data.to_csv()
            st.download_button(
                label="전체 데이터 다운로드 (CSV)",
                data=csv_data,
                file_name=f"bitcoin_data_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        
        with col2:
            if 'model' in locals():
                results_df = pd.DataFrame({
                    'Date': y_test.index,
                    'Actual': y_test.values,
                    'Predicted': y_pred_test
                })
                results_csv = results_df.to_csv(index=False)
                st.download_button(
                    label="예측 결과 다운로드 (CSV)",
                    data=results_csv,
                    file_name=f"prediction_results_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )

else:
    st.error("데이터를 로드할 수 없습니다. 날짜 설정을 확인해주세요.")

# 푸터
st.markdown("---")
st.markdown("*이 애플리케이션은 연구 목적으로 제작되었으며, 투자 조언을 제공하지 않습니다.*")
