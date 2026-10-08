import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF

# Configuración de la página
st.set_page_config(
    page_title="App Tueste - Sinfonía del Café", 
    page_icon="☕", 
    layout="wide"
)

st.title("☕ App Tueste - Sinfonía del Café")
st.caption("Sistema Predictivo de Tostión, Colorimetría SCA y Bitácora Térmica en Tiempo Real")
st.markdown("---")

# 1. ENTRADA DE DATOS DEL CAFÉ VERDE
st.sidebar.header("1. Datos del Café Verde")
nombre_cafe = st.sidebar.text_input("Nombre del Café / Finca", "Finca La Esperanza")
variedad = st.sidebar.text_input("Variedad", "Castillo / Bourbon")
proceso = st.sidebar.selectbox("Proceso / Beneficio", ["Lavado", "Natural", "Honey", "Anaeróbico"])

densidad = st.sidebar.number_input("Densidad (g/L)", min_value=500, max_value=800, value=680)
humedad = st.sidebar.number_input("Humedad (%)", min_value=8.0, max_value=15.0, value=11.5, step=0.1)
peso_carga = st.sidebar.number_input("Peso de Carga (g)", min_value=100, max_value=10000, value=1000)

st.sidebar.header("2. Perfil Objetivo en Taza")
perfil_deseado = st.sidebar.selectbox(
    "Atributo Principal Deseado",
    ["Alta Acidez (Notas Cítricas/Florales)", "Alta Dulzura (Caramelo/Miel)", "Alto Cuerpo (Chocolate/Nuez)"]
)

# ALGORITMO PREDICTIVO DE TUESTE
def calcular_prediccion(densidad, humedad, peso, perfil):
    t_carga = 185.0 + (densidad - 650.0) * 0.06 + (humedad - 11.0) * 2.5 + (peso - 1000.0) * 0.02
    rpm_base = 60 + (peso - 1000.0) * 0.01 + (densidad - 650.0) * 0.02
    rpm_recomendadas = int(round(max(45, min(90, rpm_base))))
    
    if "Acidez" in perfil:
        dtr_target = 15.0
        nivel_tueste = "Claro (City / Agtron 70-75)"
    elif "Dulzura" in perfil:
        dtr_target = 17.5
        nivel_tueste = "Medio-Claro (City+ / Agtron 60-65)"
    else:
        dtr_target = 19.0
        nivel_tueste = "Medio (Full City / Agtron 50-55)"
        
    tiempo_secado = 4.2 + (humedad - 11.0) * 0.3 + (densidad - 650.0) * 0.003
    tiempo_1st_crack = tiempo_secado + 4.5
    tiempo_total = tiempo_1st_crack / (1.0 - (dtr_target / 100.0))
    tiempo_desarrollo = tiempo_total - tiempo_1st_crack
    
    return (
        round(t_carga, 1), 
        rpm_recomendadas, 
        dtr_target, 
        nivel_tueste, 
        round(tiempo_secado, 2), 
        round(tiempo_1st_crack, 2), 
        round(tiempo_desarrollo, 2), 
        round(tiempo_total, 2)
    )

t_carga, rpm_rec, dtr_target, nivel_tueste, t_secado, t_1st_crack, t_dev, t_total = calcular_prediccion(
    densidad, humedad, peso_carga, perfil_deseado
)

# RECOMENDACIÓN TÉCNICA
st.subheader("🎯 Receta Térmica y Mecánica Recomendada")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Temp. Carga", f"{t_carga} °C")
col2.metric("RPM Tambor Sugeridas", f"{rpm_rec} RPM")
col3.metric("Objetivo DTR", f"{dtr_target} %")
col4.metric("Min. 1st Crack Est.", f"{t_1st_crack} min")
col5.metric("Min. Descarte Est.", f"{t_total} min")

st.info(f"**Lote:** {nombre_cafe} ({variedad} - {proceso}) | **Perfil:** {nivel_tueste} | **Tiempo Desarrollo Est.:** {t_dev} min")

st.markdown("---")

# BITÁCORA DE TUESTE
st.subheader("📝 Bitácora Minuto a Minuto (Hitos SCA y Colorimetría)")

data_inicial = {
    "Minuto": [0.0, 1.0, 2.0, 3.0, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, t_1st_crack, 10.5, t_total],
    "Temp Grano (°C)": [t_carga, 95.0, 110.0, 128.0, 144.0, 151.5, 158.5, 171.0, 182.0, 191.0, 198.0, 202.5, 206.5, 210.5],
    "Fase / Hito SCA": [
        "01. Carga (Charge)", "02. Punto de Viraje (TP)", "03. Secado (Drying)",
        "04. Pico de RoR", "05. Vaporización", "06. Cambio a Amarillo",
        "07. Inicio Maillard", "08. Aromas Maillard", "09. Caramelización",
        "10. Pre-Craqueo", "11. Presión Alta", "12. Primer Craqueo (1st Crack)",
        "13. Desarrollo (DTR)", "14. Descarte (Drop)"
    ],
    "Color del Grano": [
        "Verde Aceituna", "Verde Claro", "Verde Menta", "Amarillo Verdoso",
        "Amarillo Pálido", "Amarillo Dorado", "Canela Claro", "Marrón Avellana",
        "Marrón Pardo", "Marrón Medio", "Marrón Intenso", "Marrón City",
        "Marrón City+", "Marrón Chocolate Claro"
    ],
    "RPM Tambor": [rpm_rec]*6 + [rpm_rec+2]*2 + [rpm_rec+4]*2 + [rpm_rec+5]*4,
    "Flujo Aire (%)": [30, 30, 30, 30, 40, 40, 50, 50, 60, 60, 70, 80, 85, 90],
    "Potencia Gas (%)": [80, 80, 80, 80, 75, 75, 70, 65, 60, 55, 45, 35, 25, 20]
}

df = pd.DataFrame(data_inicial)
df_editado = st.data_editor(df, num_rows="dynamic", use_container_width=True)

# CÁLCULO DE ROR
rors = ["-", "TP"]
for i in range(2, len(df_editado)):
    t_curr = df_editado.loc[i, "Minuto"]
    t_prev = df_editado.loc[i-1, "Minuto"]
    temp_curr = df_editado.loc[i, "Temp Grano (°C)"]
    temp_prev = df_editado.loc[i-1, "Temp Grano (°C)"]
    
    if t_curr > t_prev:
        ror = round((temp_curr - temp_prev) / (t_curr - t_prev), 1)
        rors.append(ror)
    else:
        rors.append(0.0)

df_editado["RoR (°C/min)"] = rors

# DIAGNÓSTICO EN VIVO (ESTRUCTURA CORREGIDA)
st.subheader("🔍 Diagnóstico Térmico del RoR en Vivo")
ror_num = [0.0 if r in ["-", "TP"] else float(r) for r in rors]

has_flick = any(ror_num[idx] > ror_num[idx-1] for idx in range(3, len(ror_num)) if df_editado.loc[idx, "Minuto"] >= t_1st_crack)
has_crash = any(ror_num[idx] <= 0.5 for idx in range(3, len(ror_num)) if df_editado.loc[idx, "Minuto"] < t_total)

col_d1, col_d2 = st.columns(2)
with col_d1:
    if has_flick:
        st.error("⚠️ **Alerta de Flick:** RoR subió tras el 1st Crack.")
    else:
        st.success("✅ **Sin Flick:** RoR controlado.")

with col_d2:
    if has_crash:
        st.warning("⚠️ **Alerta de Crash:** RoR muy bajo antes del descarte.")
    else:
        st.success("✅ **Curva Fluida:** Impulso constante.")

st.markdown("---")

# GRÁFICA INTERACTIVA
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_editado["Minuto"], y=df_editado["Temp Grano (°C)"], mode='lines+markers', name='BT (°C)', line=dict(color='firebrick', width=3)))
fig.add_trace(go.Scatter(x=df_editado["Minuto"], y=ror_num, mode='lines+markers', name='RoR (°C/min)', line=dict(color='royalblue', width=2, dash='dash'), yaxis="y2"))
fig.add_trace(go.Scatter(x=df_editado["Minuto"], y=df_editado["RPM Tambor"], mode='lines+markers', name='RPM', line=dict(color='forestgreen', width=2, dash='dot'), yaxis="y2"))

fig.update_layout(
    title="Curva de Tueste, RoR y RPM",
    xaxis=dict(title="Tiempo (Min)"),
    yaxis=dict(title="Temperatura (°C)", range=[50, 240]),
    yaxis2=dict(title="RoR / RPM", overlaying="y", side="right", range=[0, 100]),
    height=500
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# CONTROL DE MASAS Y GENERACIÓN DE PDF
st.subheader("⚖️ Rendimiento Final y Generación de Reporte PDF")
col_m1, col_m2 = st.columns(2)

with col_m1:
    peso_tostado = st.number_input("Peso Final Obtenido (g)", min_value=0.0, value=peso_carga * 0.85, step=5.0)
    merma_pct = round(((peso_carga - peso_tostado) / peso_carga) * 100, 2) if peso_carga > 0 else 0.0
    st.metric("Merma Resultante (%)", f"{merma_pct} %")

def generar_pdf(nombre, variedad, proceso, densidad, humedad, peso_c, peso_t, merma, dtr, df_data):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "App Tueste - Sinfonia del Cafe", ln=True, align="C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 6, "Reporte Tecnico de Tostion de Especialidad SCA", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "1. Ficha del Cafe Verde y Rendimiento", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Lote / Finca: {nombre} | Variedad: {variedad} | Proceso: {proceso}", ln=True)
    pdf.cell(0, 6, f"Densidad: {densidad} g/L | Humedad: {humedad}% | Masa Carga: {peso_c}g", ln=True)
    pdf.cell(0, 6, f"Masa Obtenida: {peso_t}g | Merma: {merma}% | DTR Objetivo: {dtr}%", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "2. Bitacora y Registro Termico", ln=True)
    
    pdf.set_font("Arial", "B", 8)
    pdf.cell(15, 6, "Min", border=1)
    pdf.cell(20, 6, "BT (C)", border=1)
    pdf.cell(22, 6, "RoR (C/m)", border=1)
    pdf.cell(18, 6, "RPM", border=1)
    pdf.cell(18, 6, "Aire %", border=1)
    pdf.cell(18, 6, "Gas %", border=1)
    pdf.cell(80, 6, "Fase / Hito SCA", border=1, ln=True)
    
    pdf.set_font("Arial", "", 8)
    for idx, row in df_data.iterrows():
        pdf.cell(15, 5, str(row["Minuto"]), border=1)
        pdf.cell(20, 5, str(row["Temp Grano (°C)"]), border=1)
        pdf.cell(22, 5, str(row["RoR (°C/min)"]), border=1)
        pdf.cell(18, 5, str(row["RPM Tambor"]), border=1)
        pdf.cell(18, 5, str(row["Flujo Aire (%)"]), border=1)
        pdf.cell(18, 5, str(row["Potencia Gas (%)"]), border=1)
        pdf.cell(80, 5, str(row["Fase / Hito SCA"])[:40], border=1, ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

with col_m2:
    st.write("### Exportar Ficha Técnica")
    pdf_bytes = generar_pdf(
        nombre_cafe, variedad, proceso, densidad, humedad, 
        peso_carga, peso_tostado, merma_pct, dtr_target, df_editado
    )
    
    st.download_button(
        label="📄 Descargar Ficha de Tueste en PDF",
        data=pdf_bytes,
        file_name=f"Reporte_Tueste_{nombre_cafe.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
