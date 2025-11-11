"""
Database management module for Insurance CRM
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import config


class DatabaseManager:
    """SQLite database manager for CRM"""
    
    def __init__(self, db_path: Path = config.DATABASE_PATH):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(str(self.db_path))
    
    def init_database(self):
        """Initialize database with schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Execute schema
        cursor.executescript(config.DATABASE_SCHEMA)
        
        conn.commit()
        conn.close()
        
        print(f"Database initialized: {self.db_path}")
    
    def insert_commission_report(self, data: Dict[str, Any]) -> int:
        """
        Insert commission report into database
        
        Args:
            data: Dictionary with normalized data
            
        Returns:
            ID of inserted record
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
        Insert multiple commission reports from DataFrame
        
        Args:
            df: DataFrame with normalized data
            carrier_name: Carrier name
            file_name: Original file name
            
        Returns:
            Number of inserted records
        """
        conn = self.get_connection()
        
        # Add metadata
        df['carrier_name'] = carrier_name
        df['report_file_name'] = file_name
        df['upload_date'] = datetime.now().isoformat()
        
        # Insert into database
        df.to_sql('commission_reports', conn, if_exists='append', index=False)
        
        records_inserted = len(df)
        conn.close()
        
        print(f"{records_inserted} records inserted for {carrier_name}")
        return records_inserted
    
    def get_all_reports(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Get all commission reports
        
        Args:
            limit: Record limit to return
            
        Returns:
            DataFrame with reports
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
        Get reports filtered by carrier
        
        Args:
            carrier_name: Carrier name
            
        Returns:
            DataFrame with filtered reports
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
        Get reports filtered by agent
        
        Args:
            agent_name: Assigned agent name
            
        Returns:
            DataFrame with filtered reports
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
        Get summary commission statistics
        
        Returns:
            Dictionary with statistics
        """
        conn = self.get_connection()
        
        # Total records
        total_records = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM commission_reports", 
            conn
        )['count'][0]
        
        # Total commissions
        total_amount = pd.read_sql_query(
            "SELECT COALESCE(SUM(amount), 0) as total FROM commission_reports", 
            conn
        )['total'][0]
        
        # Commissions by type
        by_type = pd.read_sql_query("""
            SELECT transaction_type, COUNT(*) as count, SUM(amount) as total
            FROM commission_reports
            WHERE transaction_type IS NOT NULL
            GROUP BY transaction_type
        """, conn)
        
        # Commissions by carrier
        by_carrier = pd.read_sql_query("""
            SELECT carrier_name, COUNT(*) as count, SUM(amount) as total
            FROM commission_reports
            GROUP BY carrier_name
            ORDER BY total DESC
        """, conn)
        
        # Commissions by agent
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
        Get unique carriers list from database
        
        Returns:
            List of carrier names
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
        Get unique agents list from database
        
        Returns:
            List of agent names
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
        Delete all records from database (for testing)
        
        Returns:
            Number of deleted records
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM commission_reports")
        count = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM commission_reports")
        conn.commit()
        conn.close()
        
        print(f"{count} records deleted")
        return count
    
    def export_to_excel(self, output_path: Path, carrier_name: Optional[str] = None):
        """
        Export data to Excel file
        
        Args:
            output_path: Output file path
            carrier_name: Filter by carrier (optional)
        """
        if carrier_name:
            df = self.get_reports_by_carrier(carrier_name)
        else:
            df = self.get_all_reports()
        
        df.to_excel(output_path, index=False)
        print(f"Data exported to: {output_path}")


# Global database manager instance
db = DatabaseManager()


if __name__ == "__main__":
    # Basic test
    print("Testing Database Manager...")
    print(f"Database path: {config.DATABASE_PATH}")
    
    stats = db.get_summary_stats()
    print(f"\nTotal records: {stats['total_records']}")
    print(f"Total amount: ${stats['total_amount']:,.2f}")
