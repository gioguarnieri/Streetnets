import streamlit as st
import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import quote


st.set_page_config(
    page_title="Streetnets",
    page_icon="🛣️",
)

st.title("Streetnets")

st.sidebar.success("Select an analysis above.")

def get_Graph(path, city, gh = False):
    edges = city + "_edges.csv"
    nodes = city + "_nodes.csv"
    if gh:
        nodes, edges = pd.read_csv(path + quote(nodes), index_col =[0]), pd.read_csv(path + quote(edges), index_col = [0,1,2])
    else:
        nodes, edges = pd.read_csv(path + nodes, index_col =[0]), pd.read_csv(path + edges, index_col = [0,1,2])
    
    # edges = edges[~edges[column].isna()]
    others = ["crossing", "living_street", "unclassified", "disused", "busway", "escape", "road", "ladder"]
    edges["highway"] = edges.highway.map(lambda x: "other" if x  in others else x)
    # edges[column] = edges[column]fillna(0)
    s = gpd.GeoSeries.from_wkt(nodes.geometry)
    nodes = gpd.GeoDataFrame(data = nodes, geometry = s)
    nodes = nodes.set_crs('epsg:4326', allow_override=True)
    s = gpd.GeoSeries.from_wkt(edges.geometry)
    edges = gpd.GeoDataFrame(data = edges, geometry = s)
    edges = edges.set_crs('epsg:4326', allow_override=True)

    G = ox.graph_from_gdfs(nodes, edges)
    H = nx.MultiDiGraph()
    H.add_nodes_from(sorted(G.nodes(data=True)))
    H.add_edges_from(G.edges(data=True))
    H.graph["crs"] = G.graph["crs"]
    nodes, edges = ox.graph_to_gdfs(H)
    return H, nodes, edges

# st.write(pd.__version__)

st.write("### Showing cities")
city_list_full = ["São Paulo", # 0
                  "Rio de Janeiro", # 1
                  "Atlanta", # 2
                  "Manhattan", # 3
                  "Barcelona", # 4
                  "Madrid", # 5
                  "Buenos Aires", # 6 
                  "London", # 7
                  "Beijing", # 8
                  "Paris", # 9
                  "Cardiff", # 10
                  "Berlin", # 11
                  "Amsterdam", # 12
                  "São José dos Campos", # 13
                  "Los Angeles", # 14
                  "Wichita", # 15
                  "Toulouse", # 16
                  "Salt Lake", # 17
                  ]


# path_gh = 'https://raw.githubusercontent.com/gioguarnieri/Streetnets/refs/heads/main/csv/'
path_gh = "./csv/"


if "dict_database" not in st.session_state:
    dict_database = {}
    print("in")
    for city in city_list_full:
        G, nodes, edges = get_Graph(path_gh, city)
        dict_database[city] = {"City name": city, "Graph": G, "Nodes": nodes, "Edges": edges}
    st.session_state.dict_database = dict_database
    del(dict_database, nodes, edges)
city = st.selectbox("Select a city:", city_list_full)

size_edges = len(st.session_state.dict_database[city]["Edges"])

st.write(f'Group A: {sum(st.session_state.dict_database[city]["Edges"]["Groups"] == "A")/size_edges*100:.2f}\% \
         Group B: {sum(st.session_state.dict_database[city]["Edges"]["Groups"] == "B")/size_edges*100:.2f}\%  \
         Group C: {sum(st.session_state.dict_database[city]["Edges"]["Groups"] == "C")/size_edges*100:.2f}\% \
         ')


column = st.selectbox("Select the desired column:", ["length", "Edge Betweenness"])
vmin = min(st.session_state.dict_database[city]["Edges"][column])
vmax = max(st.session_state.dict_database[city]["Edges"][column])
cmap=plt.cm.jet
fig, axs = plt.subplots(2, 2, figsize = (20,20), constrained_layout=True)
for group,ax in zip(['C','B','A',],[axs[1,0],axs[0,1], axs[0,0]]):
    edges_group = st.session_state.dict_database[city]["Edges"][st.session_state.dict_database[city]["Edges"]["Groups"] == group].sort_values(by = column, ascending=True)
    edges_group.plot(ax = ax, column = column, cmap = cmap, vmin = vmin, vmax = vmax, linewidth = edges_group[column]/vmax*8)
    ax.set_title(f'Group {group}')
st.session_state.dict_database[city]["Edges"].sort_values(by = column, ascending=True).plot(ax = axs[1,1], column = column, cmap = cmap, linewidth = st.session_state.dict_database[city]["Edges"][column].sort_values(ascending=True)/vmax*8)
axs[1,1].set_title(f'All groups')
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin = vmin, vmax=vmax))
cbar = plt.colorbar(sm, ax = axs[:], orientation='horizontal', label = column)
cbar.set_label(label=column, size = 30)
st.pyplot(fig)
