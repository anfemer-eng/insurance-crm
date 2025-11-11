# 🏥 CRM de Comisiones - Wiseventures Consulting

Sistema automatizado para gestión de comisiones y overrides de seguros de salud.

## 🚀 Características

- ✅ Procesamiento automático de reportes Excel
- ✅ Soporte para múltiples carriers (Molina, Ambetter, Aetna, Oscar)
- ✅ Dashboard interactivo con gráficos en tiempo real
- ✅ Filtros avanzados y exportación a Excel
- ✅ Base de datos SQLite integrada
- ✅ Mapeo automático de columnas por carrier

## 🌐 Aplicación en Vivo

**Accede aquí:** [https://wiseventurescrm.streamlit.app](https://wiseventurescrm.streamlit.app)

La aplicación está disponible 24/7 en la nube. No requiere instalación.

## 📊 Carriers Soportados

| Carrier | Estado | Campos Especiales |
|---------|--------|-------------------|
| Molina Healthcare | ✅ Activo | Agente, Mes Pagado |
| Ambetter | ✅ Activo | PayoutType |
| Aetna | ✅ Activo | Payout Type |
| Oscar Health | ✅ Activo | State, Lives |

## 💻 Instalación Local (Opcional)

Si deseas ejecutar la aplicación localmente:
```bash
# Clonar el repositorio
git clone https://github.com/anfemer-eng/insurance-crm.git
cd insurance-crm

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`

## 📝 Cómo Usar

### 1. Cargar Reportes
1. Ve a la pestaña **"📤 Cargar Reportes"**
2. Selecciona el carrier del dropdown
3. Sube el archivo Excel (.xlsx o .xls)
4. Haz clic en **"🚀 Procesar Archivo"**
5. Los datos se procesan y guardan automáticamente

### 2. Ver Dashboard
- Visualiza métricas totales (registros, comisiones, overrides)
- Gráficos interactivos por carrier
- Distribución por tipo de transacción
- Ranking de agentes

### 3. Filtrar y Analizar
- Usa la pestaña **"📋 Ver Datos"**
- Filtra por carrier, agente o tipo de transacción
- Visualiza datos en tabla interactiva
- Exporta resultados a Excel

## 🔒 Seguridad

- ✅ Conexión HTTPS segura
- ✅ Datos almacenados en la nube de forma privada
- ✅ No compartimos información con terceros
- ✅ Cada usuario gestiona sus propios reportes

## 🛠️ Tecnologías

- **Frontend/Backend:** Streamlit
- **Procesamiento de datos:** Pandas, NumPy
- **Visualización:** Plotly
- **Base de datos:** SQLite
- **Archivos Excel:** OpenPyXL

## 📞 Soporte

Para soporte técnico o preguntas:
- **Email:** support@wiseventures.com
- **Desarrollado para:** Wiseventures Consulting

## 📄 Licencia

Propiedad exclusiva de Wiseventures Consulting © 2025

---

**Versión:** 1.0  
**Última actualización:** Noviembre 2025  
**Desarrollado con ❤️ para Wiseventures Consulting**
```

---

## 🚨 SOLUCIÓN 3: PROBLEMA DE PYTHON VERSION

Veo que Streamlit está usando **Python 3.13.9**, que es **demasiado nuevo** y puede causar problemas de compatibilidad.

**Forzar Python 3.11:**

1. En tu repositorio, clic en "Add file" → "Create new file"
2. Nombre: `.python-version`
3. Contenido (solo esta línea):
```
3.11
```
4. Commit

Esto le dirá a Streamlit que use Python 3.11 en lugar de 3.13.

---

## 🔄 SOLUCIÓN 4: REBOOT COMPLETO

Después de hacer los cambios arriba:

1. Ve a Streamlit Cloud
2. Menú **⋮** (tres puntos) → **"Reboot app"**
3. Espera 3-4 minutos
4. Si sigue sin funcionar → **"Delete app"** y créala de nuevo

---

## 🎯 CHECKLIST - HAZ ESTO EN ORDEN:
```
1. ✅ Editar requirements.txt (con el contenido que te di)
2. ✅ Editar README.md (con el contenido completo)
3. ✅ Crear archivo .python-version (con "3.11")
4. ✅ Reboot app en Streamlit Cloud
5. ⏱️ Esperar 3-4 minutos
