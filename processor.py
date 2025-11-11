"""
Excel file processing module for Insurance CRM
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime
import config


class FileProcessor:
    """Carrier report file processor"""
    
    def __init__(self):
        """Initialize processor"""
        self.carrier_mappings = config.CARRIER_MAPPINGS
    
    def process_file(self, file_path: Path, carrier_name: str) -> Tuple[pd.DataFrame, Dict]:
        """
        Process Excel file and normalize according to carrier
        
        Args:
            file_path: Path to Excel file
            carrier_name: Carrier name (MOLINA, AMBETTER, AETNA, OSCAR)
            
        Returns:
            Tuple with (normalized DataFrame, statistics dictionary)
        """
        if carrier_name not in self.carrier_mappings:
            raise ValueError(f"Carrier '{carrier_name}' not supported. Available carriers: {config.AVAILABLE_CARRIERS}")
        
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Get mapping for this carrier
        mapping = self.carrier_mappings[carrier_name]
        
        # Normalize data
        df_normalized = self._normalize_data(df, mapping, carrier_name)
        
        # Calculate statistics
        stats = self._calculate_stats(df_normalized, carrier_name)
        
        return df_normalized, stats
    
    def _normalize_data(self, df: pd.DataFrame, mapping: Dict, carrier_name: str) -> pd.DataFrame:
        """
        Normalize data by applying column mapping
        
        Args:
            df: Original DataFrame
            mapping: Column mapping dictionary
            carrier_name: Carrier name
            
        Returns:
            Normalized DataFrame
        """
        # Create empty DataFrame with all possible columns
        normalized_df = pd.DataFrame()
        
        # Apply mapping
        for original_col, normalized_col in mapping.items():
            if original_col in df.columns:
                normalized_df[normalized_col] = df[original_col]
        
        # Clean data
        normalized_df = self._clean_data(normalized_df)
        
        # Validate and convert data types
        normalized_df = self._convert_datatypes(normalized_df)
        
        return normalized_df
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean data: remove spaces, convert NaN, etc.
        
        Args:
            df: DataFrame to clean
            
        Returns:
            Clean DataFrame
        """
        df_clean = df.copy()
        
        # Remove spaces from strings
        for col in df_clean.select_dtypes(include=['object']).columns:
            df_clean[col] = df_clean[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        
        # Replace empty values with None
        df_clean = df_clean.replace({np.nan: None, '': None, 'nan': None})
        
        return df_clean
    
    def _convert_datatypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert data types appropriately
        
        Args:
            df: DataFrame to convert
            
        Returns:
            DataFrame with correct types
        """
        df_converted = df.copy()
        
        # Convert dates
        date_columns = ['payment_date', 'statement_date', 'effective_date']
        for col in date_columns:
            if col in df_converted.columns:
                df_converted[col] = pd.to_datetime(df_converted[col], errors='coerce')
                # Convert to string in ISO format for SQLite
                df_converted[col] = df_converted[col].dt.strftime('%Y-%m-%d')
                df_converted[col] = df_converted[col].replace('NaT', None)
        
        # Convert numbers
        numeric_columns = ['amount', 'member_count', 'lives', 'override_percentage']
        for col in numeric_columns:
            if col in df_converted.columns:
                df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce')
        
        # Convert booleans
        boolean_columns = ['new_to_medicare']
        for col in boolean_columns:
            if col in df_converted.columns:
                # Convert to boolean safely
                df_converted[col] = df_converted[col].map({
                    True: 1, False: 0, 'True': 1, 'False': 0, 
                    'true': 1, 'false': 0, 'Yes': 1, 'No': 0,
                    'yes': 1, 'no': 0, 1: 1, 0: 0
                })
        
        return df_converted
    
    def _calculate_stats(self, df: pd.DataFrame, carrier_name: str) -> Dict:
        """
        Calculate statistics for processed file
        
        Args:
            df: Processed DataFrame
            carrier_name: Carrier name
            
        Returns:
            Dictionary with statistics
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
        
        # Date range
        if 'payment_date' in df.columns:
            valid_dates = pd.to_datetime(df['payment_date'], errors='coerce').dropna()
            if len(valid_dates) > 0:
                stats['date_range'] = {
                    'start': valid_dates.min().strftime('%Y-%m-%d'),
                    'end': valid_dates.max().strftime('%Y-%m-%d')
                }
        
        # Distribution by transaction type
        if 'transaction_type' in df.columns:
            type_counts = df['transaction_type'].value_counts().to_dict()
            stats['transaction_types'] = type_counts
        
        # Distribution by assigned agent
        if 'assigned_agent_name' in df.columns:
            agent_counts = df['assigned_agent_name'].value_counts().to_dict()
            stats['agents'] = agent_counts
        
        return stats
    
    def validate_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Validate that file is a valid Excel file
        
        Args:
            file_path: File path
            
        Returns:
            Tuple (is_valid, message)
        """
        # Check extension
        if file_path.suffix not in ['.xlsx', '.xls']:
            return False, "File must be Excel (.xlsx or .xls)"
        
        # Check that it exists
        if not file_path.exists():
            return False, "File does not exist"
        
        # Try to read file
        try:
            df = pd.read_excel(file_path)
            if len(df) == 0:
                return False, "File is empty"
            return True, "Valid file"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
    
    def detect_carrier(self, file_path: Path) -> Optional[str]:
        """
        Try to automatically detect carrier based on columns
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Detected carrier name or None
        """
        try:
            df = pd.read_excel(file_path)
            columns = set(df.columns)
            
            # Check each mapping
            best_match = None
            max_matches = 0
            
            for carrier, mapping in self.carrier_mappings.items():
                expected_cols = set(mapping.keys())
                matches = len(columns.intersection(expected_cols))
                
                if matches > max_matches:
                    max_matches = matches
                    best_match = carrier
            
            # Requires at least 50% match
            if best_match and max_matches >= len(self.carrier_mappings[best_match]) * 0.5:
                return best_match
            
            return None
        except Exception:
            return None


# Global processor instance
processor = FileProcessor()


def process_and_save(file_path: Path, carrier_name: str, db_manager) -> Dict:
    """
    Process file and save to database
    
    Args:
        file_path: File path
        carrier_name: Carrier name
        db_manager: Database manager instance
        
    Returns:
        Dictionary with processing result
    """
    try:
        # Validate file
        is_valid, message = processor.validate_file(file_path)
        if not is_valid:
            return {
                'success': False,
                'error': message
            }
        
        # Process file
        df_normalized, stats = processor.process_file(file_path, carrier_name)
        
        # Save to database
        records_inserted = db_manager.insert_bulk_commission_reports(
            df_normalized, 
            carrier_name, 
            file_path.name
        )
        
        return {
            'success': True,
            'records_inserted': records_inserted,
            'stats': stats,
            'message': f'{records_inserted} records from {carrier_name} processed successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error processing file: {str(e)}'
        }


if __name__ == "__main__":
    # Basic test
    print("Testing File Processor...")
    print("Processor initialized successfully")
