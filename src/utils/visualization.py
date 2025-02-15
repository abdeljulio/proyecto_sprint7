import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error


plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
sns.set_style("whitegrid")

def plot_population_by_gender_age(df, key_suffix=""):
    """Gráfico de barras de población por género y grupo de edad."""
    st.subheader("Población por Género y Grupo de Edad")

    orden_quinquenal = [
        '0 a 4 años', '5 a 9 años', '10 a 14 años', '15 a 19 años',
        '20 a 24 años', '25 a 29 años', '30 a 34 años', '35 a 39 años',
        '40 a 44 años', '45 a 49 años', '50 a 54 años', '55 a 59 años',
        '60 a 64 años', '65 a 69 años', '70 a 74 años', '75 a 79 años',
        '80 a 84 años', '85 a 89 años', '90 a 94 años', '95 a 99 años',
        '100 y más años', 'No especificado'
    ]

    try:  
        if 'Año' in df.columns:
            available_years = sorted(df['Año'].unique())
            selected_year = st.selectbox(
                "Seleccionar año",
                options=available_years,
                index=len(available_years)-1,
                key=f"year_select_{key_suffix}"
            )
            df_filtered = df[df['Año'] == selected_year]
        else:
            df_filtered = df

        if df_filtered.empty:
            st.warning("No hay datos disponibles para los filtros seleccionados")
            return

        df_filtered['Grupo quinquenal de edad'] = pd.Categorical(
            df_filtered['Grupo quinquenal de edad'],
            categories=orden_quinquenal,
            ordered=True
        )

        grouped_df = df_filtered.groupby(['Género', 'Grupo quinquenal de edad'])['Cantidad']\
                              .sum()\
                              .reset_index()

        fig, ax = plt.subplots(figsize=(14, 7))
        sns.barplot(
            data=grouped_df,
            x='Grupo quinquenal de edad',
            y='Cantidad',
            hue='Género',
            order=orden_quinquenal,
            ax=ax
        )

        ax.set_title(
            f"Distribución por Género y Edad ({selected_year if 'Año' in df.columns else 'Total'})",
            pad=20,
            fontsize=14
        )
        ax.set_xlabel("Grupo Quinquenal de Edad", fontsize=12)
        ax.set_ylabel("Población Total", fontsize=12)
        plt.xticks(rotation=90, ha='center')
        plt.legend(title='Género', bbox_to_anchor=(1.05, 1), loc='upper left')

        for p in ax.patches:
            ax.annotate(
                f"{int(p.get_height()):,}",
                (p.get_x() + p.get_width()/2, p.get_height()),
                ha='center', va='center',
                xytext=(0, 5),
                textcoords='offset points',
                fontsize=8
            )

        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error al generar el gráfico: {e}")

def plot_population_trend(df, key_suffix=""):
    """Gráfico de tendencia temporal con selector de rango de años."""
    st.subheader("Evolución Temporal de la Población")

    if 'Año' not in df.columns:
        st.warning("No hay datos temporales disponibles")
        return

    try:  
        min_year = int(df['Año'].min())
        max_year = int(df['Año'].max())

        selected_years = st.slider(
            "Seleccionar rango de años",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year),
            key=f"year_range_{key_suffix}"
        )

        df_filtered = df[(df['Año'] >= selected_years[0]) & (df['Año'] <= selected_years[1])]
        trend_df = df_filtered.groupby(['Año', 'Género'])['Cantidad'].sum().reset_index()

        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(
            data=trend_df,
            x='Año',
            y='Cantidad',
            hue='Género',
            style='Género',
            markers=True,
            dashes=False,
            linewidth=2,
            ax=ax
        )

        ax.set_title(f"Tendencia Poblacional ({selected_years[0]}-{selected_years[1]})", pad=20)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        plt.xticks(rotation=45)
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error al generar el gráfico: {e}")

def plot_population_by_state(df, key_suffix=""):
    """Gráfico de barras horizontales para población por estado."""
    st.subheader("Distribución por Entidad Federativa")

    try:  
        use_log = st.checkbox(
            "Usar escala logarítmica",
            key=f"log_scale_{key_suffix}"
        )

        state_data = df.groupby('Entidad federativa')['Cantidad']\
                    .sum()\
                    .sort_values(ascending=False)\
                    .reset_index()

        fig, ax = plt.subplots(figsize=(14, 10))
        sns.barplot(
            x='Cantidad',
            y='Entidad federativa',
            data=state_data,
            orient='h',
            palette="viridis",
            ax=ax
        )

        if use_log:
            ax.set_xscale('log')
            ax.set_xlabel("Población (Escala Logarítmica)")
        else:
            ax.set_xlabel("Población Total")

        for p in ax.patches:
            width = p.get_width()
            ax.annotate(
                f'{width:,.0f}',
                (width * 1.02, p.get_y() + p.get_height()/2),
                va='center',
                fontsize=8
            )

        ax.set_title("Distribución por Estado", pad=20)
        ax.set_ylabel("")
        plt.tight_layout()
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error al generar el gráfico: {e}")

def plot_population_scatter(df, key_suffix=""):
    """Gráfico de dispersión comparando población por género."""
    st.subheader("Relación Poblacional Hombres vs Mujeres")

    try:  
        log_scale = st.checkbox(
            "Usar escala logarítmica",
            key=f"log_scatter_{key_suffix}"
        )

        pivot_df = df.groupby(['Entidad federativa', 'Género'])['Cantidad']\
                   .sum()\
                   .unstack()\
                   .fillna(0)

        fig, ax = plt.subplots(figsize=(10, 8))
        sns.scatterplot(
            data=pivot_df,
            x='Hombres',
            y='Mujeres',
            s=100,
            alpha=0.7,
            edgecolor='k',
            ax=ax
        )
        max_val = max(pivot_df.max().max(), 1)
        ax.plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label="Línea de Referencia") # Added label

        if log_scale:
            ax.set_xscale('log')
            ax.set_yscale('log')

        ax.set_title("Correlación por Género", pad=20)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.legend() 
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error al generar el gráfico: {e}")


def plot_population_pie(df, key_suffix=""):
    """Gráfico de distribución por género con selector de año."""
    st.subheader("Distribución por Género")

    try:  
        if 'Año' in df.columns:
            selected_year = st.selectbox(
                "Seleccionar año",
                options=sorted(df['Año'].unique()),
                key=f"pie_year_{key_suffix}"
            )
            df_filtered = df[df['Año'] == selected_year]
        else:
            df_filtered = df

        gender_data = df_filtered.groupby('Género')['Cantidad'].sum()

        if gender_data.empty:
            st.warning("No hay datos disponibles")
            return

        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(
            gender_data,
            labels=gender_data.index,
            autopct=lambda p: f'{p:.1f}%\n({p*sum(gender_data)/100:,.0f})',
            startangle=90,
            wedgeprops={'width': 0.3, 'edgecolor': 'w'},
            colors=['#66b3ff', '#ffcc99'],
            textprops={'fontsize': 12}
        )

        ax.set_title(
            f"Distribución por Género ({selected_year if 'Año' in df.columns else 'Total'})",
            pad=20
        )
        plt.legend(
            wedges,
            gender_data.index,
            title="Género",
            loc="center left",
            bbox_to_anchor=(1, 0.5)
        )
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error al generar el gráfico: {e}")

def forecast_population_quinquenal(df, key_suffix=""):
    """Pronóstico quinquenal usando regresión lineal."""
    st.subheader("Pronóstico Poblacional")

    try:  
        if 'Año' not in df.columns:
            st.warning("Se requieren datos temporales")
            return

        if len(df['Año'].unique()) < 3:
            st.warning("Se necesitan mínimo 3 periodos (15 años)")
            return

        historical = df.groupby('Año')['Cantidad'].sum().reset_index()
        min_year = historical['Año'].min()
        historical['Periodo'] = (historical['Año'] - min_year) // 5

        if not all(historical['Año'].diff().dropna() % 5 == 0):
            st.error("Los datos no son quinquenales")
            return

        model = LinearRegression()
        model.fit(historical[['Periodo']], historical['Cantidad'])

        last_period = historical['Periodo'].max()
        forecast_year = historical['Año'].max() + 5
        forecast_value = model.predict([[last_period + 1]])[0]

        fig, ax = plt.subplots(figsize=(10, 6))

        sns.lineplot(
            x=historical['Año'],
            y=historical['Cantidad'],
            marker='o',
            label='Histórico',
            ax=ax
        )

        ax.scatter(
            [forecast_year],
            [forecast_value],
            color='red',
            s=100,
            label='Pronóstico 2025'
        )

        ax.set_title("Proyección Quinquenal", pad=20)
        ax.set_xlabel("Año")
        ax.set_ylabel("Población Total")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1e6:.2f}M"))
        ax.legend()
        ax.grid(True, alpha=0.3)

        st.pyplot(fig)

        y_pred = model.predict(historical[['Periodo']])
        mae = mean_absolute_error(historical['Cantidad'], y_pred)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Pronóstico 2025", f"{forecast_value:,.0f}")
        with col2:
            st.metric("Error Medio Absoluto", f"{mae:,.0f}")

    except Exception as e:
        st.error(f"Error al generar el gráfico: {e}")