"""
Aplicación principal del CRM de Seguros
Sistema de gestión de comisiones y overrides
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import sys

# Importar módulos locales
import config
from database import db
from processor import processor, process_and_save

# Configuración de la página
st.set_page_config(**config.APP_CONFIG)

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def format_currency(value):
    """Formatea un valor como moneda USD"""
    if pd.isna(value) or value is None:
        return "$0.00"
    return f"${value:,.2f}"


def display_metric_card(label, value, delta=None, help_text=None):
    """Muestra una tarjeta de métrica estilizada"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric(label=label, value=value, delta=delta, help=help_text)


def create_summary_chart(stats):
    """Crea gráfico de resumen por carrier"""
    df_carrier = stats['by_carrier']
    
    if len(df_carrier) == 0:
        return None
    
    fig = px.bar(
        df_carrier,
        x='carrier_name',
        y='total',
        title='Comisiones por Carrier',
        labels={'carrier_name': 'Carrier', 'total': 'Total ($)'},
        color='total',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        showlegend=False,
        height=400
    )
    
    return fig


def create_transaction_type_chart(stats):
    """Crea gráfico de tipos de transacción"""
    df_type = stats['by_type']
    
    if len(df_type) == 0:
        return None
    
    fig = px.pie(
        df_type,
        values='total',
        names='transaction_type',
        title='Distribución por Tipo de Transacción',
        hole=0.4
    )
    
    fig.update_layout(height=400)
    
    return fig


def create_agent_chart(stats):
    """Crea gráfico de comisiones por agente"""
    df_agent = stats['by_agent']
    
    if len(df_agent) == 0:
        return None
    
    fig = px.bar(
        df_agent,
        x='assigned_agent_name',
        y='total',
        title='Comisiones por Agente',
        labels={'assigned_agent_name': 'Agente', 'total': 'Total ($)'},
        color='total',
        color_continuous_scale='Greens'
    )
    
    fig.update_layout(
        showlegend=False,
        height=400
    )
    
    return fig


# =============================================================================
# INTERFAZ PRINCIPAL
# =============================================================================

def main():
    """Función principal de la aplicación"""
    
    # Título principal
    st.title("🏥 CRM Comisiones - Wiseventures Consulting")
    st.markdown("---")
    
    # Sidebar - Navegación
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/health-insurance.png", width=80)
        st.title("Navegación")
        
        page = st.radio(
            "Selecciona una página:",
            ["📊 Dashboard", "📤 Cargar Reportes", "📋 Ver Datos", "⚙️ Configuración"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 📈 Resumen Rápido")
        
        # Obtener estadísticas básicas
        stats = db.get_summary_stats()
        st.metric("Total Registros", f"{stats['total_records']:,}")
        st.metric("Total Comisiones", format_currency(stats['total_amount']))
        
        st.markdown("---")
        st.markdown("**Desarrollado por:**")
        st.markdown("Wiseventures Consulting")
        st.markdown(f"*Versión 1.0 - {datetime.now().strftime('%Y')}*")
    
    # Contenido principal según la página seleccionada
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "📤 Cargar Reportes":
        show_upload_page()
    elif page == "📋 Ver Datos":
        show_data_view()
    elif page == "⚙️ Configuración":
        show_settings()


# =============================================================================
# PÁGINA: DASHBOARD
# =============================================================================

def show_dashboard():
    """Muestra el dashboard principal con métricas y gráficos"""
    
    st.header("📊 Dashboard de Comisiones")
    
    # Obtener estadísticas
    stats = db.get_summary_stats()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📝 Total Registros",
            value=f"{stats['total_records']:,}",
            help="Número total de registros en la base de datos"
        )
    
    with col2:
        st.metric(
            label="💰 Total Comisiones",
            value=format_currency(stats['total_amount']),
            help="Suma total de todas las comisiones"
        )
    
    with col3:
        commission_count = 0
        if len(stats['by_type']) > 0:
            commission_row = stats['by_type'][stats['by_type']['transaction_type'] == 'Commission']
            if len(commission_row) > 0:
                commission_count = commission_row['total'].values[0]
        st.metric(
            label="🎯 Comisiones",
            value=format_currency(commission_count),
            help="Total de comisiones regulares"
        )
    
    with col4:
        override_count = 0
        if len(stats['by_type']) > 0:
            override_row = stats['by_type'][stats['by_type']['transaction_type'] == 'Override']
            if len(override_row) > 0:
                override_count = override_row['total'].values[0]
        st.metric(
            label="⚡ Overrides",
            value=format_currency(override_count),
            help="Total de overrides"
        )
    
    st.markdown("---")
    
    # Gráficos
    if stats['total_records'] > 0:
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico por Carrier
            fig_carrier = create_summary_chart(stats)
            if fig_carrier:
                st.plotly_chart(fig_carrier, use_container_width=True)
            else:
                st.info("No hay datos para mostrar por carrier")
        
        with col2:
            # Gráfico por Tipo de Transacción
            fig_type = create_transaction_type_chart(stats)
            if fig_type:
                st.plotly_chart(fig_type, use_container_width=True)
            else:
                st.info("No hay datos para mostrar por tipo de transacción")
        
        # Gráfico por Agente (ancho completo)
        fig_agent = create_agent_chart(stats)
        if fig_agent:
            st.plotly_chart(fig_agent, use_container_width=True)
        else:
            st.info("No hay datos asignados a agentes aún")
        
        # Tabla resumen por Carrier
        st.markdown("### 📊 Resumen por Carrier")
        df_carrier_display = stats['by_carrier'].copy()
        df_carrier_display['total'] = df_carrier_display['total'].apply(format_currency)
        df_carrier_display.columns = ['Carrier', 'Registros', 'Total']
        st.dataframe(df_carrier_display, use_container_width=True, hide_index=True)
        
    else:
        st.info("👈 No hay datos cargados. Ve a 'Cargar Reportes' para subir tus archivos.")


# =============================================================================
# PÁGINA: CARGAR REPORTES
# =============================================================================

def show_upload_page():
    """Página para cargar archivos de reportes"""
    
    st.header("📤 Cargar Reportes de Comisiones")
    
    st.markdown("""
    Sube los archivos Excel de reportes de las diferentes carriers.
    El sistema procesará automáticamente los datos y los guardará en la base de datos.
    """)
    
    # Selector de Carrier
    st.markdown("### 1️⃣ Selecciona el Carrier")
    carrier_name = st.selectbox(
        "Carrier",
        options=config.AVAILABLE_CARRIERS,
        help="Selecciona la compañía de seguros del reporte"
    )
    
    # Upload de archivo
    st.markdown("### 2️⃣ Sube el Archivo")
    uploaded_file = st.file_uploader(
        "Selecciona un archivo Excel",
        type=['xlsx', 'xls'],
        help="Formatos permitidos: .xlsx, .xls"
    )
    
    if uploaded_file is not None:
        
        # Guardar archivo temporalmente
        temp_path = config.UPLOADS_DIR / uploaded_file.name
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        # Mostrar información del archivo
        st.info(f"📁 Archivo: {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)")
        
        # Botón para procesar
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🚀 Procesar Archivo", type="primary", use_container_width=True):
                with st.spinner("Procesando archivo..."):
                    result = process_and_save(temp_path, carrier_name, db)
                    
                    if result['success']:
                        st.success(result['message'])
                        
                        # Mostrar estadísticas
                        stats = result['stats']
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Registros Procesados", stats['total_records'])
                        with col_b:
                            st.metric("Total Amount", format_currency(stats['total_amount']))
                        with col_c:
                            if stats['date_range']:
                                st.metric("Rango de Fechas", 
                                         f"{stats['date_range']['start']} a {stats['date_range']['end']}")
                        
                        # Recargar la página después de un delay
                        st.balloons()
                        
                    else:
                        st.error(f"❌ {result['error']}")
        
        with col2:
            if st.button("👁️ Vista Previa", use_container_width=True):
                try:
                    df = pd.read_excel(temp_path)
                    st.markdown("### Vista Previa del Archivo")
                    st.dataframe(df.head(10), use_container_width=True)
                    st.info(f"Mostrando las primeras 10 filas de {len(df)} registros totales")
                except Exception as e:
                    st.error(f"Error al leer el archivo: {str(e)}")
    
    # Instrucciones
    st.markdown("---")
    st.markdown("### 📝 Instrucciones")
    
    with st.expander("¿Cómo usar esta función?"):
        st.markdown("""
        1. **Selecciona el Carrier** correspondiente al reporte
        2. **Sube el archivo Excel** usando el botón de arriba
        3. (Opcional) Haz clic en **Vista Previa** para verificar el contenido
        4. Haz clic en **Procesar Archivo** para importar los datos
        5. El sistema mapeará automáticamente las columnas y guardará los datos
        
        **Nota:** Los archivos deben estar en formato Excel (.xlsx o .xls)
        """)
    
    with st.expander("Carriers soportados y sus formatos"):
        for carrier in config.AVAILABLE_CARRIERS:
            st.markdown(f"**{carrier}**")
            mapping = config.CARRIER_MAPPINGS[carrier]
            st.caption(f"Columnas esperadas: {', '.join(list(mapping.keys())[:5])}...")


# =============================================================================
# PÁGINA: VER DATOS
# =============================================================================

def show_data_view():
    """Página para visualizar y filtrar los datos"""
    
    st.header("📋 Visualización de Datos")
    
    # Obtener todos los datos
    df = db.get_all_reports()
    
    if len(df) == 0:
        st.warning("No hay datos cargados en la base de datos")
        return
    
    # Filtros
    st.markdown("### 🔍 Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        carriers = ['Todos'] + db.get_carriers()
        selected_carrier = st.selectbox("Carrier", carriers)
    
    with col2:
        agents = ['Todos'] + db.get_agents()
        selected_agent = st.selectbox("Agente", agents)
    
    with col3:
        transaction_types = ['Todos'] + df['transaction_type'].dropna().unique().tolist()
        selected_type = st.selectbox("Tipo de Transacción", transaction_types)
    
    # Aplicar filtros
    df_filtered = df.copy()
    
    if selected_carrier != 'Todos':
        df_filtered = df_filtered[df_filtered['carrier_name'] == selected_carrier]
    
    if selected_agent != 'Todos':
        df_filtered = df_filtered[df_filtered['assigned_agent_name'] == selected_agent]
    
    if selected_type != 'Todos':
        df_filtered = df_filtered[df_filtered['transaction_type'] == selected_type]
    
    # Métricas filtradas
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Registros", len(df_filtered))
    with col2:
        total = df_filtered['amount'].sum() if 'amount' in df_filtered.columns else 0
        st.metric("Total", format_currency(total))
    with col3:
        avg = df_filtered['amount'].mean() if 'amount' in df_filtered.columns else 0
        st.metric("Promedio", format_currency(avg))
    
    # Tabla de datos
    st.markdown("### 📊 Datos")
    
    # Seleccionar columnas relevantes para mostrar
    display_columns = [
        'carrier_name', 'payment_date', 'insured_name', 'policy_number',
        'transaction_type', 'amount', 'assigned_agent_name', 'effective_date'
    ]
    
    # Filtrar solo las columnas que existen
    display_columns = [col for col in display_columns if col in df_filtered.columns]
    
    df_display = df_filtered[display_columns].copy()
    
    # Formatear la columna amount
    if 'amount' in df_display.columns:
        df_display['amount'] = df_display['amount'].apply(lambda x: format_currency(x) if pd.notna(x) else "$0.00")
    
    st.dataframe(df_display, use_container_width=True, height=500)
    
    # Botón de exportación
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📥 Exportar a Excel", use_container_width=True):
            export_path = config.REPORTS_DIR / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df_filtered.to_excel(export_path, index=False)
            st.success(f"Datos exportados a: {export_path}")


# =============================================================================
# PÁGINA: CONFIGURACIÓN
# =============================================================================

def show_settings():
    """Página de configuración y utilidades"""
    
    st.header("⚙️ Configuración")
    
    # Información del sistema
    st.markdown("### 📊 Información del Sistema")
    
    stats = db.get_summary_stats()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Base de Datos**
        - Ubicación: `{config.DATABASE_PATH}`
        - Total Registros: {stats['total_records']:,}
        - Carriers: {len(stats['by_carrier'])}
        - Agentes: {len(stats['by_agent'])}
        """)
    
    with col2:
        st.info(f"""
        **Carriers Soportados**
        {chr(10).join(['- ' + c for c in config.AVAILABLE_CARRIERS])}
        """)
    
    # Utilidades
    st.markdown("---")
    st.markdown("### 🛠️ Utilidades")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Actualizar Estadísticas", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("🗑️ Limpiar Base de Datos", type="secondary", use_container_width=True):
            if st.checkbox("⚠️ Confirmar eliminación de todos los datos"):
                count = db.delete_all_records()
                st.warning(f"Se eliminaron {count} registros")
                st.rerun()
    
    # Información adicional
    st.markdown("---")
    st.markdown("### ℹ️ Acerca de")
    
    st.markdown("""
    **CRM de Comisiones v1.0**
    
    Sistema desarrollado para Wiseventures Consulting para la gestión automatizada 
    de comisiones y overrides de seguros de salud.
    
    **Características:**
    - ✅ Procesamiento automático de reportes Excel
    - ✅ Soporte para múltiples carriers
    - ✅ Dashboard interactivo
    - ✅ Filtros y búsqueda
    - ✅ Exportación a Excel
    
    **Desarrollado con:**
    - Python 3.x
    - Streamlit
    - Pandas
    - SQLite
    - Plotly
    """)


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    main()
