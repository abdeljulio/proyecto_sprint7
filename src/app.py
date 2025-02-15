import pandas as pd
import sys
from pathlib import Path
import logging
from utils.data_processing import transform_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Obtiene la ruta raíz del proyecto de manera confiable."""
    current_script = Path(__file__).absolute()
    return current_script.parent.parent  

def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza texto en columnas categóricas."""
    try:
        df['Entidad federativa'] = (
            df['Entidad federativa']
            .str.normalize('NFKD')
            .str.encode('ascii', errors='ignore')
            .str.decode('utf-8')
            .str.upper()
            .str.strip()
        )
        
        df['Grupo quinquenal de edad'] = (
            df['Grupo quinquenal de edad']
            .str.replace(r'\s+', ' ', regex=True)
            .str.strip()
        )
        
        return df
    except Exception as e:
        logger.error(f"Error en limpieza de texto: {str(e)}")
        raise

def transform_data(input_path: Path, output_path: Path) -> None:
    """Transforma los datos y realiza interpolación para 2015."""
    try:
        
        logger.info(f"Leyendo archivo: {input_path}")
        df = pd.read_excel(
            input_path,
            engine='openpyxl',
            dtype={'Total': 'Int64'}
        )
        
       
        required_columns = {'Entidad federativa', 'Grupo quinquenal de edad', 'Hombres_2010'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise ValueError(f"Columnas faltantes en el archivo: {missing}")

        
        logger.info("Iniciando transformación de datos...")
        
        
        df = df[
            (df['Grupo quinquenal de edad'] != 'Total') &
            (df['Entidad federativa'] != 'Estados Unidos Mexicanos')
        ].copy()

        
        columns_to_drop = [col for col in df.columns if col.startswith('Total')]
        df.drop(columns=columns_to_drop, errors='ignore', inplace=True)

       
        fixed_columns = ['Entidad federativa', 'Grupo quinquenal de edad']
        
        def melt_data(df: pd.DataFrame, gender: str) -> pd.DataFrame:
            return pd.melt(
                df,
                id_vars=fixed_columns,
                value_vars=[col for col in df.columns if col.startswith(gender)],
                var_name='Género',
                value_name='Cantidad'
            ).assign(Género=gender)

        df_hombres = melt_data(df, 'Hombres')
        df_mujeres = melt_data(df, 'Mujeres')

       
        for df_temp in [df_hombres, df_mujeres]:
            df_temp['temp_index'] = df_temp.groupby(fixed_columns).cumcount()

        
        df_year = pd.melt(
            df,
            id_vars=fixed_columns,
            value_vars=[col for col in df.columns if col.startswith('Año')],
            var_name='Año',
            value_name='Año_valor'
        )
        df_year['Año'] = df_year['Año_valor'].str.extract(r'(\d{4})').astype(int)
        df_year['temp_index'] = df_year.groupby(fixed_columns).cumcount()

     
        df_hombres = pd.merge(
            df_hombres,
            df_year,
            on=fixed_columns + ['temp_index'],
            how='left'
        )
        
        df_mujeres = pd.merge(
            df_mujeres,
            df_year,
            on=fixed_columns + ['temp_index'],
            how='left'
        )


        df_final = pd.concat([df_hombres, df_mujeres], ignore_index=True)
        df_final = df_final[[
            'Entidad federativa',
            'Grupo quinquenal de edad',
            'Género',
            'Año',
            'Cantidad'
        ]]

 
        df_final = clean_text_columns(df_final)


        logger.info("Realizando interpolación para 2015...")
        df_final = df_final.set_index(['Entidad federativa', 'Grupo quinquenal de edad', 'Género'])
        
        def interpolar(grupo):
            if 2015 not in grupo['Año'].values:
                try:
                    año_2010 = grupo[grupo['Año'] == 2010].iloc[0]
                    año_2020 = grupo[grupo['Año'] == 2020].iloc[0]
                    
                    pendiente = (año_2020['Cantidad'] - año_2010['Cantidad']) / 10
                    cantidad_2015 = año_2010['Cantidad'] + pendiente * 5
                    
                    nueva_fila = año_2010.copy()
                    nueva_fila['Año'] = 2015
                    nueva_fila['Cantidad'] = int(round(cantidad_2015))
                    
                    return pd.concat([grupo, pd.DataFrame([nueva_fila])])
                except IndexError:
                    logger.warning(f"No hay datos suficientes para interpolación en grupo: {grupo.name}")
                    return grupo
            return grupo

        df_final = df_final.groupby(level=[0, 1, 2], group_keys=False).apply(interpolar)
        df_final = df_final.reset_index()


        logger.info(f"Guardando resultados en: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_final.to_excel(output_path, index=False, engine='openpyxl')
        
        logger.info("Proceso completado exitosamente!")
        
    except Exception as e:
        logger.error(f"Error crítico durante la transformación: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    try:

        root_dir = get_project_root()
        
        input_path = root_dir / "data" / "raw_data" / "Poblacion_02.xlsx"
        output_path = root_dir / "data" / "processed_data" / "poblacion_procesada.xlsx"


        if not input_path.exists():
            raise FileNotFoundError(f"Archivo de entrada crítico no encontrado en: {input_path}")

        if not input_path.is_file():
            raise IsADirectoryError(f"La ruta de entrada es un directorio, no un archivo: {input_path}")


        transform_data(input_path, output_path)
        
    except Exception as e:
        logger.critical(f"Error no manejado: {str(e)}")
        sys.exit(1)