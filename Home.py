import streamlit as st
import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Streetnets",
    page_icon="🛣️",
    layout = "wide",
)

st.title("Streetnets")

