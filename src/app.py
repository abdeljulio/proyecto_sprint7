import pandas as pd
import sys
from pathlib import Path
import os
import pandas as pd
import streamlit as st
from utils.data_processing import transform_data
from utils.visualization import (
    plot_population_by_gender_age,
    plot_population_trend,
    plot_population_by_state,
    plot_population_scatter,
    plot_population_pie,
    forecast_population_quinquenal
)

@st.cache_data
def load_data(path):
    """Carga los datos procesados con caché."""
    return pd.read_excel(path)

@st.cache_data
def process_data(input_path, output_path):
    """Ejecuta la transformación de datos con caché."""
    if not os.path.exists(input_path):
        st.error(f"Error: Archivo no encontrado en {input_path}")
        st.stop()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    transform_data(input_path, output_path)
    return load_data(output_path)

if __name__ == '__main__':
    current_script = Path(__file__).resolve()
    project_root = current_script.parent.parent  
    
    input_path = project_root / "data" / "raw_data" / "Poblacion_02.xlsx"
    output_path = project_root / "data" / "processed_data" / "archivo_transformado.xlsx"

    try:
        df = process_data(input_path, output_path)
        st.success("Datos cargados exitosamente!")
    except Exception as e:
        st.error(f"Error crítico: {str(e)}")
        st.stop()

    st.sidebar.header("Filtros Globales")
    selected_year = st.sidebar.selectbox(
        "Año",
        sorted(df['Año'].unique()),
        key="global_year"
    )
    
    selected_states = st.sidebar.multiselect(
        "Estados",
        options=df['Entidad federativa'].unique(),
        key="global_states"
    )


    if not selected_states:  
        df_filtered = df  
    else:
        df_filtered = df[
            (df['Año'] == selected_year) &
            (df['Entidad federativa'].isin(selected_states))
        ]


    st.title(" Dashboard Demográfico")
    

    col1, col2 = st.columns([2, 1])
    with col1:
        plot_population_by_gender_age(df_filtered, key_suffix="main")
    with col2:
        plot_population_pie(df_filtered, key_suffix="main")

    with st.expander(" Análisis Detallado", expanded=True):
        tab1, tab2, tab3 = st.tabs(["Tendencia", "Estados", "Comparativa"])
        
        with tab1:
            plot_population_trend(df, key_suffix="detail")
        
        with tab2:
            plot_population_by_state(df_filtered, key_suffix="detail")
        
        with tab3:
            plot_population_scatter(df_filtered, key_suffix="detail")


    st.sidebar.header("Pronóstico")
    if st.sidebar.checkbox("Habilitar proyección", key="forecast_check"):
        forecast_population_quinquenal(df, key_suffix="main")