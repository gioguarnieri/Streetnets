import io

import streamlit as st
import osmnx as ox
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium

from streetnets_app import metrics
from streetnets_app.config import deep_analysis_enabled
from streetnets_app.data import CITY_LIST, load_city_edges, load_city_nodes, load_examples_stats
from streetnets_app.plots import stats_violin

if not deep_analysis_enabled():
    # Belt and braces: the router doesn't register this page on hosted
    # deployments, but stop hard in case it is ever reached anyway.
    st.error("Deep Analysis is disabled on this hosted deployment — its computations are too "
             "heavy for a shared server. Install StreetNets locally (`pip install streetnets`) "
             "to use it on your own machine.")
    st.stop()

DB_AREA_M2 = float((2 * 4000) ** 2)  # 8x8 km, the database convention
MAX_MAP_FEATURES = 30_000

st.title("🔬 Deep Analysis")
st.write(
    "Research-grade metrics on a street network: centrality, orientation, "
    "vulnerability, and comparison against the 18-city database. Heavy "
    "computations run locally on your machine."
)


@st.cache_resource(show_spinner=False)
def load_db_graph(city):
    nodes = load_city_nodes(city)
    edges = load_city_edges(city)
    return metrics.graph_from_city_gdfs(nodes, edges)


# --- Source selection -------------------------------------------------------

source = st.radio("Analyze:", ["My retrieved network", "A database city"], horizontal=True)

if source == "My retrieved network":
    retrieved = st.session_state.get("retrieved")
    if not retrieved or "graph" not in retrieved:
        st.info("No retrieved network in this session yet. Retrieve an area first, then come back.")
        st.page_link("pages/Retrieve_city_data.py", label="Retrieve city data", icon="📊")
        st.stop()
    G_full = retrieved["graph"]
    area_m2 = retrieved["area_m2"]
    network_type = retrieved["network_type"]
    source_token = retrieved["token"]
    source_label = "your retrieved area"
else:
    city = st.selectbox("Database city:", CITY_LIST)
    try:
        with st.spinner(f"Loading {city}..."):
            G_full = load_db_graph(city)
    except Exception as e:
        st.error(f"Could not rebuild the {city} graph from the database files: {e}")
        st.stop()
    area_m2 = DB_AREA_M2
    network_type = "drive"
    source_token = f"db:{city}"
    source_label = city

# --- Preparation ------------------------------------------------------------

scc_on = st.toggle(
    "Reduce to largest strongly connected component",
    value=True,
    help="Matches the database methodology and makes closeness well-defined. "
         "Recommended for all centrality computations.",
)


@st.cache_resource(show_spinner=False)
def prepared_graph(token, scc, _G):
    """Working graph + aligned GeoDataFrames, cached per (source, SCC) choice."""
    G_work = metrics.largest_scc(_G) if scc else _G
    nodes_work, edges_work = ox.graph_to_gdfs(G_work)
    return G_work, nodes_work, edges_work


G_work, nodes_work, edges_work = prepared_graph(source_token, scc_on, G_full)
if scc_on:
    dropped_n = G_full.number_of_nodes() - G_work.number_of_nodes()
    dropped_m = G_full.number_of_edges() - G_work.number_of_edges()
    if dropped_n or dropped_m:
        st.caption(f"SCC reduction dropped {dropped_n:,} nodes and {dropped_m:,} edges.")

n, m = G_work.number_of_nodes(), G_work.number_of_edges()

# Size guard for the heavy computations
heavy_ok = True
if m > 150_000:
    st.warning(
        f"This network has {m:,} edges. Exact betweenness and the robustness curve "
        "may take tens of minutes and significant memory."
    )
    heavy_ok = st.checkbox("I understand — enable the heavy computations anyway")
elif m > 50_000:
    st.warning(
        f"This network has {m:,} edges — betweenness and the robustness curve "
        "may take several minutes."
    )


def memo(name, fn):
    """Session-scoped result cache keyed by (source, SCC flag, metric name)."""
    store = st.session_state.setdefault("deep_results", {})
    key = (source_token, scc_on, name)
    if key not in store:
        store[key] = fn()
    return store[key]


def memo_get(name):
    return st.session_state.get("deep_results", {}).get((source_token, scc_on, name))


def sampled(gdf):
    if len(gdf) > MAX_MAP_FEATURES:
        return gdf.sample(MAX_MAP_FEATURES, random_state=0), True
    return gdf, False


tab_centrality, tab_orientation, tab_vuln, tab_compare = st.tabs(
    ["Centrality & structure", "Orientation", "Vulnerability", "Compare to database"]
)

# --- Tab 1: Centrality & structure ------------------------------------------

with tab_centrality:
    kansky = memo("kansky", lambda: metrics.kansky_indices(n, m))
    pr_max, pr_min = memo("pagerank", lambda: metrics.pagerank_minmax(G_work))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nodes", f"{n:,}")
    c2.metric("Edges", f"{m:,}")
    c3.metric("PageRank max", f"{pr_max:.2e}")
    c4.metric("PageRank min", f"{pr_min:.2e}")
    k1, k2, k3, _ = st.columns(4)
    k1.metric("Alpha (α)", f"{kansky['Alpha']:.4f}", help="(m−n+1)/(2n−5) — cyclomatic connectivity, 0–1")
    k2.metric("Beta (β)", f"{kansky['Beta']:.4f}", help="m/n — edges per node")
    k3.metric("Gamma (γ)", f"{kansky['Gamma']:.4f}", help="m/3(n−2) — fraction of possible planar links")

    st.divider()
    if st.button("Compute betweenness & closeness", type="primary", disabled=not heavy_ok):
        with st.status("Computing centralities...", expanded=True) as status:
            st.write("Edge betweenness (length-weighted, database methodology)...")
            memo("betweenness", lambda: metrics.edge_betweenness(G_work))
            st.write("Closeness centrality...")
            memo("closeness", lambda: metrics.closeness(G_work))
            status.update(label="Centralities computed", state="complete", expanded=False)

    bt = memo_get("betweenness")
    cl = memo_get("closeness")
    if bt is not None:
        edges_plot = edges_work.copy()
        edges_plot["Edge Betweenness"] = bt
        if not scc_on:
            st.caption("Note: on graphs that are not strongly connected, closeness follows "
                       "igraph's convention (no reachable-fraction scaling).")

        map_edges, was_sampled = sampled(edges_plot)
        if was_sampled:
            st.info(f"Showing a random sample of {MAX_MAP_FEATURES:,} of {len(edges_plot):,} "
                    "segments on the map.")
        st.write("#### Edge betweenness map")
        tooltip = [c for c in ["name", "length", "highway", "Edge Betweenness"] if c in map_edges.columns]
        m_bt = map_edges.explore(column="Edge Betweenness", cmap="plasma", tooltip=tooltip)
        st_folium(m_bt, width="100%", height=450, key="bt_map", returned_objects=[])

        h1, h2 = st.columns(2)
        with h1:
            st.write("#### Betweenness distribution")
            st.plotly_chart(px.histogram(edges_plot, x="Edge Betweenness", nbins=60, log_y=True),
                            use_container_width=True)
        with h2:
            st.write("#### Closeness distribution")
            st.plotly_chart(px.histogram(cl.rename("closeness"), x="closeness", nbins=60),
                            use_container_width=True)

# --- Tab 2: Orientation -----------------------------------------------------

with tab_orientation:
    st.write("The street **orientation entropy** measures how spread out street bearings are: "
             "a perfect grid concentrates bearings in a few directions (low entropy); an "
             "organically grown network spreads them evenly (high entropy, max ≈ 3.58 for 36 bins).")

    if st.button("Compute orientation"):
        def _orientation():
            entropy, Gu = metrics.orientation_entropy_stats(G_work)
            fig, ax = ox.plot.plot_orientation(Gu)
            ax.set_title("")
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            import matplotlib.pyplot as plt
            plt.close(fig)
            return entropy, buf.getvalue()

        with st.spinner("Computing bearings..."):
            memo("orientation", _orientation)

    result = memo_get("orientation")
    if result is not None:
        entropy, png = result
        oc1, oc2 = st.columns([1, 2])
        oc1.metric("Orientation entropy", f"{entropy:.3f}",
                   help="Shannon entropy of edge bearings across 36 bins. "
                        "≈1.39 for a perfect grid, ≈3.58 for uniformly spread bearings.")
        oc2.image(png, caption=f"Street orientation compass — {source_label}")

# --- Tab 3: Vulnerability ---------------------------------------------------

with tab_vuln:
    st.write("#### Simulate a disruption")
    st.write("Draw a polygon or rectangle over the area to block (flood, closure, works). "
             "Every street segment intersecting it is removed, and connectivity is recomputed.")

    map_edges, was_sampled = sampled(edges_work)
    center = [map_edges.geometry.union_all().centroid.y, map_edges.geometry.union_all().centroid.x]
    m_draw = folium.Map(location=center, zoom_start=13)
    folium.GeoJson(
        map_edges[["geometry"]].__geo_interface__,
        style_function=lambda x: {"color": "#94a3b8", "weight": 1},
    ).add_to(m_draw)
    Draw(draw_options={"polyline": False, "polygon": True, "rectangle": True,
                       "circle": False, "marker": False, "circlemarker": False},
         edit_options={"edit": True, "remove": True}).add_to(m_draw)
    draw_state = st_folium(m_draw, width="100%", height=420, key="disrupt_map",
                           returned_objects=["all_drawings"])

    if st.button("Simulate disruption", type="primary"):
        drawings = (draw_state or {}).get("all_drawings") or []
        if not drawings:
            st.error("Draw a polygon on the map first.")
        else:
            from shapely.geometry import shape
            poly = shape(drawings[-1]["geometry"])
            with st.spinner("Recomputing connectivity..."):
                res = metrics.polygon_disruption(G_work, edges_work, poly)
            st.session_state.deep_results[(source_token, scc_on, "disruption")] = res

    res = memo_get("disruption")
    if res is not None:
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Segments removed", f"{int(res.removed_mask.sum()):,}")
        d2.metric("Street length removed", f"{res.removed_length_m/1000:,.1f} km")
        d3.metric("Connected components", f"{res.after['n_weak']:,}",
                  delta=res.after["n_weak"] - res.before["n_weak"], delta_color="inverse")
        d4.metric("Nodes cut off from main network", f"{res.unreachable_fraction:.1%}")

        if res.removed_mask.any():
            giant_label = res.node_component.value_counts().idxmax()
            off_nodes = set(res.node_component.index[res.node_component != giant_label])
            kept = edges_work[~res.removed_mask]
            disconnected = kept[
                kept.index.get_level_values("u").isin(off_nodes)
                | kept.index.get_level_values("v").isin(off_nodes)
            ]
            removed = edges_work[res.removed_mask]

            base, _ = sampled(kept)
            m_res = base[["geometry"]].explore(color="#94a3b8", name="Intact")
            if len(disconnected):
                disconnected[["geometry"]].explore(m=m_res, color="orange", name="Disconnected")
            removed[["geometry"]].explore(m=m_res, color="red", name="Removed")
            folium.LayerControl().add_to(m_res)
            st_folium(m_res, width="100%", height=450, key="disrupt_result_map",
                      returned_objects=[])

    st.divider()
    st.write("#### Robustness curve")
    st.write("How fast does the network fall apart as streets are removed? Compares a targeted "
             "attack (highest-betweenness streets first) against random failures.")

    rc1, rc2, rc3 = st.columns(3)
    max_frac = rc1.slider("Max fraction removed", 0.1, 0.9, 0.5, 0.1)
    n_random = rc2.slider("Random baseline runs", 1, 5, 3)
    seed = rc3.number_input("Random seed", value=0, step=1)

    if st.button("Compute robustness curve", disabled=not heavy_ok):
        import numpy as np
        fractions = np.linspace(0.0, max_frac, 26)

        def _curves():
            ranking = memo("betweenness", lambda: metrics.edge_betweenness(G_work))
            targeted = metrics.robustness_curve(G_work, ranking=ranking,
                                                fractions=fractions, strategy="betweenness")
            randoms = [
                metrics.robustness_curve(G_work, fractions=fractions,
                                         strategy="random", seed=int(seed) + i)
                for i in range(int(n_random))
            ]
            rnd = pd.concat(randoms).groupby("fraction_removed", as_index=False).agg(
                giant_component_fraction=("giant_component_fraction", "mean"))
            rnd["strategy"] = "random (mean)"
            return pd.concat([targeted, rnd], ignore_index=True)

        with st.status("Computing robustness curves...", expanded=False):
            curves = _curves()
        st.session_state.deep_results[(source_token, scc_on, "robustness")] = curves

    curves = memo_get("robustness")
    if curves is not None:
        fig = px.line(curves, x="fraction_removed", y="giant_component_fraction",
                      color="strategy", markers=True,
                      labels={"fraction_removed": "Fraction of edges removed",
                              "giant_component_fraction": "Largest component (fraction of nodes)"})
        st.plotly_chart(fig, use_container_width=True)
        st.caption("A targeted attack on high-betweenness streets typically collapses the network "
                   "far faster than random failures — the gap measures dependence on a few "
                   "critical corridors.")

# --- Tab 4: Compare to database ---------------------------------------------

with tab_compare:
    st.write("Computes the same statistics as the 18-city database "
             "(same methodology) and places this network among them.")
    if network_type != "drive":
        st.warning(f"This is a '{network_type}' network; the database cities are drive networks, "
                   "so the comparison is indicative only.")
    if source == "My retrieved network":
        if retrieved["aoi"].get("method") == "point":
            st.caption(f"Density metrics use the (2·dist)² area convention: {area_m2/1e6:.1f} km².")
        else:
            st.caption(f"Density metrics use your area of interest, projected: {area_m2/1e6:.1f} km².")

    if st.button("Compare", type="primary"):
        with st.spinner("Computing database-comparable statistics..."):
            memo("stats_row", lambda: metrics.stats_row(G_work, area_m2))

    row = memo_get("stats_row")
    if row is not None:
        stats_df = load_examples_stats()
        table = metrics.percentile_table(row, stats_df)
        st.dataframe(
            table.style.format({"Your area": "{:.4g}", "DB min": "{:.4g}",
                                "DB median": "{:.4g}", "DB max": "{:.4g}",
                                "Percentile": "{:.0f}%"}),
            use_container_width=True,
        )
        st.write("#### Where this network sits in the database distribution")
        st.plotly_chart(stats_violin(stats_df, highlight=row, highlight_name=source_label))
        st.caption("Red diamonds mark this network. Values outside the violin range mean it "
                   "falls outside the 18-city database for that metric.")
