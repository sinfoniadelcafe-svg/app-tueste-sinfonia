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
# BASE DE CONOCIMIENTO: MATRIZ DE COMBINACIÓN SCA
# (Variedad x Proceso de Beneficio)
# ---------------------------------------------------------
MATRIZ_SCA = {
    # GEISHA
    ("Geisha / Gesha", "Lavado (Washed)"): {
        "perfil": "Acidez Brillante y Complejidad Floral (Tueste Claro)",
        "sabores": "Jazmín, Flor de azahar, Bergamota, Lemongrass, Durazno blanco, Té verde",
        "estrategia": "Cuerpo sedoso y alta claridad (Clean cup). Tueste claro y ágil con DTR bajo (~12-14%) para preservar aromáticos volátiles."
    },
    ("Geisha / Gesha", "Honey (Amarillo / Rojo / Negro)"): {
        "perfil": "Acidez Brillante y Complejidad Floral (Tueste Claro)",
        "sabores": "Flor de limonero, Miel de azahar, Durazno en almíbar, Mandarina, Té blanco",
        "estrategia": "Dulcera acentuada y cuerpo cremoso. Transferencia de calor progresiva en Maillard para no caramelizar en exceso."
    },
    ("Geisha / Gesha", "Natural (Dry Process)"): {
        "perfil": "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "sabores": "Mango, Maracuyá, Mermelada de albaricoque, Fresa, Miel, Chicle",
        "estrategia": "Cuerpo jugoso y dulzura muy alta. Control estricto de gas inicial por alta reactividad de azúcares superficiales."
    },
    ("Geisha / Gesha", "Anaeróbico / Maceración Carbónica"): {
        "perfil": "Acidez Brillante y Complejidad Floral (Tueste Claro)",
        "sabores": "Papaya, Lichi, Flor de hibisco, Yogurt de durazno, Especias dulzonas",
        "estrategia": "Perfil exótico e intenso. Desarrollo moderado con aire alto en fase final para limpiar notas de fermentación."
    },

    # BOURBON / TYPICA
    ("Bourbon / Typica", "Lavado (Washed)"): {
        "perfil": "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "sabores": "Caramelo, Chocolate con leche, Manzana roja, Avellana, Caña de azúcar",
        "estrategia": "Taza clásica equilibrada y limpia. Tueste medio con Maillard moderado para resaltar la dulzura de la sacarosa."
    },
    ("Bourbon / Typica", "Honey (Amarillo / Rojo / Negro)"): {
        "perfil": "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "sabores": "Panela, Miel de maple, Ciruela amarilla, Almendra tostada, Higo",
        "estrategia": "Cuerpo denso y meloso. Cuidado en la fase de secado para garantizar homogeneidad térmica."
    },
    ("Bourbon / Typica", "Natural (Dry Process)"): {
        "perfil": "Cuerpo Denso / Chocolate y Caramelo (Tueste Medio-Oscuro)",
        "sabores": "Frutos del bosque, Arándano, Cacao amargo, Pasas, Vino tinto",
        "estrategia": "Cuerpo muy estructurado. RoR descendente constante para balancear la acidez vinosa."
    },
    ("Bourbon / Typica", "Anaeróbico / Maceración Carbónica"): {
        "perfil": "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "sabores": "Cereza al marasquino, Licor de cacao, Canela, Nuez moscada, Mermelada de mora",
        "estrategia": "Complejidad especiada. Tueste medio controlado para integrar armoniosamente las notas de fermentación."
    },

    # CATURRA / CASTILLO / COLOMBIA
    ("Caturra / Castillo / Colombia", "Lavado (Washed)"): {
        "perfil": "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "sabores": "Lima-limón, Caña de azúcar, Chocolate, Nuez, Naranja dulce",
        "estrategia": "Acidez cítrica brillante y excelente consistencia. Curva versátil estándar SCA."
    },
    ("Caturra / Castillo / Colombia", "Honey (Amarillo / Rojo / Negro)"): {
        "perfil": "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "sabores": "Durazno, Miel, Azúcar morena, Manzana roja, Chocolate dulce",
        "estrategia": "Dulzura acentuada. Buena conducción inicial aprovechando la alta densidad del grano."
    },
    ("Caturra / Castillo / Colombia", "Natural (Dry Process)"): {
        "perfil": "Cuerpo Denso / Chocolate y Caramelo (Tueste Medio-Oscuro)",
        "sabores": "Mora, Cereza, Chocolate negro, Vino tinto, Pasas",
        "estrategia": "Gran cuerpo y dulzor frutal. Reducción de gas antes del 1st crack para evitar tueste arrebatado."
    },
    ("Caturra / Castillo / Colombia", "Anaeróbico / Maceración Carbónica"): {
        "perfil": "Perfil Expresso / Dulce y Resaltado de Cuerpo",
        "sabores": "Yogurt de fresa, Maracuyá, Panela, Chocolate amargo, Clavo de olor",
        "estrategia": "Perfil exótico e intenso. Fase de caramelización ajustada para maximizar dulzor."
    },

    # BOURBON ROSADO / SIDRA
    ("Bourbon Rosado / Sidra", "Lavado (Washed)"): {
        "perfil": "Acidez Brillante y Complejidad Floral (Tueste Claro)",
        "sabores": "Rosa, Flor de cerezo, Toronja rosada, Melocotón, Té de jazmín",
        "estrategia": "Acidez tartárica muy elegante. Requiere tueste claro de alta convección para preservar aceites aromáticos."
    },
    ("Bourbon Rosado / Sidra", "Honey (Amarillo / Rojo / Negro)"): {
        "perfil": "Acidez Brillante y Complejidad Floral (Tueste Claro)",
        "sabores": "Cereza rosada, Miel de flores, Papaya, Naranja sangría, Caramelo suave",
        "estrategia": "Dulzura floral alta. Transferencia convectiva óptima."
    },
    ("Bourbon Rosado / Sidra", "Natural (Dry Process)"): {
        "perfil": "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "sabores": "Frambuesa, Granadilla, Maracuyá, Chocolate blanco, Vinoso elegante",
        "estrategia": "Cuerpo sedoso y perfil tropical. RoR suave y sostenido al final."
    },
    ("Bourbon Rosado / Sidra", "Anaeróbico / Maceración Carbónica"): {
        "perfil": "Acidez Brillante y Complejidad Floral (Tueste Claro)",
        "sabores": "Lichi, Chicle de fresa, Mantequilla dulce, Rosa, Maracuyá",
        "estrategia": "Aromas extremadamente volátiles. Incrementar aireación en DTR."
    },

    # PACAMARA / MARAGOGIPE
    ("Pacamara / Maragogipe", "Lavado (Washed)"): {
        "perfil": "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "sabores": "Chocolate oscuro, Nuez moscada, Toronja, Frutas tropicales, Cedro noble",
        "estrategia": "Grano de gran tamaño (elefante). Requiere aplicación de calor homogénea y secado ligeramente más largo."
    },
    ("Pacamara / Maragogipe", "Honey (Amarillo / Rojo / Negro)"): {
        "perfil": "Cuerpo Denso / Chocolate y Caramelo (Tueste Medio-Oscuro)",
        "sabores": "Miel oscura, Albaricoque seco, Cacao 70%, Caña, Avellana tostada",
        "estrategia": "Cuerpo muy estructurado. Monitorear penetración de calor en el centro del grano."
    },
    ("Pacamara / Maragogipe", "Natural (Dry Process)"): {
        "perfil": "Cuerpo Denso / Chocolate y Caramelo (Tueste Medio-Oscuro)",
        "sabores": "Ciruela pasa, Mango maduro, Licor de cacao, Tabaco dulce, Especias",
        "estrategia": "Rico en azúcares complejos. Cargar con temperatura moderada para evitar carao externo."
    },
    ("Pacamara / Maragogipe", "Anaeróbico / Maceración Carbónica"): {
        "perfil": "Perfil Expresso / Dulce y Resaltado de Cuerpo",
        "sabores": "Higo maduro, Ron, Chocolate especiado, Cereza, Pimienta dulce",
        "estrategia": "Intensidad sensorial alta. Extensión moderada de DTR."
    },

    # SL28 / SL38
    ("SL28 / SL38", "Lavado (Washed)"): {
        "perfil": "Acidez Brillante y Complejidad Floral (Tueste Claro)",
        "sabores": "Grosella negra (Blackcurrant), Toronja, Tomate dulce, Vino tinto joven, Caña",
        "estrategia": "Acidez fosfórica brillante icónica de Kenia. Tueste claro de alta energía convectiva."
    },
    ("SL28 / SL38", "Honey (Amarillo / Rojo / Negro)"): {
        "perfil": "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "sabores": "Mora azul, Ciruela, Miel de caña, Toronja dulce, Chocolate al 60%",
        "estrategia": "Equilibrio entre acidez fosfórica y dulzor de miel."
    },
    ("SL28 / SL38", "Natural (Dry Process)"): {
        "perfil": "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "sabores": "Casis, Cereza negra, Mermelada de mora, Cacao, Vinoso frutal",
        "estrategia": "Frutos oscuros jugosos. Controlar RoR para mantener la brillantez de la acidez."
    },
    ("SL28 / SL38", "Anaeróbico / Maceración Carbónica"): {
        "perfil": "Acidez Brillante y Complejidad Floral (Tueste Claro)",
        "sabores": "Arándano azul, Maracuyá, Vino Oporto, Tamarindo, Hibisco",
        "estrategia": "Sabor explosivo. Tueste rápido con alta conducción/convección inicial."
    },

    # OTRO / MEZCLA
    ("Otro / Mezcla", "Lavado (Washed)"): {
        "perfil": "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "sabores": "Caramelo, Cítricos dulces, Frutos secos, Chocolate",
        "estrategia": "Curva estándar balanceada."
    },
    ("Otro / Mezcla", "Honey (Amarillo / Rojo / Negro)"): {
        "perfil": "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "sabores": "Miel, Panela, Frutas amarillas, Almendras",
        "estrategia": "Desarrollo medio equilibrado."
    },
    ("Otro / Mezcla", "Natural (Dry Process)"): {
        "perfil": "Cuerpo Denso / Chocolate y Caramelo (Tueste Medio-Oscuro)",
        "sabores": "Frutos rojos, Chocolate maduro, Vino, Pasas",
        "estrategia": "Tueste con mayor desarrollo de Maillard y cuerpo."
    },
    ("Otro / Mezcla", "Anaeróbico / Maceración Carbónica"): {
        "perfil": "Perfil Expresso / Dulce y Resaltado de Cuerpo",
        "sabores": "Frutas exóticas, Especias, Licor, Yogurt",
        "estrategia": "Cuidadoso control térmico para moderar acidez fermentada."
    }
}

# ---------------------------------------------------------
# MOTOR DE SIMULACIÓN TERMODINÁMICA
# ---------------------------------------------------------
def simular_curva_termodinamica(df_input, temp_carga, rpm_optima):
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
            tp_temp = 92.0 + (gas - 80.0) * 0.12 + (rpm - rpm_optima) * 0.08
            temps.append(round(tp_temp, 1))
        else:
            base_ror = 3.0 + (gas / 100.0) * 20.0
            
            rpm_diff = abs(rpm - rpm_optima)
            rpm_eff = 1.0 if rpm_diff <= 4 else max(0.60, 1.0 - (rpm_diff - 4) * 0.02)
                
            if air <= 30:
                air_eff = 0.85 + (air / 30.0) * 0.10
            elif air <= 65:
                air_eff = 0.95 + ((air - 30) / 35.0) * 0.10
            else:
                air_eff = 1.05 - ((air - 65) / 35.0) * 0.28
                
            temp_gradient = max(0.35, 1.0 - (curr_temp - 90.0) / 215.0)
            
            calc_ror = round(base_ror * rpm_eff * air_eff * temp_gradient, 1)
            next_temp = round(curr_temp + calc_ror * dt, 1)
            
            temps.append(next_temp)
            rors.append(calc_ror)
            
    df["Temp Grano (°C)"] = temps
    df["RoR (°C/min)"] = rors
    return df

# ---------------------------------------------------------
# BARRA LATERAL: FICHA Y PERFIL OBJETIVO DINÁMICO
# ---------------------------------------------------------
st.sidebar.header("📋 Ficha del Café Verde")
nombre_lote = st.sidebar.text_input("Nombre del Lote / Finca", "Finca La Esperanza")

# Menú desplegable de Variedades
opciones_variedad = [
    "Geisha / Gesha",
    "Bourbon / Typica",
    "Caturra / Castillo / Colombia",
    "Bourbon Rosado / Sidra",
    "Pacamara / Maragogipe",
    "SL28 / SL38",
    "Otro / Mezcla"
]
variedad = st.sidebar.selectbox("Variedad (Genotipo)", opciones_variedad, index=0)

# Menú desplegable de Procesos de Beneficio
opciones_proceso = [
    "Lavado (Washed)",
    "Honey (Amarillo / Rojo / Negro)",
    "Natural (Dry Process)",
    "Anaeróbico / Maceración Carbónica"
]
proceso = st.sidebar.selectbox("Proceso de Beneficio", opciones_proceso, index=0)

densidad = st.sidebar.number_input("Densidad (g/L)", value=680, step=5)
humedad = st.sidebar.number_input("Humedad (%)", value=11.5, step=0.1)

# Obtener recomendación automática desde la Matriz SCA
info_sca = MATRIZ_SCA.get(
    (variedad, proceso),
    {
        "perfil": "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
        "sabores": "Caramelo, Cítricos dulces, Frutos secos, Chocolate",
        "estrategia": "Ajustar curva según densidad y humedad."
    }
)

st.sidebar.header("🎯 Perfil Objetivo y Sabores Deseados")

opciones_perfil = [
    "Acidez Brillante y Complejidad Floral (Tueste Claro)",
    "Balance Medio / Dulzor y Frutas Redondas (Tueste Medio)",
    "Cuerpo Denso / Chocolate y Caramelo (Tueste Medio-Oscuro)",
    "Perfil Expresso / Dulce y Resaltado de Cuerpo"
]

# Seleccionar el índice predeterminado según la sugerencia de la matriz
idx_sugerido = opciones_perfil.index(info_sca["perfil"]) if info_sca["perfil"] in opciones_perfil else 1

perfil_objetivo = st.sidebar.selectbox(
    "Tipo de Perfil de Tostión",
    opciones_perfil,
    index=idx_sugerido
)

sabores_deseados = st.sidebar.text_input(
    "Sabores / Descriptores a Percibir",
    value=info_sca["sabores"]
)

st.sidebar.header("⚙️ Configuración del Batch")
peso_carga = st.sidebar.number_input("Peso de Carga (g)", value=1000, step=50)
temp_carga = st.sidebar.number_input("Temp. Carga / Drop (°C)", value=188.1, step=0.5)
rpm_objetivo = st.sidebar.slider("RPM Óptimas Tostadora", min_value=40, max_value=80, value=61)

modo_calculo = st.sidebar.radio(
    "Modo de Operación",
    ["🔥 Simulador Térmico Dinámico (Física de Tostión)", "📝 Bitácora de Campo (Ingreso Manual Libre)"]
)

# ---------------------------------------------------------
# GENERADOR DE PRESETS SEGÚN EL PERFIL ELEGIDO
# ---------------------------------------------------------
def obtener_preset_perfil(perfil):
    if "Acidez Brillante" in perfil:
        return {
            "Minuto": [0.0, 1.0, 2.0, 3.0, 4.0, 4.5, 5.0, 5.8, 6.5, 7.2, 8.0, 8.6, 9.2, 9.8],
            "Fase / Hito SCA": [
                "01. Carga", "02. TP", "03. Secado", "04. Pico RoR", "05. Vaporización",
                "06. Amarillo", "07. In. Maillard", "08. Aromas", "09. Carameliz.",
                "10. Pre-Crack", "11. Presión Alta", "12. 1st Crack", "13. DTR", "14. Drop"
            ],
            "Temp Grano (°C)": [188.1, 92.5, 110.0, 128.0, 142.0, 150.0, 158.0, 170.0, 180.0, 188.0, 194.0, 198.0, 202.0, 205.0],
            "Color del Grano": ["Verde", "Verde C.", "Verde M.", "Amarillo V.", "Amarillo P.", "Amarillo D.", "Canela C.", "Marrón A.", "Marrón P.", "Marrón M.", "Marrón I.", "Marrón City", "Marrón City", "Marrón Claro"],
            "RPM Tambor": [63]*14,
            "Flujo Aire (%)": [35, 35, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90],
            "Potencia Gas (%)": [85, 85, 85, 80, 75, 70, 65, 55, 45, 35, 25, 20, 15, 10]
        }
    elif "Cuerpo Denso" in perfil:
        return {
            "Minuto": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 10.8, 11.8, 12.8],
            "Fase / Hito SCA": [
                "01. Carga", "02. TP", "03. Secado", "04. Pico RoR", "05. Vaporización",
                "06. Amarillo", "07. In. Maillard", "08. Aromas", "09. Carameliz.",
                "10. Pre-Crack", "11. Presión Alta", "12. 1st Crack", "13. DTR", "14. Drop"
            ],
            "Temp Grano (°C)": [188.1, 90.0, 105.0, 120.0, 134.0, 148.0, 160.0, 172.0, 182.0, 192.0, 200.0, 204.0, 210.0, 214.0],
            "Color del Grano": ["Verde", "Verde C.", "Verde M.", "Amarillo V.", "Amarillo P.", "Amarillo D.", "Canela C.", "Marrón A.", "Marrón P.", "Marrón M.", "Marrón I.", "Marrón City", "Marrón Full City", "Marrón Oscuro"],
            "RPM Tambor": [60]*14,
            "Flujo Aire (%)": [25, 25, 30, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80],
            "Potencia Gas (%)": [75, 75, 75, 70, 70, 65, 60, 55, 50, 45, 35, 30, 25, 15]
        }
    else:
        return {
            "Minuto": [0.0, 1.0, 2.0, 3.0, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 9.75, 10.5, 11.5],
            "Fase / Hito SCA": [
                "01. Carga", "02. TP", "03. Secado", "04. Pico RoR", "05. Vaporización",
                "06. Amarillo", "07. In. Maillard", "08. Aromas", "09. Carameliz.",
                "10. Pre-Crack", "11. Presión Alta", "12. 1st Crack", "13. DTR", "14. Drop"
            ],
            "Temp Grano (°C)": [188.1, 91.0, 108.0, 125.0, 138.0, 145.0, 152.0, 165.0, 176.0, 186.0, 195.0, 200.0, 205.0, 210.0],
            "Color del Grano": ["Verde", "Verde C.", "Verde M.", "Amarillo V.", "Amarillo P.", "Amarillo D.", "Canela C.", "Marrón A.", "Marrón P.", "Marrón M.", "Marrón I.", "Marrón City", "Marrón City+", "Marrón Choc."],
            "RPM Tambor": [61, 61, 61, 61, 61, 61, 63, 63, 65, 65, 66, 66, 66, 66],
            "Flujo Aire (%)": [30, 30, 30, 30, 40, 40, 50, 50, 60, 60, 70, 80, 85, 90],
            "Potencia Gas (%)": [80, 80, 80, 80, 75, 75, 70, 65, 60, 55, 45, 35, 25, 20]
        }

datos_preset = obtener_preset_perfil(perfil_objetivo)
df_base = pd.DataFrame(datos_preset)

# ---------------------------------------------------------
# PANEL PRINCIPAL: TARJETA EXPLICATIVA Y MATRIZ SCA
# ---------------------------------------------------------
st.markdown("### 🧪 Diagnóstico de Selección: Variedad x Proceso de Beneficio")

col_info1, col_info2 = st.columns([2, 1])

with col_info1:
    st.success(
        f"**Selección Actual:** `{variedad}` | Proceso: `{proceso}`\n\n"
        f"🎯 **Perfil Recomendado SCA:** {info_sca['perfil']}\n\n"
        f"☕ **Notas Sensoriales Esperadas:** {info_sca['sabores']}\n\n"
        f"🔥 **Estrategia Térmica:** {info_sca['estrategia']}"
    )

with col_info2:
    st.info(
        "💡 **Estándar SCA:**\n\n"
        "La **Variedad** define los precursores genéticos (azúcares/ácidos) y la **Beneficiación** altera la conductividad y solubilidad del grano. ¡Ajusta tu receta acorde!"
    )

# EXPANDER DE LA MATRIZ DE COMBINACIÓN COMPLETA
with st.expander("📚 Ver Matriz de Combinación SCA Completa (Todas las Variedades y Beneficios)"):
    filas_matriz = []
    for (var_k, proc_k), v_data in MATRIZ_SCA.items():
        filas_matriz.append({
            "Variedad": var_k,
            "Proceso": proc_k,
            "Perfil Recomendado": v_data["perfil"],
            "Sabores Esperados": v_data["sabores"],
            "Estrategia de Tueste": v_data["estrategia"]
        })
    df_matriz_full = pd.DataFrame(filas_matriz)
    st.dataframe(df_matriz_full, use_container_width=True)

# ---------------------------------------------------------
# INTERFAZ Y TABLA INTERACTIVA
# ---------------------------------------------------------
st.markdown("---")
st.markdown("### 📊 Control y Bitácora Interactiva")

df_editado = st.data_editor(
    df_base,
    num_rows="dynamic",
    use_container_width=True,
    key=f"editor_{variedad}_{proceso}_{perfil_objetivo}",
    column_config={
        "Minuto": st.column_config.NumberColumn("Minuto", format="%.2f"),
        "Temp Grano (°C)": st.column_config.NumberColumn("BT (°C)", format="%.1f"),
        "RPM Tambor": st.column_config.NumberColumn("RPM Tambor", min_value=30, max_value=100, step=1),
        "Flujo Aire (%)": st.column_config.NumberColumn("Aire %", min_value=0, max_value=100, step=5),
        "Potencia Gas (%)": st.column_config.NumberColumn("Gas %", min_value=0, max_value=100, step=5),
    }
)

# ---------------------------------------------------------
# PROCESAMIENTO ROBUSTO SEGÚN MODO SELECCIONADO
# ---------------------------------------------------------
if "Simulador" in modo_calculo:
    df_procesado = simular_curva_termodinamica(df_editado, temp_carga, rpm_objetivo)
else:
    df_procesado = df_editado.copy()
    
    if "Temp Grano (°C)" not in df_procesado.columns:
        df_procesado["Temp Grano (°C)"] = 100.0
        
    rors = ["-", "TP"]
    for i in range(2, len(df_procesado)):
        try:
            dt = float(df_procesado.loc[i, "Minuto"]) - float(df_procesado.loc[i-1, "Minuto"])
            dtemp = float(df_procesado.loc[i, "Temp Grano (°C)"]) - float(df_procesado.loc[i-1, "Temp Grano (°C)"])
            rors.append(round(dtemp / dt, 1) if dt > 0 else 0.0)
        except (KeyError, ValueError, TypeError):
            rors.append(0.0)
            
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

min_1st_crack = df_procesado.loc[df_procesado["Fase / Hito SCA"].astype(str).str.contains("1st Crack|Primer Craqueo", na=False), "Minuto"]
min_drop = float(df_procesado["Minuto"].iloc[-1]) if len(df_procesado) > 0 else 1.0

if not min_1st_crack.empty:
    t_1st = float(min_1st_crack.values[0])
    dev_time = min_drop - t_1st
    dtr_val = round((dev_time / min_drop) * 100, 1) if min_drop > 0 else 0
else:
    dtr_val = 15.0

col_p3.metric("DTR (Tiempo Desarrollo)", f"{dtr_val} %")
ror_final = df_procesado["RoR (°C/min)"].iloc[-1] if len(df_procesado) > 0 else 0.0
col_p4.metric("RoR Final", f"{ror_final} °C/min")

# ---------------------------------------------------------
# GRÁFICA PLOTLY OPTIMIZADA
# ---------------------------------------------------------
fig = make_subplots(specs=[[{"secondary_y": True}]])

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

ror_numeric = [0.0 if str(r) in ["-", "TP", "nan"] else float(r) for r in df_procesado["RoR (°C/min)"]]
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

fig.update_xaxes(
    title_text="Tiempo (Minutos)",
    dtick=0.5,
    tickangle=-45,
    showgrid=True,
    gridcolor="#EBEBEB"
)

fig.update_yaxes(
    title_text="Temperatura BT (°C)",
    secondary_y=False,
    range=[50, 230],
    dtick=10,
    showgrid=True,
    gridcolor="#EBEBEB"
)

fig.update_yaxes(
    title_text="RoR (°C/min) / RPM / Aire% / Gas%",
    secondary_y=True,
    range=[0, 110],
    dtick=10,
    showgrid=False
)

fig.update_layout(
    title=f"Curva Termodinámica de Tueste: {variedad} ({proceso})",
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
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "App Tueste - Sinfonia del Cafe", ln=True, align="C")
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 5, "Reporte Tecnico de Tostion SCA y Simulador Termodinamico", ln=True, align="C")
    pdf.ln(3)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "1. Ficha del Cafe Verde, Perfil Objetivo y Rendimiento", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, f"Lote / Finca: {nombre} | Variedad: {var} | Proceso: {proc}", ln=True)
    pdf.cell(0, 5, f"Densidad: {dens} g/L | Humedad: {hum}% | Masa Carga: {peso_c}g", ln=True)
    pdf.cell(0, 5, f"Perfil Objetivo: {p_obj}", ln=True)
    pdf.cell(0, 5, f"Sabores Deseados: {sab_obj}", ln=True)
    pdf.cell(0, 5, f"Masa Obtenida: {peso_t}g | Merma: {m_val}% | DTR: {dtr}%", ln=True)
    pdf.ln(3)
    
    fig_plt, ax1 = plt.subplots(figsize=(8, 4), dpi=150)
    ax1.plot(df["Minuto"], df["Temp Grano (°C)"], color='firebrick', marker='o', linewidth=2, label='BT (°C)')
    
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
    r_vals = [0.0 if str(r) in ["-", "TP", "nan"] else float(r) for r in df["RoR (°C/min)"]]
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
