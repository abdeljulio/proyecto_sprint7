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
    # Configuración de rutas
    input_path = os.path.join('..', 'data', 'raw_data', 'Poblacion_02.xlsx')
    output_path = os.path.join('..', 'data', 'processed_data', 'archivo_transformado.xlsx')

    try:
        df = process_data(input_path, output_path)
        st.success("Datos cargados exitosamente!")
    except Exception as e:
        st.error(f"Error crítico: {str(e)}")
        st.stop()

    # Filtros globales (sidebar)
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

    # Dataset filtrado (CORRECCIÓN)
    if not selected_states:  # Si no se selecciona ningún estado
        df_filtered = df  # Usa el DataFrame completo
    else:
        df_filtered = df[
            (df['Año'] == selected_year) &
            (df['Entidad federativa'].isin(selected_states))
        ]

    # Layout principal
    st.title(" Dashboard Demográfico")
    
    # Sección principal en columnas
    col1, col2 = st.columns([2, 1])
    with col1:
        plot_population_by_gender_age(df_filtered, key_suffix="main")
    with col2:
        plot_population_pie(df_filtered, key_suffix="main")

    # Secciones adicionales
    with st.expander(" Análisis Detallado", expanded=True):
        tab1, tab2, tab3 = st.tabs(["Tendencia", "Estados", "Comparativa"])
        
        with tab1:
            plot_population_trend(df, key_suffix="detail")
        
        with tab2:
            plot_population_by_state(df_filtered, key_suffix="detail")
        
        with tab3:
            plot_population_scatter(df_filtered, key_suffix="detail")

    # Pronóstico en sidebar
    st.sidebar.header("Pronóstico")
    if st.sidebar.checkbox("Habilitar proyección", key="forecast_check"):
        forecast_population_quinquenal(df, key_suffix="main")