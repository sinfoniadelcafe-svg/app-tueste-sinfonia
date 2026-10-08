import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import io
import tempfile
from fpdf import FPDF

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="App Tueste - Simulador y Bitácora SCA",
    page_icon="☕",
    layout="wide"
)

st.title("☕ App Tueste - Sinfonía del Café")
st.subheader("Simulador Térmico Dinámico y Control de Tostión de Especialidad SCA")

# ---------------------------------------------------------
# MOTOR DE SIMULACIÓN TERMODINÁMICA (FÍSICA DE TOSTIÓN)
# ---------------------------------------------------------
def simular_curva_termodinamica(df_input, temp_carga, rpm_optima):
    """
    Recalcula la curva de Temperatura BT (°C) y RoR (°C/min) en función de:
    - Potencia de Gas (%)
    - Flujo de Aire (%)
    - RPM del Tambor
    """
    df = df_input.copy()
    temps = [float(temp_carga)]
    rors = ["-", "TP"]
    
    for i in range(1, len(df)):
        t_prev = float(df.loc[i-1, "Minuto"])
        t_curr = float(df.loc[i, "Minuto"])
        dt = t_curr - t_prev if t_curr > t_prev else 1.0
        
        gas = float(df.loc[i, "Potencia Gas (%)"])
        air = float(df.loc[i, "Flujo Aire (%)"])
        rpm = float(df.loc[i, "RPM Tambor"])
        curr_temp = temps[-1]
        
        if i == 1:
            # Turning Point (Punto de Viraje)
            tp_temp = 92.0 + (gas - 80.0) * 0.12 + (rpm - rpm_optima) * 0.08
            temps.append(round(tp_temp, 1))
        else:
            # 1. Impulso de calor por Potencia de Gas (0-100% -> RoR base)
            base_ror = 3.0 + (gas / 100.0) * 20.0
            
            # 2. Eficiencia por RPM del Tambor
            rpm_diff = abs(rpm - rpm_optima)
            if rpm_diff <= 4:
                rpm_eff = 1.0
            else:
                rpm_eff = max(0.60, 1.0 - (rpm_diff - 4) * 0.02)
                
            # 3. Eficiencia por Flujo de Aire (Convección vs Pérdida por Extracción)
            if air <= 30:
                air_eff = 0.85 + (air / 30.0) * 0.10
            elif air <= 65:
                air_eff = 0.95 + ((air - 30) / 35.0) * 0.10
            else:
                air_eff = 1.05 - ((air - 65) / 35.0) * 0.28
                
            # 4. Gradiente Térmico del Grano
            temp_gradient = max(0.35, 1.0 - (curr_temp - 90.0) / 215.0)
            
            # RoR Resultante
            calc_ror = round(base_ror * rpm_eff * air_eff * temp_gradient, 1)
            next_temp = round(curr_temp + calc_ror * dt, 1)
            
            temps.append(next_temp)
            rors.append(calc_ror)
            
    df["Temp Grano (°C)"] = temps
    df["RoR (°C/min)"] = rors
    return df

# ---------------------------------------------------------
# BARRA LATERAL: PARAMETROS Y PERFIL DESEADO
# ---------------------------------------------------------
st.sidebar.header("📋 Ficha del Café Verde")
nombre_lote = st.sidebar.text_input("Nombre del Lote / Finca", "Finca La Esperanza")
variedad = st.sidebar.text_input("Variedad", "Castillo / Geisha")
proceso = st.sidebar.selectbox("Proceso de Beneficio", ["Lavado", "Natural", "Honey", "Anaeróbico"])
densidad = st.sidebar.number_input("Densidad (g/L)", value=680, step=5)
humedad = st.sidebar.number_input("Humedad (%)", value=11.5, step=0.1)

st.sidebar.header("🎯 Perfil Objetivo y Sabores Deseados")
perfil_objetivo = st.sidebar.selectbox(
    "Tipo de Perfil de Tostión",
    [
        "Acidez Brillante y Complejidad Floral (Tueste Claro)",
        "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "Cuerpo Denso / Chocolate y Caramelo (Tueste Medio-Oscuro)",
        "Perfil Expresso / Dulce y Resaltado de Cuerpo"
    ]
)
sabores_deseados = st.sidebar.text_input(
    "Sabores / Descriptores a Percibir",
    "Jasmin, Durazno, Panela, Cacao fino"
)

st.sidebar.header("⚙️ Configuración del Batch")
peso_carga = st.sidebar.number_input("Peso de Carga (g)", value=1000, step=50)
temp_carga = st.sidebar.number_input("Temp. Carga / Drop (°C)", value=188.1, step=0.5)
rpm_objetivo = st.sidebar.slider("RPM Óptimas Tostadora", min_value=40, max_value=80, value=61)

modo_calculo = st.sidebar.radio(
    "Modo de Operación",
    ["🔥 Simulador Térmico Dinámico (Física de Tostión)", "📝 Bitácora de Campo (Ingreso Manual Libre)"]
)

# Datos base iniciales
datos_iniciales = {
    "Minuto": [0.0, 1.0, 2.0, 3.0, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 9.75, 10.5, 11.5],
    "Fase / Hito SCA": [
        "01. Carga", "02. TP", "03. Secado",
        "04. Pico RoR", "05. Vaporización", "06. Amarillo",
        "07. In. Maillard", "08. Aromas", "09. Carameliz.",
        "10. Pre-Crack", "11. Presión Alta", "12. 1st Crack",
        "13. DTR", "14. Drop"
    ],
    "Color del Grano": [
        "Verde Aceituna", "Verde Claro", "Verde Menta", "Amarillo Verdoso",
        "Amarillo Pálido", "Amarillo Dorado", "Canela Claro", "Marrón Avellana",
        "Marrón Pardo", "Marrón Medio", "Marrón Intenso", "Marrón City",
        "Marrón City+", "Marrón Chocolate Claro"
    ],
    "RPM Tambor": [61, 61, 61, 61, 61, 61, 63, 63, 65, 65, 66, 66, 66, 66],
    "Flujo Aire (%)": [30, 30, 30, 30, 40, 40, 50, 50, 60, 60, 70, 80, 85, 90],
    "Potencia Gas (%)": [80, 80, 80, 80, 75, 75, 70, 65, 60, 55, 45, 35, 25, 20],
    "Temp Grano (°C)": [188.1, 92.0, 109.9, 126.2, 140.8, 147.5, 153.7, 164.9, 174.9, 183.5, 190.1, 193.7, 196.3, 199.2],
    "RoR (°C/min)": ["-", "TP", "17.9", "16.3", "14.6", "13.4", "12.4", "11.2", "10.0", "8.6", "6.6", "4.8", "3.5", "2.9"]
}

df_base = pd.DataFrame(datos_iniciales)

# ---------------------------------------------------------
# INTERFAZ Y TABLA INTERACTIVA
# ---------------------------------------------------------
st.markdown("### 📊 Control y Bitácora Interactiva")
st.info(f"🎯 **Perfil Seleccionado:** {perfil_objetivo} | **Sabores:** {sabores_deseados}")

df_editado = st.data_editor(
    df_base,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Minuto": st.column_config.NumberColumn("Minuto", format="%.2f"),
        "Temp Grano (°C)": st.column_config.NumberColumn("BT (°C)", format="%.1f"),
        "RPM Tambor": st.column_config.NumberColumn("RPM Tambor", min_value=30, max_value=100, step=1),
        "Flujo Aire (%)": st.column_config.NumberColumn("Aire %", min_value=0, max_value=100, step=5),
        "Potencia Gas (%)": st.column_config.NumberColumn("Gas %", min_value=0, max_value=100, step=5),
    }
)

# PROCESAMIENTO SEGÚN MODO SELECCIONADO
if "Simulador" in modo_calculo:
    df_procesado = simular_curva_termodinamica(df_editado, temp_carga, rpm_objetivo)
else:
    df_procesado = df_editado.copy()
    rors = ["-", "TP"]
    for i in range(2, len(df_procesado)):
        dt = float(df_procesado.loc[i, "Minuto"]) - float(df_procesado.loc[i-1, "Minuto"])
        dtemp = float(df_procesado.loc[i, "Temp Grano (°C)"]) - float(df_procesado.loc[i-1, "Temp Grano (°C)"])
        rors.append(round(dtemp / dt, 1) if dt > 0 else 0.0)
    df_procesado["RoR (°C/min)"] = rors

# ---------------------------------------------------------
# DIAGNÓSTICO EN TIEMPO REAL
# ---------------------------------------------------------
st.markdown("---")
st.markdown("### 📈 Diagnóstico en Tiempo Real")

col_p1, col_p2, col_p3, col_p4 = st.columns(4)

peso_tostado = col_p1.number_input("Peso Tostado Obtenido (g)", value=850.0, step=10.0)
merma = round(((peso_carga - peso_tostado) / peso_carga) * 100, 2)
col_p2.metric("Pérdida de Masa (Merma)", f"{merma} %")

min_1st_crack = df_procesado.loc[df_procesado["Fase / Hito SCA"].str.contains("1st Crack|Primer Craqueo", na=False), "Minuto"]
min_drop = df_procesado["Minuto"].iloc[-1]

if not min_1st_crack.empty:
    t_1st = min_1st_crack.values[0]
    dev_time = min_drop - t_1st
    dtr_val = round((dev_time / min_drop) * 100, 1) if min_drop > 0 else 0
else:
    dtr_val = 15.0

col_p3.metric("DTR (Tiempo Desarrollo)", f"{dtr_val} %")
col_p4.metric("RoR Final", f"{df_procesado['RoR (°C/min)'].iloc[-1]} °C/min")

# ---------------------------------------------------------
# GRÁFICA PLOTLY OPTIMIZADA CON ALTA ESCALA Y HITOS SCA
# ---------------------------------------------------------
fig = make_subplots(specs=[[{"secondary_y": True}]])

# 1. Curva BT con Marcadores y Texto de Hitos SCA
fig.add_trace(
    go.Scatter(
        x=df_procesado["Minuto"],
        y=df_procesado["Temp Grano (°C)"],
        mode="lines+markers+text",
        name="BT (°C)",
        text=[str(h).split(". ")[-1] if ". " in str(h) else str(h) for h in df_procesado["Fase / Hito SCA"]],
        textposition="top center",
        textfont=dict(size=9, color="#8b0000"),
        line=dict(color="#d9534f", width=3),
        marker=dict(size=8, symbol="circle"),
        hovertemplate="<b>%{text}</b><br>Minuto: %{x}<br>BT: %{y}°C"
    ),
    secondary_y=False
)

# 2. Curva RoR
ror_numeric = [0.0 if r in ["-", "TP"] else float(r) for r in df_procesado["RoR (°C/min)"]]
fig.add_trace(
    go.Scatter(
        x=df_procesado["Minuto"],
        y=ror_numeric,
        mode="lines+markers",
        name="RoR (°C/min)",
        line=dict(color="#0275d8", width=2, dash="dash"),
        marker=dict(size=6, symbol="square"),
        hovertemplate="Minuto: %{x}<br>RoR: %{y}°C/min"
    ),
    secondary_y=True
)

# 3. Curva RPM Tambor
fig.add_trace(
    go.Scatter(
        x=df_procesado["Minuto"],
        y=df_procesado["RPM Tambor"],
        mode="lines+markers",
        name="RPM Tambor",
        line=dict(color="#5cb85c", width=2, dash="dot"),
        marker=dict(size=6, symbol="triangle-up"),
        hovertemplate="Minuto: %{x}<br>RPM: %{y}"
    ),
    secondary_y=True
)

# Configuración detallada de escalas y ejes
fig.update_xaxes(
    title_text="Tiempo (Minutos)",
    dtick=0.5,             # Escala en X cada 0.5 minutos
    tickangle=-45,
    showgrid=True,
    gridcolor="#EBEBEB"
)

fig.update_yaxes(
    title_text="Temperatura BT (°C)",
    secondary_y=False,
    range=[50, 230],
    dtick=10,              # Escala en Y1 cada 10 °C
    showgrid=True,
    gridcolor="#EBEBEB"
)

fig.update_yaxes(
    title_text="RoR (°C/min) / RPM / Aire% / Gas%",
    secondary_y=True,
    range=[0, 110],
    dtick=10,              # Escala en Y2 cada 10 unidades
    showgrid=False
)

fig.update_layout(
    title="Curva Termodinámica de Tueste: BT, RoR, RPM y Hitos SCA",
    hovermode="x unified",
    height=620,
    margin=dict(l=40, r=40, t=60, b=80),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# GENERACIÓN DE REPORTES PDF
# ---------------------------------------------------------
def generar_pdf_reporte(nombre, var, proc, dens, hum, p_obj, sab_obj, peso_c, peso_t, m_val, dtr, df):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "App Tueste - Sinfonia del Cafe", ln=True, align="C")
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 5, "Reporte Tecnico de Tostion SCA y Simulador Termodinamico", ln=True, align="C")
    pdf.ln(3)
    
    # 1. Ficha Técnica y Perfil Objetivo
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "1. Ficha del Cafe Verde, Perfil Objetivo y Rendimiento", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, f"Lote / Finca: {nombre} | Variedad: {var} | Proceso: {proc}", ln=True)
    pdf.cell(0, 5, f"Densidad: {dens} g/L | Humedad: {hum}% | Masa Carga: {peso_c}g", ln=True)
    pdf.cell(0, 5, f"Perfil Objetivo: {p_obj}", ln=True)
    pdf.cell(0, 5, f"Sabores Deseados: {sab_obj}", ln=True)
    pdf.cell(0, 5, f"Masa Obtenida: {peso_t}g | Merma: {m_val}% | DTR: {dtr}%", ln=True)
    pdf.ln(3)
    
    # 2. Gráfica Matplotlib para PDF
    fig_plt, ax1 = plt.subplots(figsize=(8, 4), dpi=150)
    ax1.plot(df["Minuto"], df["Temp Grano (°C)"], color='firebrick', marker='o', linewidth=2, label='BT (°C)')
    
    # Anotación de Hitos SCA en PDF
    for idx, r in df.iterrows():
        hito_txt = str(r["Fase / Hito SCA"]).split(". ")[-1] if ". " in str(r["Fase / Hito SCA"]) else str(r["Fase / Hito SCA"])
        ax1.annotate(hito_txt[:12], (r["Minuto"], r["Temp Grano (°C)"]),
                     textcoords="offset points", xytext=(0,5), ha='center', fontsize=4.5, color='darkred', rotation=30)
        
    ax1.set_xlabel('Tiempo (Minutos)', fontsize=8)
    ax1.set_ylabel('Temperatura BT (°C)', color='firebrick', fontsize=8)
    ax1.set_ylim(50, 230)
    
    max_m = max(df["Minuto"]) if len(df) > 0 else 12.0
    ax1.set_xticks([x/2.0 for x in range(0, int(max_m*2)+2)])
    ax1.set_yticks(range(50, 240, 10))
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    ax2 = ax1.twinx()
    r_vals = [0.0 if r in ["-", "TP"] else float(r) for r in df["RoR (°C/min)"]]
    ax2.plot(df["Minuto"], r_vals, color='royalblue', linestyle='--', marker='s', label='RoR (°C/min)')
    ax2.plot(df["Minuto"], df["RPM Tambor"], color='forestgreen', linestyle=':', marker='^', label='RPM')
    ax2.set_ylabel('RoR / RPM', color='black', fontsize=8)
    ax2.set_ylim(0, 110)
    ax2.set_yticks(range(0, 120, 10))
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=7)
    plt.title('Curva Termodinamica de Tueste (BT, RoR, RPM y Hitos SCA)', fontsize=9)
    plt.tight_layout()
    
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=150)
    img_buf.seek(0)
    plt.close(fig_plt)
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp.write(img_buf.getvalue())
        tmp_path = tmp.name
        
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "2. Grafica de Tueste con Hitos SCA", ln=True)
    pdf.image(tmp_path, x=10, y=pdf.get_y(), w=190)
    pdf.set_y(pdf.get_y() + 95)
    
    # 3. Bitácora
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "3. Bitacora Tabulada", ln=True)
    pdf.set_font("Arial", "B", 7)
    pdf.cell(12, 5, "Min", border=1)
    pdf.cell(16, 5, "BT (C)", border=1)
    pdf.cell(18, 5, "RoR(C/m)", border=1)
    pdf.cell(14, 5, "RPM", border=1)
    pdf.cell(15, 5, "Aire%", border=1)
    pdf.cell(15, 5, "Gas%", border=1)
    pdf.cell(100, 5, "Fase / Hito SCA", border=1, ln=True)
    
    pdf.set_font("Arial", "", 7)
    for idx, row in df.iterrows():
        pdf.cell(12, 4.5, str(row["Minuto"]), border=1)
        pdf.cell(16, 4.5, str(row["Temp Grano (°C)"]), border=1)
        pdf.cell(18, 4.5, str(row["RoR (°C/min)"]), border=1)
        pdf.cell(14, 4.5, str(row["RPM Tambor"]), border=1)
        pdf.cell(15, 4.5, str(row["Flujo Aire (%)"]), border=1)
        pdf.cell(15, 4.5, str(row["Potencia Gas (%)"]), border=1)
        pdf.cell(100, 4.5, str(row["Fase / Hito SCA"])[:50], border=1, ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

st.markdown("---")
st.markdown("### 📥 Exportar Reporte Técnico")
pdf_bytes = generar_pdf_reporte(
    nombre_lote, variedad, proceso, densidad, humedad,
    perfil_objetivo, sabores_deseados, peso_carga, peso_tostado,
    merma, dtr_val, df_procesado
)

st.download_button(
    label="📄 Descargar Reporte PDF Completo",
    data=pdf_bytes,
    file_name=f"Reporte_Tueste_{nombre_lote.replace(' ', '_')}.pdf",
    mime="application/pdf"
)
