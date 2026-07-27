"""Shared Plotly figures used by more than one page. Streamlit-free."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def stats_violin(df: pd.DataFrame, highlight: pd.Series | None = None,
                 highlight_name: str = "Your area") -> go.Figure:
    """Violin plots of every stats column, min-max normalized per column.

    ``highlight`` (a Series with the same metric names, e.g. a user-retrieved
    area's stats row) is overlaid as red diamonds, normalized with the *same*
    per-column min/max as ``df`` — values outside [0, 1] mean the area falls
    outside the database range, which is meaningful and allowed.
    """
    dmin, dmax = df.min(), df.max()
    span = (dmax - dmin).replace(0, 1.0)
    normalized = (df - dmin) / span

    fig = go.Figure()
    for column in normalized.columns:
        fig.add_trace(
            go.Violin(
                y=normalized[column],
                name=column,
                box_visible=True,
                meanline_visible=True,
                spanmode="hard",
                points="all",
                hovertext=df.index.astype(str),
                hoverinfo="text",
                showlegend=False,
            )
        )

    if highlight is not None:
        cols = [c for c in normalized.columns if c in highlight.index and pd.notna(highlight[c])]
        y = [(highlight[c] - dmin[c]) / span[c] for c in cols]
        fig.add_trace(
            go.Scatter(
                x=cols,
                y=y,
                mode="markers",
                name=highlight_name,
                marker=dict(symbol="diamond", size=14, color="red",
                            line=dict(width=1, color="black")),
                hovertext=[f"{c}: {highlight[c]:.4g}" for c in cols],
                hoverinfo="text",
                showlegend=True,
            )
        )

    fig.update_layout(
        violingap=0.30,
        violingroupgap=0,
        violinmode="overlay",
        width=1500,
        height=600,
        font_size=20,
        margin=dict(l=20, r=20, t=45, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig
