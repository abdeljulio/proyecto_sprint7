import pandas as pd
import sys
from pathlib import Path
import os
import streamlit as st
from utils.data_processing import transform_data
from utils.visualization import (
    plot_population_by_gender_age,
    plot_population_trend,
    plot_population_by_state,
    plot_population_scatter,
    plot_population_pie,
    forecast_population_quinquenal,
    forecast_prophet,
    plot_clusters
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

    # ========== CONFIGURACIÓN DE IA ==========
    st.sidebar.header("⚙️ Configuración de IA")
    forecast_years = st.sidebar.slider("Años a pronosticar", 1, 10, 5)
    n_clusters = st.sidebar.selectbox("Número de clusters", [2,3,4,5], index=1)

    # ========== FILTROS GLOBALES ==========
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

    # ========== FILTRADO DE DATOS ==========
    df_filtered = df[df['Año'] == selected_year]
    if selected_states:
        df_filtered = df_filtered[df_filtered['Entidad federativa'].isin(selected_states)]

    # ========== LAYOUT PRINCIPAL ==========
    st.title(" Dashboard Demográfico")
    
    # Primera fila de gráficos
    col1, col2 = st.columns([2, 1])
    with col1:
        plot_population_by_gender_age(df_filtered, key_suffix="main")
    with col2:
        plot_population_pie(df_filtered, key_suffix="main")

    # Sección expandible
    with st.expander("🧠 Análisis con Inteligencia Artificial", expanded=True):
        tab1, tab2, tab3, tab_ai = st.tabs(["Tendencia", "Estados", "Comparativa", "IA"])
        
        with tab1:
            plot_population_trend(df, key_suffix="detail")
        
        with tab2:
            plot_population_by_state(df_filtered, key_suffix="detail")
        
        with tab3:
            plot_population_scatter(df_filtered, key_suffix="detail")

        with tab_ai:
            st.header("Insights Automatizados")
            
            # En tu app.py (asegúrate de recibir la figura correctamente)

    
            # Subsección de Clustering
            st.subheader("🧩 Agrupamiento de Estados")
            cluster_year = st.selectbox("Selecciona el año para clustering:", sorted(df['Año'].unique()))
            st.plotly_chart(plot_clusters(df, cluster_year, n_clusters), use_container_width=True)
            
            # Subsección de Forecasting
            st.subheader("🔮 Pronóstico de Población")
            if selected_states:
                st.plotly_chart(forecast_prophet(df, selected_states, forecast_years), use_container_width=True)
            else:
                st.warning("Selecciona estados en el sidebar para generar pronósticos")

            st.subheader("🔮 Pronóstico de Población")
            if selected_states:
                fig = forecast_prophet(df, selected_states, forecast_years)
                st.plotly_chart(fig, use_container_width=True)