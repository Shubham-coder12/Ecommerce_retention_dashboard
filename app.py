from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
from datetime import datetime, timedelta

app = FastAPI()

def generate_mock_data():
    """Generates synthetic e-commerce data."""
    np.random.seed(42)
    n_customers = 1000
    n_orders = 5000
    
    customer_ids = np.random.randint(1000, 1000+n_customers, n_orders)
    start_date = datetime.today() - timedelta(days=365)
    order_dates = [start_date + timedelta(days=int(np.random.randint(0, 365))) for _ in range(n_orders)]
    order_values = np.random.lognormal(mean=4.0, sigma=1.0, size=n_orders)
    
    df = pd.DataFrame({
        'CustomerID': customer_ids,
        'OrderDate': pd.to_datetime(order_dates),
        'Revenue': order_values
    })
    
    snapshot_date = df['OrderDate'].max() + timedelta(days=1)
    
    # Calculate RFM metrics
    rfm = df.groupby('CustomerID').agg({
        'OrderDate': lambda x: (snapshot_date - x.max()).days,
        'CustomerID': 'count',
        'Revenue': 'sum'
    }).rename(columns={'OrderDate': 'Recency', 'CustomerID': 'Frequency', 'Revenue': 'Monetary'})
    
    def segment_customer(row):
        if row['Recency'] <= 30 and row['Frequency'] > 5: return 'Champion'
        elif row['Recency'] > 90 and row['Frequency'] == 1: return 'Churned'
        elif row['Recency'] > 60 and row['Frequency'] >= 3: return 'At Risk'
        else: return 'Average'

    rfm['Segment'] = rfm.apply(segment_customer, axis=1)
    return df, rfm

@app.get("/", response_class=HTMLResponse)
def render_dashboard():
    df, rfm = generate_mock_data()
    
    # 1. Create the Pie Chart
    segment_counts = rfm['Segment'].value_counts().reset_index()
    segment_counts.columns = ['Segment', 'Count']
    fig_pie = px.pie(segment_counts, values='Count', names='Segment', hole=0.4, 
                     color_discrete_sequence=px.colors.sequential.Teal,
                     title="Customer Segments Distribution")
    
    # 2. Create the Scatter Plot
    fig_scatter = px.scatter(rfm, x='Recency', y='Monetary', color='Segment',
                             size='Frequency', hover_data=['Frequency'],
                             labels={'Recency': 'Days Since Last Purchase', 'Monetary': 'Total Spent ($)'},
                             title="Recency vs. Monetary Value")

    # Convert Plotly figures to HTML strings
    # We include the Plotly JS library in the first chart, and omit it in the second to save space
    pie_html = pio.to_html(fig_pie, full_html=False, include_plotlyjs='cdn')
    scatter_html = pio.to_html(fig_scatter, full_html=False, include_plotlyjs=False)

    # 3. Build the final HTML page
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>E-Commerce Retention Dashboard</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f8f9fa; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; }}
            .metrics {{ display: flex; justify-content: space-around; background: #f1f3f5; padding: 15px; border-radius: 8px; margin-bottom: 30px; }}
            .metric-box {{ text-align: center; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #00796b; }}
            .metric-label {{ font-size: 14px; color: #666; text-transform: uppercase; }}
            .charts {{ display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }}
            .chart-container {{ flex: 1; min-width: 400px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 E-Commerce Retention & RFM Dashboard</h1>
            
            <div class="metrics">
                <div class="metric-box">
                    <div class="metric-value">{len(rfm):,}</div>
                    <div class="metric-label">Total Customers</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">${rfm['Monetary'].mean():.2f}</div>
                    <div class="metric-label">Avg Lifetime Value</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{rfm['Frequency'].mean():.1f}</div>
                    <div class="metric-label">Avg Purchase Freq</div>
                </div>
            </div>

            <div class="charts">
                <div class="chart-container">{pie_html}</div>
                <div class="chart-container">{scatter_html}</div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content
