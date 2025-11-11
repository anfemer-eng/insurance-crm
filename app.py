"""
Main Insurance CRM Application
Commission and override management system
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import sys

# Import local modules
import config
from database import db
from processor import processor, process_and_save

# Page configuration
st.set_page_config(**config.APP_CONFIG)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_currency(value):
    """Format value as USD currency"""
    if pd.isna(value) or value is None:
        return "$0.00"
    return f"${value:,.2f}"


def display_metric_card(label, value, delta=None, help_text=None):
    """Display styled metric card"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric(label=label, value=value, delta=delta, help=help_text)


def create_summary_chart(stats):
    """Create summary chart by carrier"""
    df_carrier = stats['by_carrier']
    
    if len(df_carrier) == 0:
        return None
    
    fig = px.bar(
        df_carrier,
        x='carrier_name',
        y='total',
        title='Commissions by Carrier',
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
    """Create transaction type chart"""
    df_type = stats['by_type']
    
    if len(df_type) == 0:
        return None
    
    fig = px.pie(
        df_type,
        values='total',
        names='transaction_type',
        title='Distribution by Transaction Type',
        hole=0.4
    )
    
    fig.update_layout(height=400)
    
    return fig


def create_agent_chart(stats):
    """Create commission chart by agent"""
    df_agent = stats['by_agent']
    
    if len(df_agent) == 0:
        return None
    
    fig = px.bar(
        df_agent,
        x='assigned_agent_name',
        y='total',
        title='Commissions by Agent',
        labels={'assigned_agent_name': 'Agent', 'total': 'Total ($)'},
        color='total',
        color_continuous_scale='Greens'
    )
    
    fig.update_layout(
        showlegend=False,
        height=400
    )
    
    return fig


# =============================================================================
# MAIN INTERFACE
# =============================================================================

def main():
    """Main application function"""
    
    # Main title
    st.title("🏥 CRM Comisiones - Wiseventures Consulting")
    st.markdown("---")
    
    # Sidebar - Navigation
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/health-insurance.png", width=80)
        st.title("Navigation")
        
        page = st.radio(
            "Select a page:",
            ["📊 Dashboard", "📤 Upload Reports", "📋 View Data", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 📈 Quick Summary")
        
        # Get basic statistics
        stats = db.get_summary_stats()
        st.metric("Total Records", f"{stats['total_records']:,}")
        st.metric("Total Commissions", format_currency(stats['total_amount']))
        
        st.markdown("---")
        st.markdown("**Developed by:**")
        st.markdown("Wiseventures Consulting")
        st.markdown(f"*Version 1.0 - {datetime.now().strftime('%Y')}*")
    
    # Main content according to selected page
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "📤 Upload Reports":
        show_upload_page()
    elif page == "📋 View Data":
        show_data_view()
    elif page == "⚙️ Settings":
        show_settings()


# =============================================================================
# PAGE: DASHBOARD
# =============================================================================

def show_dashboard():
    """Show main dashboard with metrics and charts"""
    
    st.header("📊 Commissions Dashboard")
    
    # Get statistics
    stats = db.get_summary_stats()
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📝 Total Records",
            value=f"{stats['total_records']:,}",
            help="Total number of records in database"
        )
    
    with col2:
        st.metric(
            label="💰 Total Commissions",
            value=format_currency(stats['total_amount']),
            help="Sum of all commissions"
        )
    
    with col3:
        commission_count = 0
        if len(stats['by_type']) > 0:
            commission_row = stats['by_type'][stats['by_type']['transaction_type'] == 'Commission']
            if len(commission_row) > 0:
                commission_count = commission_row['total'].values[0]
        st.metric(
            label="🎯 Commissions",
            value=format_currency(commission_count),
            help="Total regular commissions"
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
            help="Total overrides"
        )
    
    st.markdown("---")
    
    # Charts
    if stats['total_records'] > 0:
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Chart by Carrier
            fig_carrier = create_summary_chart(stats)
            if fig_carrier:
                st.plotly_chart(fig_carrier, use_container_width=True)
            else:
                st.info("No data to show by carrier")
        
        with col2:
            # Chart by Transaction Type
            fig_type = create_transaction_type_chart(stats)
            if fig_type:
                st.plotly_chart(fig_type, use_container_width=True)
            else:
                st.info("No data to show by transaction type")
        
        # Chart by Agent (full width)
        fig_agent = create_agent_chart(stats)
        if fig_agent:
            st.plotly_chart(fig_agent, use_container_width=True)
        else:
            st.info("No data assigned to agents yet")
        
        # Summary table by Carrier
        st.markdown("### 📊 Summary by Carrier")
        df_carrier_display = stats['by_carrier'].copy()
        df_carrier_display['total'] = df_carrier_display['total'].apply(format_currency)
        df_carrier_display.columns = ['Carrier', 'Records', 'Total']
        st.dataframe(df_carrier_display, use_container_width=True, hide_index=True)
        
    else:
        st.info("👈 No data loaded. Go to 'Upload Reports' to upload your files.")


# =============================================================================
# PAGE: UPLOAD REPORTS
# =============================================================================

def show_upload_page():
    """Page to upload report files"""
    
    st.header("📤 Upload Commission Reports")
    
    st.markdown("""
    Upload Excel report files from different carriers.
    The system will automatically process the data and save it to the database.
    """)
    
    # Carrier selector
    st.markdown("### 1️⃣ Select Carrier")
    carrier_name = st.selectbox(
        "Carrier",
        options=config.AVAILABLE_CARRIERS,
        help="Select the insurance company of the report"
    )
    
    # File upload
    st.markdown("### 2️⃣ Upload File")
    uploaded_file = st.file_uploader(
        "Select an Excel file",
        type=['xlsx', 'xls'],
        help="Allowed formats: .xlsx, .xls"
    )
    
    if uploaded_file is not None:
        
        # Save file temporarily
        temp_path = config.UPLOADS_DIR / uploaded_file.name
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        # Show file information
        st.info(f"📁 File: {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)")
        
        # Process button
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🚀 Process File", type="primary", use_container_width=True):
                with st.spinner("Processing file..."):
                    result = process_and_save(temp_path, carrier_name, db)
                    
                    if result['success']:
                        st.success(result['message'])
                        
                        # Show statistics
                        stats = result['stats']
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Processed Records", stats['total_records'])
                        with col_b:
                            st.metric("Total Amount", format_currency(stats['total_amount']))
                        with col_c:
                            if stats['date_range']:
                                st.metric("Date Range", 
                                         f"{stats['date_range']['start']} to {stats['date_range']['end']}")
                        
                        # Reload page after delay
                        st.balloons()
                        
                    else:
                        st.error(f"❌ {result['error']}")
        
        with col2:
            if st.button("👁️ Preview", use_container_width=True):
                try:
                    df = pd.read_excel(temp_path)
                    st.markdown("### File Preview")
                    st.dataframe(df.head(10), use_container_width=True)
                    st.info(f"Showing first 10 rows of {len(df)} total records")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
    
    # Instructions
    st.markdown("---")
    st.markdown("### 📝 Instructions")
    
    with st.expander("How to use this feature?"):
        st.markdown("""
        1. **Select the Carrier** corresponding to the report
        2. **Upload the Excel file** using the button above
        3. (Optional) Click **Preview** to verify content
        4. Click **Process File** to import data
        5. System will automatically map columns and save data
        
        **Note:** Files must be in Excel format (.xlsx or .xls)
        """)
    
    with st.expander("Supported carriers and formats"):
        for carrier in config.AVAILABLE_CARRIERS:
            st.markdown(f"**{carrier}**")
            mapping = config.CARRIER_MAPPINGS[carrier]
            st.caption(f"Expected columns: {', '.join(list(mapping.keys())[:5])}...")


# =============================================================================
# PAGE: VIEW DATA
# =============================================================================

def show_data_view():
    """Page to view and filter data"""
    
    st.header("📋 Data Visualization")
    
    # Get all data
    df = db.get_all_reports()
    
    if len(df) == 0:
        st.warning("No data loaded in database")
        return
    
    # Filters
    st.markdown("### 🔍 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        carriers = ['All'] + db.get_carriers()
        selected_carrier = st.selectbox("Carrier", carriers)
    
    with col2:
        agents = ['All'] + db.get_agents()
        selected_agent = st.selectbox("Agent", agents)
    
    with col3:
        transaction_types = ['All'] + df['transaction_type'].dropna().unique().tolist()
        selected_type = st.selectbox("Transaction Type", transaction_types)
    
    # Apply filters
    df_filtered = df.copy()
    
    if selected_carrier != 'All':
        df_filtered = df_filtered[df_filtered['carrier_name'] == selected_carrier]
    
    if selected_agent != 'All':
        df_filtered = df_filtered[df_filtered['assigned_agent_name'] == selected_agent]
    
    if selected_type != 'All':
        df_filtered = df_filtered[df_filtered['transaction_type'] == selected_type]
    
    # Filtered metrics
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Records", len(df_filtered))
    with col2:
        total = df_filtered['amount'].sum() if 'amount' in df_filtered.columns else 0
        st.metric("Total", format_currency(total))
    with col3:
        avg = df_filtered['amount'].mean() if 'amount' in df_filtered.columns else 0
        st.metric("Average", format_currency(avg))
    
    # Data table
    st.markdown("### 📊 Data")
    
    # Select relevant columns to display
    display_columns = [
        'carrier_name', 'payment_date', 'insured_name', 'policy_number',
        'transaction_type', 'amount', 'assigned_agent_name', 'effective_date'
    ]
    
    # Filter only columns that exist
    display_columns = [col for col in display_columns if col in df_filtered.columns]
    
    df_display = df_filtered[display_columns].copy()
    
    # Format amount column
    if 'amount' in df_display.columns:
        df_display['amount'] = df_display['amount'].apply(lambda x: format_currency(x) if pd.notna(x) else "$0.00")
    
    st.dataframe(df_display, use_container_width=True, height=500)
    
    # Export button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📥 Export to Excel", use_container_width=True):
            export_path = config.REPORTS_DIR / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df_filtered.to_excel(export_path, index=False)
            st.success(f"Data exported to: {export_path}")


# =============================================================================
# PAGE: SETTINGS
# =============================================================================

def show_settings():
    """Settings and utilities page"""
    
    st.header("⚙️ Settings")
    
    # System information
    st.markdown("### 📊 System Information")
    
    stats = db.get_summary_stats()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Database**
        - Location: `{config.DATABASE_PATH}`
        - Total Records: {stats['total_records']:,}
        - Carriers: {len(stats['by_carrier'])}
        - Agents: {len(stats['by_agent'])}
        """)
    
    with col2:
        st.info(f"""
        **Supported Carriers**
        {chr(10).join(['- ' + c for c in config.AVAILABLE_CARRIERS])}
        """)
    
    # Utilities
    st.markdown("---")
    st.markdown("### 🛠️ Utilities")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Update Statistics", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Database", type="secondary", use_container_width=True):
            if st.checkbox("⚠️ Confirm deletion of all data"):
                count = db.delete_all_records()
                st.warning(f"{count} records deleted")
                st.rerun()
    
    # Additional information
    st.markdown("---")
    st.markdown("### ℹ️ About")
    
    st.markdown("""
    **Commissions CRM v1.0**
    
    System developed for Wiseventures Consulting for automated management 
    of health insurance commissions and overrides.
    
    **Features:**
    - ✅ Automatic Excel report processing
    - ✅ Support for multiple carriers
    - ✅ Interactive dashboard
    - ✅ Filters and search
    - ✅ Export to Excel
    
    **Built with:**
    - Python 3.x
    - Streamlit
    - Pandas
    - SQLite
    - Plotly
    """)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()
