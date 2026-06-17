import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="销售数据分析看板", page_icon="📊", layout="wide")


@st.cache_resource
def get_engine():
    """获取 SQLite 数据库连接"""
    db_path = '/mount/src/streamlit-board/sales_data.db' if os.path.exists('/mount/src') else 'sales_data.db'
    return create_engine(f'sqlite:///{db_path}')


@st.cache_data
def get_data_info():
    """获取数据的日期范围和可用渠道"""
    engine = get_engine()
    try:
        info = pd.read_sql("""
                           SELECT MIN(order_date)                as min_date,
                                  MAX(order_date)                as max_date,
                                  GROUP_CONCAT(DISTINCT channel) as channels
                           FROM orders
                           """, engine)
        return {
            'min_date': info['min_date'].iloc[0],
            'max_date': info['max_date'].iloc[0],
            'channels': info['channels'].iloc[0].split(',') if info['channels'].iloc[0] else ['app', 'h5', 'pc']
        }
    except:
        return {'min_date': None, 'max_date': None, 'channels': ['app', 'h5', 'pc']}


@st.cache_data(ttl=300)
def load_data(start_date, end_date, channels):
    """加载数据"""
    engine = get_engine()
    channel_str = ','.join([f"'{c}'" for c in channels])
    sql = f"""
    SELECT 
        order_date, channel,
        COUNT(DISTINCT order_id) as order_cnt,
        SUM(amount) as gmv,
        COUNT(DISTINCT user_id) as user_cnt,
        AVG(amount) as avg_order_value
    FROM orders
    WHERE order_date BETWEEN '{start_date}' AND '{end_date}'
        AND channel IN ({channel_str})
    GROUP BY order_date, channel
    ORDER BY order_date
    """
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


def show_metrics(df):
    """显示核心指标"""
    col1, col2, col3, col4 = st.columns(4)
    total_gmv = df['gmv'].sum()
    total_orders = df['order_cnt'].sum()
    total_users = df['user_cnt'].sum()
    avg_price = total_gmv / total_orders if total_orders > 0 else 0

    col1.metric("总 GMV", f"¥{total_gmv / 10000:.1f}万")
    col2.metric("总订单数", f"{total_orders:,}")
    col3.metric("总用户数", f"{total_users:,}")
    col4.metric("客单价", f"¥{avg_price:.0f}")


def show_trend_chart(df):
    """显示双轴趋势图"""
    daily = df.groupby('order_date', as_index=False).agg({'gmv': 'sum', 'order_cnt': 'sum'})
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily['order_date'], y=daily['order_cnt'], name='订单数', yaxis='y',
                             line=dict(color='steelblue', width=2), marker=dict(size=6)))
    fig.add_trace(go.Scatter(x=daily['order_date'], y=daily['gmv'] / 10000, name='GMV (万元)', yaxis='y2',
                             line=dict(color='coral', width=2), marker=dict(size=6)))
    fig.update_layout(
        title='订单数 & GMV 趋势',
        xaxis=dict(title='日期'),
        yaxis=dict(title='订单数', title_font=dict(color='steelblue'), tickfont=dict(color='steelblue')),
        yaxis2=dict(title='GMV (万元)', title_font=dict(color='coral'), tickfont=dict(color='coral'),
                    overlaying='y', side='right'),
        legend=dict(x=0.02, y=0.98), height=450, hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)


def show_channel_analysis(df):
    """显示渠道分析"""
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🥧 渠道 GMV 占比")
        channel_gmv = df.groupby('channel')['gmv'].sum().reset_index()
        fig = px.pie(channel_gmv, values='gmv', names='channel', hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📊 渠道 GMV 趋势")
        fig = px.line(df, x='order_date', y='gmv', color='channel', markers=True,
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(xaxis_title='日期', yaxis_title='GMV', height=400, legend_title='渠道')
        st.plotly_chart(fig, use_container_width=True)


def main():
    st.title("📊 销售数据分析看板")
    st.markdown("---")

    # 获取数据信息
    info = get_data_info()
    max_date = info['max_date']
    min_date = info['min_date']
    all_channels = info['channels']

    # 默认日期：优先当天，若无数据则回退到数据最大日期
    today = datetime.now().date()
    default_end = today - timedelta(days=1)  # 默认昨天
    # 如果当天没有数据（即数据最大日期 < 昨天），使用数据最大日期
    if max_date and pd.to_datetime(max_date).date() < default_end:
        default_end = pd.to_datetime(max_date).date()

    default_start = default_end - timedelta(days=30)

    # 侧边栏筛选
    st.sidebar.header("🔍 筛选条件")

    # 显示数据范围
    if min_date and max_date:
        st.sidebar.caption(f"📅 数据范围：{min_date} 至 {max_date}")

    date_range = st.sidebar.date_input(
        "日期范围",
        value=(default_start, default_end),
        min_value=pd.to_datetime(min_date).date() if min_date else None,
        max_value=pd.to_datetime(max_date).date() if max_date else None
    )

    channels = st.sidebar.multiselect("渠道", options=all_channels, default=all_channels)

    # 校验
    if len(date_range) != 2 or not channels:
        st.warning("请选择完整的日期范围和至少一个渠道")
        return

    start_date, end_date = date_range[0].strftime('%Y-%m-%d'), date_range[1].strftime('%Y-%m-%d')

    # 加载数据
    with st.spinner("数据加载中..."):
        df = load_data(start_date, end_date, channels)

    if df.empty:
        st.warning("⚠️ 所选日期范围内暂无数据，请调整日期范围")
        return

    # 展示内容
    show_metrics(df)
    st.markdown("---")
    show_trend_chart(df)
    show_channel_analysis(df)

    # 数据明细
    st.markdown("---")
    with st.expander("📋 查看数据明细"):
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 下载 CSV", data=csv,
                           file_name=f"sales_data_{start_date}_{end_date}.csv", mime="text/csv")


if __name__ == "__main__":
    main()