import streamlit as st
import pandas as pd
import geopandas as gpd
import zipfile

st.title("Download dataframes")

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

def convert_df_to_csv(df):
    return df.to_csv().encode('utf-8')

bools_checkbox = []
col1, col2 = st.columns(2)
with col1:
    for city in city_list_full:
        bools_checkbox.append(st.checkbox(city))

with col2:
    with zipfile.ZipFile('cities.zip', 'x') as csv_zip:
                    count = 0
                    for i in bools_checkbox:
                        if i:
                            csv_zip.writestr(city_list_full[count]+ "_nodes.csv", convert_df_to_csv(st.session_state.dict_database[city_list_full[count]]["Nodes"]))
                            csv_zip.writestr(city_list_full[count]+ "_edges.csv", convert_df_to_csv(st.session_state.dict_database[city_list_full[count]]["Edges"]))
                        count+=1
                        
                    with open("cities.zip", "rb") as file:
                        st.download_button(
                            label = "Download zip",
                            data = file,
                            file_name = "cities.zip",
                            mime = 'application/zip'
                    
                        )

#     csv_nodes = convert_df_to_csv(st.session_state.dict_database[city]["Nodes"].drop(columns=['geometry']))
#     csv_edges = convert_df_to_csv(st.session_state.dict_database[city]["Edges"].drop(columns=['geometry']))
#     col1, col2 = st.columns(2)
#     with col1:
#         st.download_button(
#             label=f"Download {city} Nodes Data",
#             data=csv_nodes,
#             file_name=f'{city}_nodes_stats.csv',
#             mime='text/csv',
#         )
#     with col2:
#         st.download_button(
#             label=f"Download {city} Edges Data",
#             data=csv_edges,
#             file_name=f'{city}_edges_stats.csv',
#             mime='text/csv',
#         )