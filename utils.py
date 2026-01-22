import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import List, Dict

def create_skill_gap_pie(similarity: float):
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        values=[similarity, max(0, 100 - similarity)],
        labels=['Match', 'Gap'],
        hole=0.6,
        marker_colors=['#6366f1', '#f1f5f9'],
        textinfo='none',
        hoverinfo='label+value+percent',
        showlegend=False
    ))
    
    fig.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=160,
        width=160,
        annotations=[
            dict(
                text=f'<b>{similarity}%</b><br><span style="font-size:8px">Similarity</span>',
                x=0.5, y=0.5,
                font_size=16,
                showarrow=False,
                font_color='#6366f1'
            )
        ]
    )
    
    return fig

def create_performance_pie_chart(attendance_data: List[Dict]):
    if not attendance_data:
        return go.Figure()
    
    scores = [entry['score'] for entry in attendance_data if entry['score']]
    
    excellent = sum(1 for s in scores if s >= 8)
    good = sum(1 for s in scores if 6 <= s < 8)
    average = sum(1 for s in scores if 4 <= s < 6)
    poor = sum(1 for s in scores if s < 4)
    
    categories = ['Excellent (8-10)', 'Good (6-8)', 'Average (4-6)', 'Poor (<4)']
    values = [excellent, good, average, poor]
    colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444']
    
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        labels=categories,
        values=values,
        hole=0.4,
        marker_colors=colors,
        textinfo='label+percent',
        hoverinfo='value+percent'
    ))
    
    fig.update_layout(
        height=300,
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=30, b=20, l=20, r=20)
    )
    
    return fig

def create_score_velocity_chart(attendance_data: List[Dict]):
    if not attendance_data:
        return go.Figure()
    
    dates = [entry['date'] for entry in attendance_data][-15:]
    scores = [entry['score'] for entry in attendance_data][-15:]
    
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'scatter'}, {'type': 'domain'}]],
        subplot_titles=("Score Velocity", "Performance Distribution")
    )
    
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=scores,
            mode='lines+markers',
            name='Scores',
            line=dict(color='#6366f1', width=3),
            marker=dict(size=8, color='#6366f1'),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)'
        ),
        row=1, col=1
    )
    
    if len(scores) > 1:
        import numpy as np
        x_numeric = list(range(len(scores)))
        z = np.polyfit(x_numeric, scores, 1)
        p = np.poly1d(z)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=p(x_numeric),
                mode='lines',
                name='Trend',
                line=dict(color='#ef4444', width=2, dash='dash')
            ),
            row=1, col=1
        )
    
    categories = ['Excellent (8-10)', 'Good (6-8)', 'Average (4-6)', 'Poor (<4)']
    excellent = sum(1 for s in scores if s >= 8)
    good = sum(1 for s in scores if 6 <= s < 8)
    average = sum(1 for s in scores if 4 <= s < 6)
    poor = sum(1 for s in scores if s < 4)
    values = [excellent, good, average, poor]
    colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444']
    
    fig.add_trace(
        go.Pie(
            labels=categories,
            values=values,
            hole=0.4,
            marker_colors=colors,
            textinfo='label+percent',
            hoverinfo='value+percent'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=50, b=20, l=20, r=20)
    )
    
    fig.update_xaxes(title_text="Session Date", row=1, col=1)
    fig.update_yaxes(title_text="Score", range=[0, 10], row=1, col=1)
    
    return fig

def create_performance_analysis_chart(attendance_data: List[Dict], performance_metrics: Dict):
    if not attendance_data:
        return go.Figure()
    
    dates = [entry['date'] for entry in attendance_data][-10:]
    scores = [entry['score'] for entry in attendance_data][-10:]
    durations = [entry['duration'] for entry in attendance_data][-10:]
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Score Trend Over Time",
            "Session Duration",
            "Performance Distribution",
            "Performance Metrics"
        ),
        specs=[
            [{'type': 'scatter'}, {'type': 'bar'}],
            [{'type': 'histogram'}, {'type': 'indicator'}]
        ]
    )
    
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=scores,
            mode='lines+markers',
            name='Scores',
            line=dict(color='#6366f1', width=2),
            marker=dict(size=8)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=dates,
            y=durations,
            name='Duration (min)',
            marker_color='#10b981',
           
