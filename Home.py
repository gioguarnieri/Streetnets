import streamlit as st
import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import quote
import plotly.express as px
import json
import plotly.graph_objects as go
import plotly
import re

st.set_page_config(
    page_title="Streetnets",
    page_icon="🛣️",
    layout = "wide",
)

st.title("Streetnets")

