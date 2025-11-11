"""
Módulo de gestión de base de datos para el CRM de Seguros
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import config


class DatabaseManager:
    """Gestor de base de datos SQLite para el CRM"""
    
    def __init__(self, db_path: Path = config.DATABASE_PATH):
        """
        Inicializa el gestor de base de datos
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Obtiene una conexión a la base de datos"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Inicializa la base de datos con el esquema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Ejecutar el esquema
        cursor.executescript(config.DATABASE_SCHEMA)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Base de datos inicializada: {self.db_path}")
    
    def insert_commission_report(self, data: Dict[str, Any]) -> int:
        """
        Inserta un registro de comisión en la base de datos
        
        Args:
            data: Diccionario con los datos normalizados
            
        Returns:
            ID del registro insertado
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO commission_reports ({columns}) VALUES ({placeholders})"
        
        cursor.execute(query, list(data.values()))
        record_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return record_id
    
    def insert_bulk_commission_reports(self, df: pd.DataFrame, carrier_name: str, file_name: str) -> int:
        """
        Inserta múltiples registros de comisión desde un DataFrame
        
        Args:
            df: DataFrame con los datos normalizados
            carrier_name: Nombre del carrier
            file_name: Nombre del archivo original
            
        Returns:
            Número de registros insertados
        """
        conn = self.get_connection()
        
        # Agregar metadatos
        df['carrier_name'] = carrier_name
        df['report_file_name'] = file_name
        df['upload_date'] = datetime.now().isoformat()
        
        # Insertar en la base de datos
        df.to_sql('commission_reports', conn, if_exists='append', index=False)
        
        records_inserted = len(df)
        conn.close()
        
        print(f"✅ {records_inserted} registros insertados para {carrier_name}")
        return records_inserted
    
    def get_all_reports(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Obtiene todos los reportes de comisiones
        
        Args:
            limit: Límite de registros a retornar
            
        Returns:
            DataFrame con los reportes
        """
        conn = self.get_connection()
        
        query = "SELECT * FROM commission_reports ORDER BY upload_date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_reports_by_carrier(self, carrier_name: str) -> pd.DataFrame:
        """
        Obtiene reportes filtrados por carrier
        
        Args:
            carrier_name: Nombre del carrier
            
        Returns:
            DataFrame con los reportes filtrados
        """
        conn = self.get_connection()
        
        query = """
        SELECT * FROM commission_reports 
        WHERE carrier_name = ? 
        ORDER BY upload_date DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(carrier_name,))
        conn.close()
        
        return df
    
    def get_reports_by_agent(self, agent_name: str) -> pd.DataFrame:
        """
        Obtiene reportes filtrados por agente
        
        Args:
            agent_name: Nombre del agente asignado
            
        Returns:
            DataFrame con los reportes filtrados
        """
        conn = self.get_connection()
        
        query = """
        SELECT * FROM commission_reports 
        WHERE assigned_agent_name = ? 
        ORDER BY upload_date DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(agent_name,))
        conn.close()
        
        return df
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas resumidas de las comisiones
        
        Returns:
            Diccionario con las estadísticas
        """
        conn = self.get_connection()
        
        # Total de registros
        total_records = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM commission_reports", 
            conn
        )['count'][0]
        
        # Total de comisiones
        total_amount = pd.read_sql_query(
            "SELECT COALESCE(SUM(amount), 0) as total FROM commission_reports", 
            conn
        )['total'][0]
        
        # Comisiones por tipo
        by_type = pd.read_sql_query("""
            SELECT transaction_type, COUNT(*) as count, SUM(amount) as total
            FROM commission_reports
            WHERE transaction_type IS NOT NULL
            GROUP BY transaction_type
        """, conn)
        
        # Comisiones por carrier
        by_carrier = pd.read_sql_query("""
            SELECT carrier_name, COUNT(*) as count, SUM(amount) as total
            FROM commission_reports
            GROUP BY carrier_name
            ORDER BY total DESC
        """, conn)
        
        # Comisiones por agente
        by_agent = pd.read_sql_query("""
            SELECT assigned_agent_name, COUNT(*) as count, SUM(amount) as total
            FROM commission_reports
            WHERE assigned_agent_name IS NOT NULL
            GROUP BY assigned_agent_name
            ORDER BY total DESC
        """, conn)
        
        conn.close()
        
        return {
            'total_records': total_records,
            'total_amount': total_amount,
            'by_type': by_type,
            'by_carrier': by_carrier,
            'by_agent': by_agent
        }
    
    def get_carriers(self) -> List[str]:
        """
        Obtiene la lista de carriers únicos en la base de datos
        
        Returns:
            Lista de nombres de carriers
        """
        conn = self.get_connection()
        
        df = pd.read_sql_query(
            "SELECT DISTINCT carrier_name FROM commission_reports ORDER BY carrier_name", 
            conn
        )
        
        conn.close()
        
        return df['carrier_name'].tolist()
    
    def get_agents(self) -> List[str]:
        """
        Obtiene la lista de agentes únicos en la base de datos
        
        Returns:
            Lista de nombres de agentes
        """
        conn = self.get_connection()
        
        df = pd.read_sql_query("""
            SELECT DISTINCT assigned_agent_name 
            FROM commission_reports 
            WHERE assigned_agent_name IS NOT NULL
            ORDER BY assigned_agent_name
        """, conn)
        
        conn.close()
        
        return df['assigned_agent_name'].tolist()
    
    def delete_all_records(self) -> int:
        """
        Elimina todos los registros de la base de datos (para testing)
        
        Returns:
            Número de registros eliminados
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM commission_reports")
        count = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM commission_reports")
        conn.commit()
        conn.close()
        
        print(f"🗑️ {count} registros eliminados")
        return count
    
    def export_to_excel(self, output_path: Path, carrier_name: Optional[str] = None):
        """
        Exporta los datos a un archivo Excel
        
        Args:
            output_path: Ruta del archivo de salida
            carrier_name: Filtrar por carrier (opcional)
        """
        if carrier_name:
            df = self.get_reports_by_carrier(carrier_name)
        else:
            df = self.get_all_reports()
        
        df.to_excel(output_path, index=False)
        print(f"📊 Datos exportados a: {output_path}")


# Instancia global del gestor de base de datos
db = DatabaseManager()


if __name__ == "__main__":
    # Test básico
    print("Testing Database Manager...")
    print(f"Database path: {config.DATABASE_PATH}")
    
    stats = db.get_summary_stats()
    print(f"\nTotal records: {stats['total_records']}")
    print(f"Total amount: ${stats['total_amount']:,.2f}")
