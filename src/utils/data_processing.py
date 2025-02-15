import pandas as pd
import os

def transform_data(input_path, output_path):
    """Transforma los datos y realiza la interpolación para el año 2015."""
    try:
        df = pd.read_excel(input_path)
    except FileNotFoundError:
        print(f"Error: Archivo no encontrado en {input_path}")
        return

    # Limpieza y filtrado 
    df = df[df['Grupo quinquenal de edad'] != 'Total']
    df = df[df['Entidad federativa'] != 'Estados Unidos Mexicanos']
    df.drop(columns=['Total.1', 'Total.2', 'Total.3', 'Total.4', 'Total.5', 'Total'], axis=1, errors='ignore', inplace=True)  

    fixed_columns = ['Entidad federativa', 'Grupo quinquenal de edad']

    df_hombres = pd.melt(df, id_vars=fixed_columns, value_vars=[col for col in df.columns if col.startswith('Hombres')], var_name='Género', value_name='Cantidad')
    df_hombres['Género'] = 'Hombres'

    df_mujeres = pd.melt(df, id_vars=fixed_columns, value_vars=[col for col in df.columns if col.startswith('Mujeres')], var_name='Género', value_name='Cantidad')
    df_mujeres['Género'] = 'Mujeres'

    df_year = pd.melt(df, id_vars=fixed_columns, value_vars=[col for col in df.columns if col.startswith('Año')], var_name='Año', value_name='Año_valor')
    df_year['Año_valor'] = df_year['Año_valor'].astype(str)
    df_year['Año'] = df_year['Año_valor'].str.extract('(\d{4})').astype(int)
    df_year.drop(columns=['Año_valor'], inplace=True)  

   
    df_hombres['temp_index'] = df_hombres.groupby(fixed_columns).cumcount()
    df_mujeres['temp_index'] = df_mujeres.groupby(fixed_columns).cumcount()
    df_year['temp_index'] = df_year.groupby(fixed_columns).cumcount()

    df_hombres = pd.merge(df_hombres, df_year, on=fixed_columns + ['temp_index'], how='left')
    df_mujeres = pd.merge(df_mujeres, df_year, on=fixed_columns + ['temp_index'], how='left')

    df_hombres.drop(columns=['temp_index'], inplace=True)  
    df_mujeres.drop(columns=['temp_index'], inplace=True)  

    df_final = pd.concat([df_hombres, df_mujeres], ignore_index=True)
    df_final = df_final[['Entidad federativa', 'Grupo quinquenal de edad', 'Género', 'Año', 'Cantidad']]

   
    df_final = clean_text_columns(df_final)

    # Interpolación lineal
    df_final = df_final.set_index(['Entidad federativa', 'Grupo quinquenal de edad', 'Género'])

    def interpolar(grupo):
        if 2015 not in grupo['Año'].values:
            año_2010 = grupo[grupo['Año'] == 2010].iloc[0]
            año_2020 = grupo[grupo['Año'] == 2020].iloc[0]

            cantidad_2010 = año_2010['Cantidad']
            cantidad_2020 = año_2020['Cantidad']

            cantidad_2015 = cantidad_2010 + (cantidad_2020 - cantidad_2010) * (2015 - 2010) / (2020 - 2010)

            nueva_fila = año_2010.copy()
            nueva_fila['Año'] = 2015
            nueva_fila['Cantidad'] = int(round(cantidad_2015))

            grupo = pd.concat([grupo, pd.DataFrame([nueva_fila])], ignore_index=True)
            grupo = grupo.sort_values('Año')
        return grupo

    df_final = df_final.groupby(level=[0, 1, 2]).apply(interpolar).reset_index(level=[0, 1, 2])
    df_final = df_final.reset_index(drop=True)

    try:
        df_final.to_excel(output_path, index=False)
        print(f"Datos transformados y guardados en {output_path}")
    except Exception as e:
        print(f"Error al guardar el archivo: {e}")


def clean_text_columns(df):
    df['Entidad federativa'] = df['Entidad federativa'].str.normalize('NFKD')\
                                                      .str.encode('ascii', errors='ignore')\
                                                      .str.decode('utf-8')\
                                                      .str.upper()
    return df

if __name__ == '__main__':
    input_path = os.path.join("data", "raw_data", "Poblacion_02.xlsx")
    output_path = os.path.join("data", "processed_data", "archivo_transformado.xlsx")
    transform_data(input_path, output_path)