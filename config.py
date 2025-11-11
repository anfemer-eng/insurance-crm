"""
Configuración del CRM de Seguros
Mapeos de campos por carrier y configuración general
"""

import os
from pathlib import Path

# Rutas del proyecto
BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
UPLOADS_DIR = BASE_DIR / "uploads"
REPORTS_DIR = BASE_DIR / "reports"

DATABASE_PATH = DATABASE_DIR / "insurance_crm.db"

# Crear directorios si no existen
for directory in [DATABASE_DIR, UPLOADS_DIR, REPORTS_DIR]:
    directory.mkdir(exist_ok=True)

# =============================================================================
# MAPEOS DE CAMPOS POR CARRIER
# =============================================================================

MOLINA_MAPPING = {
    'Generated From': 'generated_from',
    'Payment Date': 'payment_date',
    'PayeeName': 'payee_name',
    'NPN': 'payee_npn',
    'Statement Date': 'statement_date',
    'Product': 'product',
    'Policy': 'policy_number',
    'Insured': 'insured_name',
    'Effective Date': 'effective_date',
    'WritingAgent': 'writing_agent',
    'Writing Agent Number': 'writing_agent_number',
    'Transaction Type': 'transaction_type',
    'NewToMedicare': 'new_to_medicare',
    'Carrier Transaction Type': 'carrier_transaction_type',
    'Member Count': 'member_count',
    'Amount': 'amount',
    'Agente': 'assigned_agent_name',
    'Mes Pagado': 'commission_month'
}

AMBETTER_MAPPING = {
    'Generated From': 'generated_from',
    'Payment Date': 'payment_date',
    'PayeeName': 'payee_name',
    'NPN': 'payee_npn',
    'Statement Date': 'statement_date',
    'Product': 'product',
    'Policy': 'policy_number',
    'Insured': 'insured_name',
    'Effective Date': 'effective_date',
    'PayoutType': 'payout_type',
    'Writing Agent': 'writing_agent',
    'Writing Agent Number': 'writing_agent_number',
    'TransactionType': 'transaction_type',
    'NewToMedicare': 'new_to_medicare',
    'Carrier Transaction Type': 'carrier_transaction_type',
    'Member Count': 'member_count',
    'Amount': 'amount',
    'Unnamed: 18': 'assigned_agent_name'
}

AETNA_MAPPING = {
    'Generated From': 'generated_from',
    'Payment Date': 'payment_date',
    'PayeeName': 'payee_name',
    'Statement Date': 'statement_date',
    'Product': 'product',
    'Policy': 'policy_number',
    'Insured': 'insured_name',
    'Effective Date': 'effective_date',
    'Payout Type': 'payout_type',
    'WritingAgent': 'writing_agent',
    'WritingAgentNumber': 'writing_agent_number',
    'Transaction Type': 'transaction_type',
    'NewToMedicare': 'new_to_medicare',
    'CarrierTransactionType': 'carrier_transaction_type',
    'Member Count': 'member_count',
    'Amount': 'amount'
}

OSCAR_MAPPING = {
    'Commission type': 'commission_type',
    'Payee name': 'payee_name',
    'Payee type': 'payee_type',
    'Payee NPN': 'payee_npn',
    'Member ID': 'member_id',
    'Subscriber name': 'insured_name',
    'State': 'state',
    'Lives': 'lives',
    'Effective Date': 'effective_date',
    'Commission': 'amount',
    'Commission month': 'commission_month',
    'Block Reason': 'block_reason',
    'Unnamed: 12': 'assigned_agent_name'
}

# Mapeo de carriers
CARRIER_MAPPINGS = {
    'MOLINA': MOLINA_MAPPING,
    'AMBETTER': AMBETTER_MAPPING,
    'AETNA': AETNA_MAPPING,
    'OSCAR': OSCAR_MAPPING
}

# Lista de carriers disponibles
AVAILABLE_CARRIERS = list(CARRIER_MAPPINGS.keys())

# =============================================================================
# ESQUEMA DE LA BASE DE DATOS
# =============================================================================

DATABASE_SCHEMA = """
-- Tabla de carriers
CREATE TABLE IF NOT EXISTS carriers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    code TEXT UNIQUE NOT NULL,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de agentes
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    npn TEXT,
    email TEXT,
    phone TEXT,
    override_percentage REAL,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla principal de reportes de comisiones
CREATE TABLE IF NOT EXISTS commission_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Metadatos del reporte
    carrier_name TEXT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_date TEXT,
    statement_date TEXT,
    report_file_name TEXT,
    
    -- Información del pago
    payee_name TEXT,
    payee_npn TEXT,
    payee_type TEXT,
    
    -- Información de la póliza
    policy_number TEXT,
    member_id TEXT,
    insured_name TEXT,
    effective_date TEXT,
    
    -- Información de comisión
    transaction_type TEXT,
    payout_type TEXT,
    commission_type TEXT,
    amount REAL,
    member_count INTEGER,
    lives INTEGER,
    
    -- Información del agente de escritura
    writing_agent TEXT,
    writing_agent_number TEXT,
    
    -- Asignación interna
    assigned_agent_name TEXT,
    
    -- Campos adicionales
    state TEXT,
    product TEXT,
    new_to_medicare BOOLEAN,
    carrier_transaction_type TEXT,
    block_reason TEXT,
    commission_month TEXT,
    generated_from TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimizar búsquedas
CREATE INDEX IF NOT EXISTS idx_carrier ON commission_reports(carrier_name);
CREATE INDEX IF NOT EXISTS idx_payment_date ON commission_reports(payment_date);
CREATE INDEX IF NOT EXISTS idx_assigned_agent ON commission_reports(assigned_agent_name);
CREATE INDEX IF NOT EXISTS idx_policy ON commission_reports(policy_number);
CREATE INDEX IF NOT EXISTS idx_transaction_type ON commission_reports(transaction_type);
CREATE INDEX IF NOT EXISTS idx_upload_date ON commission_reports(upload_date);

-- Insertar carriers iniciales
INSERT OR IGNORE INTO carriers (name, code) VALUES 
    ('Molina Healthcare', 'MOLINA'),
    ('Ambetter', 'AMBETTER'),
    ('Aetna', 'AETNA'),
    ('Oscar Health', 'OSCAR');
"""

# =============================================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# =============================================================================

APP_CONFIG = {
    'title': '🏥 CRM Comisiones - Wiseventures Consulting',
    'page_icon': '🏥',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# Formatos de archivo permitidos
ALLOWED_EXTENSIONS = ['.xlsx', '.xls', '.pdf']

# Colores para el dashboard
COLORS = {
    'primary': '#1f77b4',
    'success': '#2ecc71',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'info': '#3498db'
}
