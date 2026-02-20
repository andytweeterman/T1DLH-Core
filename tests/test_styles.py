import sys
import os
import pandas as pd
import plotly.graph_objects as go
import pytest

# Add parent directory to path to import styles
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import styles

def test_render_sparkline_return_type():
    data = pd.Series([1, 2, 3, 2, 1])
    line_color = '#FF0000'
    fig = styles.render_sparkline(data, line_color)
    assert isinstance(fig, go.Figure)

def test_render_sparkline_layout():
    data = pd.Series([1, 2, 3])
    line_color = '#00FF00'
    fig = styles.render_sparkline(data, line_color)

    assert fig.layout.height == 40
    assert fig.layout.margin.l == 0
    assert fig.layout.margin.r == 0
    assert fig.layout.margin.t == 0
    assert fig.layout.margin.b == 0
    assert fig.layout.xaxis.visible is False
    assert fig.layout.yaxis.visible is False
    assert fig.layout.plot_bgcolor == 'rgba(0,0,0,0)'
    assert fig.layout.paper_bgcolor == 'rgba(0,0,0,0)'

def test_render_sparkline_data():
    data = pd.Series([10, 20, 15], index=['a', 'b', 'c'])
    line_color = '#0000FF'
    fig = styles.render_sparkline(data, line_color)

    trace = fig.data[0]
    assert list(trace.x) == ['a', 'b', 'c']
    assert list(trace.y) == [10, 20, 15]
    assert trace.mode == 'lines'
    assert trace.line.width == 2
    assert trace.hoverinfo == 'skip'

def test_render_sparkline_color():
    data = pd.Series([1, 2, 3])
    line_color = '#123456'
    fig = styles.render_sparkline(data, line_color)

    trace = fig.data[0]
    assert trace.line.color == '#123456'

def test_render_sparkline_empty_data():
    data = pd.Series([], dtype=float)
    line_color = '#000000'
    fig = styles.render_sparkline(data, line_color)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert len(fig.data[0].x) == 0
    assert len(fig.data[0].y) == 0
