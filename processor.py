"""
Módulo de procesamiento de archivos Excel para el CRM de Seguros
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime
import config


class FileProcessor:
    """Procesador de archivos de reportes de carriers"""
    
    def __init__(self):
        """Inicializa el procesador"""
        self.carrier_mappings = config.CARRIER_MAPPINGS
    
    def process_file(self, file_path: Path, carrier_name: str) -> Tuple[pd.DataFrame, Dict]:
        """
        Procesa un archivo Excel y lo normaliza según el carrier
        
        Args:
            file_path: Ruta al archivo Excel
            carrier_name: Nombre del carrier (MOLINA, AMBETTER, AETNA, OSCAR)
            
        Returns:
            Tupla con (DataFrame normalizado, diccionario de estadísticas)
        """
        if carrier_name not in self.carrier_mappings:
            raise ValueError(f"Carrier '{carrier_name}' no soportado. Carriers disponibles: {config.AVAILABLE_CARRIERS}")
        
        # Leer el archivo Excel
        df = pd.read_excel(file_path)
        
        # Obtener el mapeo para este carrier
        mapping = self.carrier_mappings[carrier_name]
        
        # Normalizar los datos
        df_normalized = self._normalize_data(df, mapping, carrier_name)
        
        # Calcular estadísticas
        stats = self._calculate_stats(df_normalized, carrier_name)
        
        return df_normalized, stats
    
    def _normalize_data(self, df: pd.DataFrame, mapping: Dict, carrier_name: str) -> pd.DataFrame:
        """
        Normaliza los datos aplicando el mapeo de columnas
        
        Args:
            df: DataFrame original
            mapping: Diccionario de mapeo de columnas
            carrier_name: Nombre del carrier
            
        Returns:
            DataFrame normalizado
        """
        # Crear DataFrame vacío con todas las columnas posibles
        normalized_df = pd.DataFrame()
        
        # Aplicar el mapeo
        for original_col, normalized_col in mapping.items():
            if original_col in df.columns:
                normalized_df[normalized_col] = df[original_col]
        
        # Limpiar datos
        normalized_df = self._clean_data(normalized_df)
        
        # Validar y convertir tipos de datos
        normalized_df = self._convert_datatypes(normalized_df)
        
        return normalized_df
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia los datos: elimina espacios, convierte NaN, etc.
        
        Args:
            df: DataFrame a limpiar
            
        Returns:
            DataFrame limpio
        """
        df_clean = df.copy()
        
        # Eliminar espacios en strings
        for col in df_clean.select_dtypes(include=['object']).columns:
            df_clean[col] = df_clean[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        
        # Reemplazar valores vacíos por None
        df_clean = df_clean.replace({np.nan: None, '': None, 'nan': None})
        
        return df_clean
    
    def _convert_datatypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convierte los tipos de datos apropiadamente
        
        Args:
            df: DataFrame a convertir
            
        Returns:
            DataFrame con tipos correctos
        """
        df_converted = df.copy()
        
        # Convertir fechas
        date_columns = ['payment_date', 'statement_date', 'effective_date']
        for col in date_columns:
            if col in df_converted.columns:
                df_converted[col] = pd.to_datetime(df_converted[col], errors='coerce')
                # Convertir a string en formato ISO para SQLite
                df_converted[col] = df_converted[col].dt.strftime('%Y-%m-%d')
                df_converted[col] = df_converted[col].replace('NaT', None)
        
        # Convertir números
        numeric_columns = ['amount', 'member_count', 'lives', 'override_percentage']
        for col in numeric_columns:
            if col in df_converted.columns:
                df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce')
        
        # Convertir booleanos
        boolean_columns = ['new_to_medicare']
        for col in boolean_columns:
            if col in df_converted.columns:
                # Convertir a booleano de forma segura
                df_converted[col] = df_converted[col].map({
                    True: 1, False: 0, 'True': 1, 'False': 0, 
                    'true': 1, 'false': 0, 'Yes': 1, 'No': 0,
                    'yes': 1, 'no': 0, 1: 1, 0: 0
                })
        
        return df_converted
    
    def _calculate_stats(self, df: pd.DataFrame, carrier_name: str) -> Dict:
        """
        Calcula estadísticas del archivo procesado
        
        Args:
            df: DataFrame procesado
            carrier_name: Nombre del carrier
            
        Returns:
            Diccionario con estadísticas
        """
        stats = {
            'carrier': carrier_name,
            'total_records': len(df),
            'total_amount': df['amount'].sum() if 'amount' in df.columns else 0,
            'avg_amount': df['amount'].mean() if 'amount' in df.columns else 0,
            'unique_policies': df['policy_number'].nunique() if 'policy_number' in df.columns else 0,
            'unique_members': df['member_id'].nunique() if 'member_id' in df.columns else 0,
            'date_range': None,
            'transaction_types': {}
        }
        
        # Rango de fechas
        if 'payment_date' in df.columns:
            valid_dates = pd.to_datetime(df['payment_date'], errors='coerce').dropna()
            if len(valid_dates) > 0:
                stats['date_range'] = {
                    'start': valid_dates.min().strftime('%Y-%m-%d'),
                    'end': valid_dates.max().strftime('%Y-%m-%d')
                }
        
        # Distribución por tipo de transacción
        if 'transaction_type' in df.columns:
            type_counts = df['transaction_type'].value_counts().to_dict()
            stats['transaction_types'] = type_counts
        
        # Distribución por agente asignado
        if 'assigned_agent_name' in df.columns:
            agent_counts = df['assigned_agent_name'].value_counts().to_dict()
            stats['agents'] = agent_counts
        
        return stats
    
    def validate_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Valida que el archivo sea un Excel válido
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Tupla (es_válido, mensaje)
        """
        # Verificar extensión
        if file_path.suffix not in ['.xlsx', '.xls']:
            return False, "El archivo debe ser Excel (.xlsx o .xls)"
        
        # Verificar que existe
        if not file_path.exists():
            return False, "El archivo no existe"
        
        # Intentar leer el archivo
        try:
            df = pd.read_excel(file_path)
            if len(df) == 0:
                return False, "El archivo está vacío"
            return True, "Archivo válido"
        except Exception as e:
            return False, f"Error al leer el archivo: {str(e)}"
    
    def detect_carrier(self, file_path: Path) -> Optional[str]:
        """
        Intenta detectar automáticamente el carrier basado en las columnas
        
        Args:
            file_path: Ruta al archivo Excel
            
        Returns:
            Nombre del carrier detectado o None
        """
        try:
            df = pd.read_excel(file_path)
            columns = set(df.columns)
            
            # Verificar cada mapping
            best_match = None
            max_matches = 0
            
            for carrier, mapping in self.carrier_mappings.items():
                expected_cols = set(mapping.keys())
                matches = len(columns.intersection(expected_cols))
                
                if matches > max_matches:
                    max_matches = matches
                    best_match = carrier
            
            # Requiere al menos 50% de coincidencia
            if best_match and max_matches >= len(self.carrier_mappings[best_match]) * 0.5:
                return best_match
            
            return None
        except Exception:
            return None


# Instancia global del procesador
processor = FileProcessor()


def process_and_save(file_path: Path, carrier_name: str, db_manager) -> Dict:
    """
    Procesa un archivo y lo guarda en la base de datos
    
    Args:
        file_path: Ruta al archivo
        carrier_name: Nombre del carrier
        db_manager: Instancia del gestor de base de datos
        
    Returns:
        Diccionario con el resultado del procesamiento
    """
    try:
        # Validar archivo
        is_valid, message = processor.validate_file(file_path)
        if not is_valid:
            return {
                'success': False,
                'error': message
            }
        
        # Procesar archivo
        df_normalized, stats = processor.process_file(file_path, carrier_name)
        
        # Guardar en base de datos
        records_inserted = db_manager.insert_bulk_commission_reports(
            df_normalized, 
            carrier_name, 
            file_path.name
        )
        
        return {
            'success': True,
            'records_inserted': records_inserted,
            'stats': stats,
            'message': f'✅ {records_inserted} registros de {carrier_name} procesados exitosamente'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error al procesar archivo: {str(e)}'
        }


if __name__ == "__main__":
    # Test básico
    print("Testing File Processor...")
    
    test_file = Path("/mnt/user-data/uploads/MOLINA_COMISIONES_Y_OVERRIDE_2025-08-07.xlsx")
    if test_file.exists():
        print(f"\nProcesando archivo de prueba: {test_file.name}")
        
        # Detectar carrier
        detected = processor.detect_carrier(test_file)
        print(f"Carrier detectado: {detected}")
        
        # Procesar archivo
        df, stats = processor.process_file(test_file, 'MOLINA')
        print(f"\nEstadísticas:")
        print(f"  - Total registros: {stats['total_records']}")
        print(f"  - Total amount: ${stats['total_amount']:,.2f}")
        print(f"  - Columnas normalizadas: {list(df.columns)}")
