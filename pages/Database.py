import io

import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

from streetnets_app.data import CITY_LIST, load_city_edges, load_examples_stats


@st.cache_data(show_spinner=False)
def load_edges(city):
    """Load one city's edges with only the columns this page needs."""
    return load_city_edges(city, columns=["length", "Edge Betweenness", "Groups", "geometry"])


@st.cache_data(show_spinner=False)
def load_stats():
    return load_examples_stats()


@st.cache_data(show_spinner=False)
def group_maps_png(city, column):
    """Render the per-group street maps as a PNG, cached per (city, metric)."""
    edges = load_edges(city)
    vmin, vmax = edges[column].min(), edges[column].max()
    cmap = plt.cm.jet
    fig, axs = plt.subplots(2, 2, figsize=(20, 20), constrained_layout=True)
    for group, ax in zip(["A", "B", "C"], [axs[0, 0], axs[0, 1], axs[1, 0]]):
        edges_group = edges[edges["Groups"] == group].sort_values(by=column)
        edges_group.plot(
            ax=ax,
            column=column,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            linewidth=edges_group[column] / vmax * 8,
        )
        ax.set_title(f"Group {group}")
    edges_sorted = edges.sort_values(by=column)
    edges_sorted.plot(
        ax=axs[1, 1],
        column=column,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        linewidth=edges_sorted[column] / vmax * 8,
    )
    axs[1, 1].set_title("All groups")
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    cbar = plt.colorbar(sm, ax=axs[:], orientation="horizontal")
    cbar.set_label(label=column, size=30)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def stats_violin(df):
    fig = go.Figure()
    for column in df.columns:
        fig.add_trace(
            go.Violin(
                y=df[column],
                name=column,
                box_visible=True,
                meanline_visible=True,
                spanmode="hard",
                points="all",
                hovertext=df.index.astype(str),
                hoverinfo="text",
            )
        )
    fig.update_layout(
        violingap=0.30,
        violingroupgap=0,
        violinmode="overlay",
        width=1500,
        height=600,
        font_size=20,
        showlegend=False,
        margin=dict(l=20, r=20, t=45, b=0),
    )
    return fig


st.title("🗺️ City Database")
st.write("Explore pre-calculated statistics and maps for 18 example cities.")

city = st.selectbox("Select a city:", CITY_LIST)

all_stats = load_stats()
stats = all_stats.loc[city]

with st.spinner(f"Loading {city}..."):
    edges = load_edges(city)

dist = 4000
size_edges = len(edges)
size_nodes = int(stats["n"])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Street segments", f"{size_edges:,}")
m2.metric("Intersections / dead ends", f"{size_nodes:,}")
m3.metric("Avg. street length", f"{stats['street_length_avg']:.1f} m")
m4.metric("Circuity", f"{stats['circuity_avg']:.3f}")

st.write(f"""
{city} downtown region has {size_edges} street segments and {size_nodes} intersections/dead ends,
within a {2*dist/1000:.0f}x{2*dist/1000:.0f}km area, where each intersection connects {stats["k_avg"]:.2f} streets in average.

The average street length in meters is {stats["street_length_avg"]:.2f}m, with a density of {stats["street_density_km"]:.2f}m/km².

The city has {stats["intersection_density_km"]:.2f} intersections per km², and a circuity of {stats["circuity_avg"]:.2f}
""")

st.markdown("## [Groups](Glossary#groups)")
group_counts = edges["Groups"].value_counts()
fig_groups = px.pie(
    values=group_counts.values,
    names=group_counts.index,
    color_discrete_sequence=px.colors.qualitative.Set1,
)
st.plotly_chart(fig_groups)
st.caption("A = highways & trunks · B = arterial streets (primary/secondary/tertiary) · C = local streets")
st.page_link("pages/Glossary.py", label="What do these groups mean?", icon="📖")

st.markdown("## Maps")
column = st.selectbox("Select the desired metric:", ["length", "Edge Betweenness"])
with st.spinner("Rendering maps..."):
    st.image(group_maps_png(city, column))

st.markdown("## All cities stats")

df_cut = load_stats()
# normalize the data to better visualize it
normalized_df = (df_cut - df_cut.min()) / (df_cut.max() - df_cut.min())

st.plotly_chart(stats_violin(normalized_df))

st.dataframe(df_cut)
