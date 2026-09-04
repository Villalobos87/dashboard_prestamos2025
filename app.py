import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import JsCode
from datetime import datetime
from sqlalchemy import create_engine
from streamlit_autorefresh import st_autorefresh   # ✅ Import correcto

# =========================
# CONFIGURACIÓN INICIAL
# =========================
st.set_page_config(page_title="Dashboard Préstamos", layout="wide")


# 🔄 Auto-refresco cada 50 segundos
count = st_autorefresh(interval=50 * 1000, limit=None, key="datarefresh")

# --- Conexión a PostgreSQL usando Secrets ---
DB_USER = "djangouser"
DB_PASS = "mHihqeccaRH1CMjB4jJZj1wZSVwHoO8j"
DB_HOST = "dpg-d765klea2pns73eh70b0-a.oregon-postgres.render.com"
DB_PORT = "5432"
DB_NAME = "djangocrud_har8_xhoj"

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
)

st.success("✅ Conexión establecida con PostgreSQL en Render")
st.caption(f"🔄 Datos actualizados automáticamente cada 30 segundos (recarga #{count})")

# =========================
# CONSULTA DE DATOS
# =========================
query = """
SELECT 
       c.id AS "ID Cuota",
       p.id AS "ID Prestamo",
       c.numero AS "Número", 
       c.fecha_pago AS "Fecha", 
       t.nombre AS "Nombre y Apellido", 
       t.campus AS "Campus", 
       c.principal AS "Principal", 
       c.interes AS "Interes", 
       c.comision AS "Comisión", 
       c.monto_total AS "Cuota", 
       c.estado AS "Estado", 
       c.cheque AS "Cheque", 
       p.fecha_inicio AS "Fecha de Inicio", 
       p.fecha_final AS "Fecha de Finalización" 
FROM prestamos_cuota c 
JOIN prestamos_prestamo p 
     ON c.prestamo_id = p.id 
JOIN prestamos_trabajador t 
     ON p.trabajador_id = t.id;
"""
df = pd.read_sql(query, engine)

# --- Preprocesamiento general ---
df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
df["Nombre y Apellido"] = df["Nombre y Apellido"].astype(str)
df["Campus"] = df["Campus"].astype(str)
df["Estado"] = df["Estado"].astype(str)
for col in ["Principal", "Interes", "Comisión", "Cuota"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# =========================
# SIDEBAR FILTROS
# =========================
st.sidebar.header("Filtros")
estado = st.sidebar.multiselect("Estado", df["Estado"].unique(), default=df["Estado"].unique())
campus = st.sidebar.multiselect("Campus", df["Campus"].unique(), default=df["Campus"].unique())
df_filtrado = df[(df["Estado"].isin(estado)) & (df["Campus"].isin(campus))]

st.title("📊 Dashboard de Préstamos")

# =========================
# MÉTRICAS GENERALES
# =========================
total_prestado  = df_filtrado["Principal"].sum()
total_interes   = df_filtrado["Interes"].sum()
total_comision  = df_filtrado["Comisión"].sum()
gan_total       = total_interes + total_comision

c1,c2,c3,c4 = st.columns(4)
c1.metric("💰 Total Prestado"   ,f"${total_prestado:,.2f}")
c2.metric("💸 Total Comisión"   ,f"${total_comision:,.2f}")
c3.metric("📈 Total Interés"    ,f"${total_interes:,.2f}")
c4.metric("🔥 Ganancias Totales",f"${gan_total:,.2f}")

st.markdown("---")

# =========================
# RESUMEN MENSUAL
# =========================
meses_ingles  = ["January","February","March","April","May","June","July","August","September","October","November","December"]
meses_espanol = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
dic_meses     = dict(zip(meses_ingles, meses_espanol))

df_filtrado["Año"]      = df_filtrado["Fecha"].dt.year
df_filtrado["Mes_Num"]  = df_filtrado["Fecha"].dt.month
df_filtrado["Mes"]      = df_filtrado["Fecha"].dt.strftime("%B").map(dic_meses)
df_filtrado["Mes"]      = pd.Categorical(df_filtrado["Mes"], categories=meses_espanol, ordered=True)

resumen_mensual = (
    df_filtrado
      .groupby(["Año","Mes_Num","Mes"], observed=True)[["Interes","Comisión"]]
      .sum()
      .reset_index()
)
resumen_mensual["Total_Ganancias"] = resumen_mensual["Interes"] + resumen_mensual["Comisión"]
resumen_mensual = resumen_mensual.sort_values(["Año","Mes_Num"])
resumen_mensual["Mes_Año"] = resumen_mensual["Mes"].astype(str) + " " + resumen_mensual["Año"].astype(str)

anos_disponibles = sorted(resumen_mensual['Año'].unique())
anio_actual      = datetime.now().year

col1, col2 = st.columns([2,1])
with col1:
    if anio_actual in anos_disponibles:
        ano_seleccionado = st.selectbox("Selecciona el Año", anos_disponibles, index=anos_disponibles.index(anio_actual))
    else:
        ano_seleccionado = st.selectbox("Selecciona el Año", anos_disponibles, index=len(anos_disponibles)-1)

resumen_filtrado = resumen_mensual[resumen_mensual['Año'] == ano_seleccionado]
total_ganancias_anual = resumen_filtrado["Total_Ganancias"].sum()

with col2:
    st.metric(label="💰 Total del Año", value=f"{total_ganancias_anual:,.2f}")

fig_bar = px.bar(
    resumen_filtrado,
    x="Mes_Año",
    y="Total_Ganancias",
    text="Total_Ganancias",
    color="Total_Ganancias",
    title=f"📈 Ganancias Mensuales ({ano_seleccionado})"
)
fig_bar.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
fig_bar.update_layout(height=500, showlegend=False, coloraxis_showscale=False)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# =========================
# MÉTRICAS ADICIONALES
# =========================
total_cuota_cancelada = df[df["Estado"]=="Pagado"]["Cuota"].sum()
Capital_Inicial       = 11000.00
Ganancias_Entregadas  = 11964.43
Efectivo              = total_cuota_cancelada + Capital_Inicial - total_prestado - Ganancias_Entregadas
Pendiente_Recuperar   = df[df["Estado"]=="Pendiente"]["Cuota"].sum()

c1,c2,c3,c4 = st.columns(4)
c1.metric("💵 Yanina Orochena",f"${Efectivo:,.2f}")
c2.metric("⏳ Por Recuperar" ,f"${Pendiente_Recuperar:,.2f}")
c3.metric("💼 Capital"       ,f"${Capital_Inicial:,.2f}")
c4.metric("📤 Rodrigo Gurdian",f"${Ganancias_Entregadas:,.2f}")

st.markdown("---")

# =========================
# DETALLE DE PRÉSTAMOS
# =========================
st.subheader("📋 Detalle de Préstamos")
df_detalle = df_filtrado[df_filtrado["Estado"]=="Pendiente"].copy()
df_detalle["Fecha"] = df_detalle["Fecha"].dt.strftime("%Y-%m-%d")
for col in ["Principal","Comisión","Interes","Cuota"]:
    df_detalle[col] = df_detalle[col].map(lambda x: f"{x:,.2f}")

cols_quitar = ["Cheque","Fecha de Inicio","Fecha de Finalización","Año","Mes_Num","Mes"]
df_detalle  = df_detalle.drop(columns=[c for c in cols_quitar if c in df_detalle.columns])

g = GridOptionsBuilder.from_dataframe(df_detalle)
g.configure_default_column(filter=True, sortable=True, resizable=True, editable=False)

# Estilo de la columna Estado
g.configure_column(
    "Estado",
    cellStyle=JsCode("function(params){return {'backgroundColor':'#FFF3CD','color':'#856404'};}")
)

# Aumentar ancho de columnas específicas
g.configure_column("id", minWidth=100)
g.configure_column("Nombre y Apellido", minWidth=250)
g.configure_column("Campus", minWidth=150)
g.configure_column("Fecha", minWidth=120)
g.configure_column("Principal", minWidth=120)
g.configure_column("Comisión", minWidth=120)
g.configure_column("Interes", minWidth=120)
g.configure_column("Cuota", minWidth=120)
g.configure_column("Estado", minWidth=120)


g.configure_side_bar()
g.configure_pagination(paginationPageSize=20)
tbl_opts = g.build()

AgGrid(
    df_detalle, 
    gridOptions=tbl_opts, 
    enable_enterprise_modules=True,
    fit_columns_on_grid_load=True, 
    allow_unsafe_jscode=True, 
    theme="alpine", 
    height=500
)

st.markdown("---")

# =========================
# GRÁFICO DE GANANCIAS POR CAMPUS
# =========================
gan_campus = df_filtrado.groupby("Campus")[["Interes","Comisión"]].sum().reset_index()
gan_campus["Total_Ganancias"] = gan_campus["Interes"] + gan_campus["Comisión"]

fig_pie = px.pie(
    gan_campus,
    names="Campus",
    values="Total_Ganancias",
    title="📊 Distribución de Ganancias por Campus",
    color_discrete_sequence=px.colors.qualitative.Pastel,
    hole=0
)
fig_pie.update_traces(
    texttemplate="%{label}: %{value:,.2f} (%{percent})",
    hovertemplate="%{label}<br>Ganancias: %{value:,.2f}<br>%{percent}",
    pull=[0.05]*len(gan_campus)
)
fig_pie.update_layout(title_font_size=24, height=700)
st.plotly_chart(fig_pie, use_container_width=True)

# =========================
# 📋 RESUMEN POR TRABAJADOR
# =========================
st.markdown("---")
st.subheader("📋 Resumen de Préstamos")


# ==========================================================
# 🪟 VENTANA EMERGENTE - HISTORIAL
# ==========================================================
@st.dialog("📋 Historial de Préstamos", width="large")
def mostrar_historial(trabajador):

    st.markdown(f"## 👤 {trabajador}")

    # Buscar todos los registros del trabajador
    historial = df[
        df["Nombre y Apellido"] == trabajador
    ].copy()

    if historial.empty:
        st.warning("No se encontraron préstamos para este trabajador.")
        return

    # ======================================================
    # MÉTRICAS
    # ======================================================

    total_prestado = historial["Principal"].sum()
    total_interes = historial["Interes"].sum()
    total_comision = historial["Comisión"].sum()
    total_cuotas = historial["Cuota"].sum()

    cuotas_pagadas = (
        historial["Estado"] == "Pagado"
    ).sum()

    cuotas_pendientes = (
        historial["Estado"] == "Pendiente"
    ).sum()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "💰 Total Prestado",
        f"${total_prestado:,.2f}"
    )

    c2.metric(
        "📈 Total Interés",
        f"${total_interes:,.2f}"
    )

    c3.metric(
        "💵 Total Comisión",
        f"${total_comision:,.2f}"
    )

    c4.metric(
        "💳 Total Cuotas",
        f"${total_cuotas:,.2f}"
    )

    st.markdown("---")

    c5, c6 = st.columns(2)

    c5.metric(
        "✅ Cuotas Pagadas",
        cuotas_pagadas
    )

    c6.metric(
        "⏳ Cuotas Pendientes",
        cuotas_pendientes
    )

    st.markdown("---")

    # ======================================================
    # HISTORIAL DE PRÉSTAMOS
    # ======================================================

    st.markdown("### 💼 Préstamos")

    prestamos = (
    historial[
        [
            "ID Prestamo",
            "Fecha de Inicio",
            "Fecha de Finalización"
        ]
    ]
    .drop_duplicates()
    .copy()
)

    # ======================================================
    # MOSTRAR CADA PRÉSTAMO
    # ======================================================

    for _, prestamo in prestamos.iterrows():

        id_prestamo = prestamo["ID Prestamo"]

        fecha_inicio = prestamo["Fecha de Inicio"]
        fecha_final = prestamo["Fecha de Finalización"]

        cuotas_prestamo = historial[
            historial["ID Prestamo"] == id_prestamo
        ].copy()

        principal = cuotas_prestamo["Principal"].sum()
        interes = cuotas_prestamo["Interes"].sum()
        comision = cuotas_prestamo["Comisión"].sum()
        cuota_total = cuotas_prestamo["Cuota"].sum()

        pagadas = (
            cuotas_prestamo["Estado"] == "Pagado"
        ).sum()

        pendientes = (
            cuotas_prestamo["Estado"] == "Pendiente"
        ).sum()

        # ==================================================
        # EXPANDER
        # ==================================================

        with st.expander(
            f"📄 Préstamo #{id_prestamo}",
            expanded=False
        ):

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "💰 Principal",
                f"${principal:,.2f}"
            )

            c2.metric(
                "📈 Interés",
                f"${interes:,.2f}"
            )

            c3.metric(
                "💵 Comisión",
                f"${comision:,.2f}"
            )

            c4.metric(
                "💳 Cuotas",
                f"${cuota_total:,.2f}"
            )

            st.markdown("---")

            c1, c2 = st.columns(2)

            c1.write(
                f"📅 **Inicio:** {fecha_inicio}"
            )

            c2.write(
                f"📅 **Finalización:** {fecha_final}"
            )

            st.markdown("---")

            c1, c2 = st.columns(2)

            c1.metric(
                "✅ Pagadas",
                pagadas
            )

            c2.metric(
                "⏳ Pendientes",
                pendientes
            )

            st.markdown("#### 📋 Detalle de Cuotas")

            detalle = cuotas_prestamo.copy()

            # ----------------------------------------------
            # FORMATO FECHA
            # ----------------------------------------------

            detalle["Fecha"] = pd.to_datetime(
                detalle["Fecha"],
                errors="coerce"
            ).dt.strftime("%Y-%m-%d")

            # ----------------------------------------------
            # COLUMNAS
            # ----------------------------------------------

            columnas = [
                "Número",
                "Fecha",
                "Principal",
                "Interes",
                "Comisión",
                "Cuota",
                "Estado",
                "Cheque"
            ]

            columnas = [
                col
                for col in columnas
                if col in detalle.columns
            ]

            detalle = detalle[columnas]

            # ----------------------------------------------
            # FORMATO DINERO
            # ----------------------------------------------

            for col in [
                "Principal",
                "Interes",
                "Comisión",
                "Cuota"
            ]:

                if col in detalle.columns:

                    detalle[col] = detalle[col].apply(
                        lambda x:
                            f"${x:,.2f}"
                            if pd.notna(x)
                            else "$0.00"
                    )

            st.dataframe(
                detalle,
                use_container_width=True,
                hide_index=True
            )


# ==========================================================
# 🧮 RESUMEN POR TRABAJADOR
# ==========================================================

resumen_trabajador = (
    df_filtrado
    .groupby(
        "Nombre y Apellido",
        observed=True
    )
    .agg(

        Cuotas_Pendientes=(
            "Estado",
            lambda x: (x == "Pendiente").sum()
        ),

        Total_Prestado=(
            "Principal",
            "sum"
        ),

        Total_Interes=(
            "Interes",
            "sum"
        ),

        Total_Comision=(
            "Comisión",
            "sum"
        )
    )
    .reset_index()
)


# ==========================================================
# 📈 TOTAL GANANCIAS
# ==========================================================

resumen_trabajador["Total_Ganancias"] = (
    resumen_trabajador["Total_Interes"]
    +
    resumen_trabajador["Total_Comision"]
)


# ==========================================================
# 💰 FORMATO DINERO
# ==========================================================

resumen_trabajador["Total_Prestado"] = (
    resumen_trabajador["Total_Prestado"]
    .apply(lambda x: f"${x:,.2f}")
)

resumen_trabajador["Total_Ganancias"] = (
    resumen_trabajador["Total_Ganancias"]
    .apply(lambda x: f"${x:,.2f}")
)


# ==========================================================
# 🧹 ELIMINAR COLUMNAS
# ==========================================================

resumen_trabajador = resumen_trabajador.drop(
    columns=[
        "Total_Interes",
        "Total_Comision"
    ]
)


# ==========================================================
# 🔽 ORDENAR
# ==========================================================

resumen_trabajador = resumen_trabajador.sort_values(
    by="Cuotas_Pendientes",
    ascending=False
)


# ==========================================================
# 📋 COLUMNA HISTORIAL
# ==========================================================

resumen_trabajador["Historial"] = "📋 Ver"


# ==========================================================
# 🔁 ORDENAR COLUMNAS
# ==========================================================

resumen_trabajador = resumen_trabajador[
    [
        "Cuotas_Pendientes",
        "Nombre y Apellido",
        "Total_Prestado",
        "Total_Ganancias",
        "Historial"
    ]
]


# ==========================================================
# 🎨 AGGRID
# ==========================================================

g_trab = GridOptionsBuilder.from_dataframe(
    resumen_trabajador
)

g_trab.configure_default_column(
    filter=True,
    sortable=True,
    resizable=True,
    editable=False
)


g_trab.configure_column(
    "Cuotas_Pendientes",
    headerName="Cuotas Pendientes",
    minWidth=200
)

g_trab.configure_column(
    "Nombre y Apellido",
    headerName="Nombre y Apellido",
    minWidth=350
)

g_trab.configure_column(
    "Total_Prestado",
    headerName="💰 Total Prestado",
    minWidth=200
)

g_trab.configure_column(
    "Total_Ganancias",
    headerName="📈 Total Ganancias",
    minWidth=200
)


# ==========================================================
# 🔘 BOTÓN VER
# ==========================================================

g_trab.configure_column(
    "Historial",
    headerName="📋 Historial",
    minWidth=140,
    maxWidth=160,
    sortable=False,
    filter=False,

    cellRenderer=JsCode(
        """
        class ButtonRenderer {

            init(params) {

                this.eGui = document.createElement('button');

                this.eGui.innerHTML = '📋 Ver';

                this.eGui.style.padding = '5px 15px';
                this.eGui.style.cursor = 'pointer';
                this.eGui.style.border = 'none';
                this.eGui.style.borderRadius = '5px';
                this.eGui.style.fontWeight = 'bold';

                this.eGui.addEventListener(
                    'click',
                    function() {

                        params.node.setSelected(true);

                    }
                );
            }

            getGui() {
                return this.eGui;
            }
        }
        """
    )
)


# ==========================================================
# ☑️ SELECCIÓN
# ==========================================================

g_trab.configure_selection(
    selection_mode="single",
    use_checkbox=False
)


# ==========================================================
# PAGINACIÓN
# ==========================================================

g_trab.configure_pagination(
    paginationPageSize=20
)


tbl_trab = g_trab.build()


# ==========================================================
# 📊 MOSTRAR TABLA
# ==========================================================

respuesta_trabajadores = AgGrid(

    resumen_trabajador,

    gridOptions=tbl_trab,

    enable_enterprise_modules=True,

    fit_columns_on_grid_load=True,

    allow_unsafe_jscode=True,

    theme="alpine",

    height=500,

    update_on=["selectionChanged"]
)


# ==========================================================
# 🪟 DETECTAR TRABAJADOR SELECCIONADO
# ==========================================================

filas_seleccionadas = respuesta_trabajadores.get(
    "selected_rows"
)


# ==========================================================
# ⚠️ IMPORTANTE:
# selected_rows puede ser DataFrame
# ==========================================================

if filas_seleccionadas is not None:

    if isinstance(filas_seleccionadas, pd.DataFrame):

        if not filas_seleccionadas.empty:

            trabajador_seleccionado = (
                filas_seleccionadas.iloc[0][
                    "Nombre y Apellido"
                ]
            )

            mostrar_historial(
                trabajador_seleccionado
            )

    else:

        if len(filas_seleccionadas) > 0:

            trabajador_seleccionado = (
                filas_seleccionadas[0][
                    "Nombre y Apellido"
                ]
            )

            mostrar_historial(
                trabajador_seleccionado
            )

# ==========================================================
# 📊 REPORTE DE GANANCIAS POR CAMPUS Y AÑO
# ==========================================================

st.markdown("---")
st.subheader("📊 Reporte de Ganancias por Campus y Año")


# Crear copia
df_reporte = df_filtrado.copy()


# Ganancia = Interés + Comisión
df_reporte["Ganancias"] = (
    df_reporte["Interes"] +
    df_reporte["Comisión"]
)


# ==========================================================
# AGRUPAR CAMPUS + AÑO
# ==========================================================

reporte_ganancias = (
    df_reporte
    .groupby(["Campus", "Año"])["Ganancias"]
    .sum()
    .reset_index()
)


# ==========================================================
# CONVERTIR A TABLA:
# CAMPUS | 2025 | 2026 | 2027
# ==========================================================

reporte_ganancias = (
    reporte_ganancias
    .pivot(
        index="Campus",
        columns="Año",
        values="Ganancias"
    )
    .fillna(0)
    .reset_index()
)


# ==========================================================
# TOTAL POR CAMPUS
# ==========================================================

columnas_anios = [
    col for col in reporte_ganancias.columns
    if col != "Campus"
]

reporte_ganancias["TOTAL"] = (
    reporte_ganancias[columnas_anios].sum(axis=1)
)


# ==========================================================
# TOTAL GENERAL
# ==========================================================

fila_total = {"Campus": "TOTAL GENERAL"}

for columna in columnas_anios:
    fila_total[columna] = reporte_ganancias[columna].sum()

fila_total["TOTAL"] = reporte_ganancias["TOTAL"].sum()


reporte_ganancias = pd.concat(
    [
        reporte_ganancias,
        pd.DataFrame([fila_total])
    ],
    ignore_index=True
)


# ==========================================================
# FORMATO DE DINERO
# ==========================================================

for columna in reporte_ganancias.columns:
    
    if columna != "Campus":
        reporte_ganancias[columna] = (
            reporte_ganancias[columna]
            .map(lambda x: f"${x:,.2f}")
        )


# ==========================================================
# MOSTRAR TABLA
# ==========================================================

st.dataframe(
    reporte_ganancias,
    use_container_width=True,
    hide_index=True
)


# =========================
# 📋 PLAN DE PRÉSTAMOS (ESTILIZADO PRO)
# =========================
st.markdown("---")
st.subheader("📊 Plan de Préstamos")

data_planes = {
    "Valor": [500, 450, 400, 350, 300, 250, 200, 150, 100, 50],
    "Plazo (Meses)": [5.5, 5.5, 5, 4.5, 4, 3.5, 3.5, 3, 3, 2],
    "Cuotas": [11, 11, 10, 9, 8, 7, 7, 6, 6, 4],
    "Cuota Quincenal": [57.50, 51.75, 50.00, 48.03, 45.75, 43.04, 34.43, 29.75, 19.83, 14.50]
}

df_planes = pd.DataFrame(data_planes)

# ✅ Asegurar entero
df_planes["Cuotas"] = df_planes["Cuotas"].astype(int)

# =========================
# 🧠 CÁLCULO DE TASA MENSUAL
# =========================
df_planes["Interés"] = (df_planes["Cuota Quincenal"] * df_planes["Cuotas"]) - df_planes["Valor"]

df_planes["Tasa Mensual (%)"] = (
    df_planes["Interés"] / (df_planes["Valor"] * df_planes["Plazo (Meses)"])
) * 100

# redondeo bonito
df_planes["Tasa Mensual (%)"] = df_planes["Tasa Mensual (%)"].round(2)

# =========================
# ORDENAR
# =========================
df_planes = df_planes.sort_values(by="Valor", ascending=False)

# 🧠 DETALLE
df_planes["Detalle"] = df_planes.apply(
    lambda row: f"💰 ${row['Valor']:,.2f} | ⏳ {row['Plazo (Meses)']} meses | 📆 {row['Cuotas']} cuotas de ${row['Cuota Quincenal']:,.2f}",
    axis=1
)

# 🎨 FORMATO VISUAL
df_planes["💰 Valor del Préstamo"] = df_planes["Valor"].map(lambda x: f"${x:,.2f}")
df_planes["💵 Cuota Quincenal"] = df_planes["Cuota Quincenal"].map(lambda x: f"${x:,.2f}")
df_planes["📈 Tasa Mensual"] = df_planes["Tasa Mensual (%)"].map(lambda x: f"{x:.2f}%")

# 🧹 COLUMNAS FINALES
df_planes = df_planes[
    [
        "💰 Valor del Préstamo",
        "Plazo (Meses)",
        "Cuotas",
        "💵 Cuota Quincenal",
        "📈 Tasa Mensual",
        "Detalle"
    ]
]

# =========================
# 🎨 ESTILO HOVER (CSS)
# =========================
st.markdown("""
<style>
div[data-testid="stDataFrame"] tbody tr:hover {
    background-color: #262730 !important;
    color: #00E5FF !important;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 🎯 MOSTRAR TABLA
# =========================
st.dataframe(
    df_planes,
    use_container_width=True,
    hide_index=True
)