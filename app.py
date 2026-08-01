import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ----------------------------------------
# 1. PAGE CONFIGURATION
# ----------------------------------------
st.set_page_config(page_title="E-Commerce Retention Dashboard", layout="wide")
st.title("📊 E-Commerce Customer Retention & RFM Dashboard")
st.markdown("This dashboard analyzes customer churn, retention cohorts, and RFM segments.")

# ----------------------------------------
# 2. DATA GENERATION (Mock Data for Portfolio)
# ----------------------------------------
@st.cache_data
def load_data():
    """Generates synthetic e-commerce data for demonstration."""
    np.random.seed(42)
    n_customers = 1000
    n_orders = 5000
    
    customer_ids = np.random.randint(1000, 1000+n_customers, n_orders)
    # Generate random dates over the last year
    start_date = datetime.today() - timedelta(days=365)
    order_dates = [start_date + timedelta(days=np.random.randint(0, 365)) for _ in range(n_orders)]
    order_values = np.random.lognormal(mean=4.0, sigma=1.0, size=n_orders) # Skewed spending
    
    df = pd.DataFrame({
        'CustomerID': customer_ids,
        'OrderDate': pd.to_datetime(order_dates),
        'Revenue': order_values
    })
    return df

df = load_data()

# ----------------------------------------
# 3. DATA PROCESSING & RFM CALCULATION
# ----------------------------------------
# Set snapshot date to one day after the last transaction
snapshot_date = df['OrderDate'].max() + timedelta(days=1)

# Calculate RFM metrics
rfm = df.groupby('CustomerID').agg({
    'OrderDate': lambda x: (snapshot_date - x.max()).days, # Recency
    'CustomerID': 'count',                                 # Frequency
    'Revenue': 'sum'                                       # Monetary
}).rename(columns={'OrderDate': 'Recency', 'CustomerID': 'Frequency', 'Revenue': 'Monetary'})

# Simple Segmentation Logic
def segment_customer(row):
    if row['Recency'] <= 30 and row['Frequency'] > 5:
        return 'Champion'
    elif row['Recency'] > 90 and row['Frequency'] == 1:
        return 'Churned/One-Off'
    elif row['Recency'] > 60 and row['Frequency'] >= 3:
        return 'At Risk'
    else:
        return 'Average'

rfm['Segment'] = rfm.apply(segment_customer, axis=1)

# ----------------------------------------
# 4. SIDEBAR FILTERS
# ----------------------------------------
st.sidebar.header("Dashboard Filters")
selected_segment = st.sidebar.multiselect(
    "Select Customer Segments",
    options=rfm['Segment'].unique(),
    default=rfm['Segment'].unique()
)

# Apply filter
filtered_rfm = rfm[rfm['Segment'].isin(selected_segment)]

# ----------------------------------------
# 5. KPI METRICS (Top Row)
# ----------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Customers", f"{len(filtered_rfm):,}")
col2.metric("Avg CLV (Monetary)", f"${filtered_rfm['Monetary'].mean():.2f}")
col3.metric("Avg Purchase Freq", f"{filtered_rfm['Frequency'].mean():.1f}")
col4.metric("At-Risk Customers", f"{len(filtered_rfm[filtered_rfm['Segment'] == 'At Risk'])}")

st.divider()

# ----------------------------------------
# 6. VISUALIZATIONS
# ----------------------------------------
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Customer Segments Distribution")
    segment_counts = filtered_rfm['Segment'].value_counts().reset_index()
    segment_counts.columns = ['Segment', 'Count']
    fig_pie = px.pie(segment_counts, values='Count', names='Segment', hole=0.4, 
                     color_discrete_sequence=px.colors.sequential.Teal)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_chart2:
    st.subheader("Recency vs. Monetary Value")
    fig_scatter = px.scatter(filtered_rfm, x='Recency', y='Monetary', color='Segment',
                             size='Frequency', hover_data=['Frequency'],
                             labels={'Recency': 'Days Since Last Purchase', 'Monetary': 'Total Spent ($)'})
    st.plotly_chart(fig_scatter, use_container_width=True)

# Cohort Analysis (Simplified Monthly Revenue)
st.subheader("Monthly Revenue Trend")
df['MonthYear'] = df['OrderDate'].dt.to_period('M').astype(str)
monthly_rev = df.groupby('MonthYear')['Revenue'].sum().reset_index()
fig_line = px.line(monthly_rev, x='MonthYear', y='Revenue', markers=True, 
                   labels={'MonthYear': 'Month', 'Revenue': 'Total Revenue ($)'})
st.plotly_chart(fig_line, use_container_width=True)
