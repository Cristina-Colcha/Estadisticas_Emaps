import os
import textwrap
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import plotly.express as px

from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AI_MODEL = "gemini-2.5-flash"
llm = ChatGoogleGenerativeAI(model=AI_MODEL, google_api_key=GOOGLE_API_KEY)

st.set_page_config(layout="wide")
st.title("📊 Estadísticas de Sensores")

archivo = st.file_uploader("📁 Sube el archivo Excel", type=["xlsx"])
if archivo:
    hoja = st.selectbox("Selecciona la hoja", ["Original", "Completado_Filas"])
    df = pd.read_excel(archivo, sheet_name=hoja)

    if 'Fecha' in df.columns:
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df['Año'] = df['Fecha'].dt.year
        df['AñoMes'] = df['Fecha'].dt.to_period('M').astype(str)

        # --- Menú lateral ---
        opcion = st.sidebar.radio("📂 Selecciona una sección para visualizar", [
            "Métricas Totales",
            "Gráficos Anuales",
            "Gráfico Combinado por Mes",
            "Promedios Mensuales",
            "Máximos y Mínimos",
            "Distribución",
            "Proporción Total"
        ])

        # --- Conclusión comparativa de ambas hojas en la barra lateral ---
        st.sidebar.markdown("---")
        st.sidebar.header("📋 Comparación de Hojas")

        if st.sidebar.button("📊 Generar Comparación"):
            with st.spinner("Analizando ambas hojas con IA..."):
                try:
                    df_original = pd.read_excel(archivo, sheet_name="Original")
                    df_completado = pd.read_excel(archivo, sheet_name="Completado_Filas")
                except Exception as e:
                    st.sidebar.error(f"Error al leer hojas: {e}")
                    st.stop()

                for df_temp in [df_original, df_completado]:
                    if 'Fecha' in df_temp.columns:
                        df_temp['Fecha'] = pd.to_datetime(df_temp['Fecha'], errors='coerce')

                def resumen(df, nombre):
                    return f"""
📄 **{nombre}**
- Fechas: desde {df['Fecha'].min().strftime('%Y-%m-%d')} hasta {df['Fecha'].max().strftime('%Y-%m-%d')}
- Suma P42: {df['P42'].sum():,.2f}
- Suma P43: {df['P43'].sum():,.2f}
- Suma P55: {df['P55'].sum():,.2f}
- Promedio P42: {df['P42'].mean():,.2f}
- Promedio P43: {df['P43'].mean():,.2f}
- Promedio P55: {df['P55'].mean():,.2f}
"""

                resumen_original = resumen(df_original, "Original")
                resumen_completado = resumen(df_completado, "Completado_Filas")

                prompt_comparativo = textwrap.dedent(f"""
                Tengo dos hojas de un archivo Excel con datos históricos de sensores del volcán Antisana: una hoja llamada "Original" y otra llamada "Completado_Filas".

                La hoja "Original" contiene los datos base, mientras que la hoja "Completado_Filas" incluye datos completados o corregidos para mejorar el registro.

                A continuación, te presento un resumen estadístico de cada hoja:

                {resumen_original}

                {resumen_completado}

                El objetivo es utilizar los datos de la hoja "Completado_Filas" para mejorar el sistema de mantenimiento preventivo de los sensores del Antisana y evitar posibles desastres derivados de fallos o datos incompletos.

                Por favor, genera una conclusión general comparativa que incluya:

                - Principales diferencias y tendencias entre ambas hojas.
                - Identificación de mejoras significativas en la calidad o consistencia de los datos.
                - Potenciales problemas o áreas donde aún se puede mejorar el sistema.
                - Recomendaciones prácticas para optimizar el mantenimiento y garantizar la fiabilidad de los sensores basándote en los datos.
                - Cómo estas mejoras podrían ayudar a prevenir fallos o desastres futuros.

                Responde de forma clara, precisa y orientada a la acción.
                """)

                conclusion_comparativa = llm.predict(prompt_comparativo)
                st.sidebar.markdown("### 🤖 Conclusión:")
                st.sidebar.write(conclusion_comparativa)

        # --- 1. Métricas Totales ---
        if opcion == "Métricas Totales":
            st.subheader("📍 Métricas Totales")
            col1, col2, col3 = st.columns(3)
            col1.metric("Suma de P42", f"{df['P42'].sum():,.2f} mil")
            col2.metric("Suma de P43", f"{df['P43'].sum():,.2f} mil")
            col3.metric("Suma de P55", f"{df['P55'].sum():,.2f} mil")
            st.info("📌 Esta sección muestra la suma total de cada sensor durante todo el período de tiempo.")

        # --- 2. Gráficos Anuales ---
        elif opcion == "Gráficos Anuales":
            st.subheader("📆 Suma por Año")
            df_agg = df.groupby("Año")[["P42", "P43", "P55"]].sum().reset_index()
            col4, col5, col6 = st.columns(3)
            with col4:
                fig = px.line(df_agg, x="Año", y="P42", title="🔵 Suma de P42 por Año")
                st.plotly_chart(fig, use_container_width=True)
            with col5:
                fig = px.line(df_agg, x="Año", y="P43", title="🟠 Suma de P43 por Año")
                st.plotly_chart(fig, use_container_width=True)
            with col6:
                fig = px.line(df_agg, x="Año", y="P55", title="🔴 Suma de P55 por Año")
                st.plotly_chart(fig, use_container_width=True)
            st.info("📌 Estas gráficas muestran cómo varía la suma de cada sensor por año. Ideal para detectar tendencias generales.")

        # --- 3. Gráfico Combinado por Mes ---
        elif opcion == "Gráfico Combinado por Mes":
            st.subheader("📊 Tendencia mensual combinada")
            df_mes = df.groupby("AñoMes")[["P42", "P43", "P55"]].sum().reset_index()
            df_mes = df_mes.sort_values("AñoMes")
            df_mes[["P42", "P43", "P55"]] = df_mes[["P42", "P43", "P55"]].replace(0, pd.NA)
            fig = px.line(df_mes, x="AñoMes", y=["P42", "P43", "P55"],
                          title="Suma mensual de sensores (líneas se cortan con 0s)")
            st.plotly_chart(fig, use_container_width=True)
            st.info("📌 Este gráfico permite visualizar la evolución mensual de los tres sensores simultáneamente. Los ceros han sido ocultos para evitar distorsiones.")

        # --- 4. Promedios Mensuales ---
        elif opcion == "Promedios Mensuales":
            st.subheader("📉 Promedio mensual por sensor")
            df_prom = df.groupby("AñoMes")[["P42", "P43", "P55"]].mean().reset_index()
            df_prom_long = pd.melt(df_prom, id_vars="AñoMes", value_vars=["P42", "P43", "P55"],
                                   var_name="Sensor", value_name="Promedio")
            fig_prom = px.line(df_prom_long, x="AñoMes", y="Promedio", color="Sensor",
                               markers=True, title="Promedio mensual de cada sensor")
            st.plotly_chart(fig_prom, use_container_width=True)
            st.info("📌 Este gráfico muestra el promedio mensual por sensor. Útil para comparar comportamientos a lo largo del tiempo.")

        # --- 5. Máximos y Mínimos ---
        elif opcion == "Máximos y Mínimos":
            st.subheader("📈 Máximos y mínimos por sensor")
            cols_maxmin = st.columns(3)
            for i, sensor in enumerate(["P42", "P43", "P55"]):
                max_val = df[sensor].max()
                min_val = df[sensor].min()
                fecha_max = df.loc[df[sensor] == max_val, "Fecha"].dt.strftime('%Y-%m').values[0]
                fecha_min = df.loc[df[sensor] == min_val, "Fecha"].dt.strftime('%Y-%m').values[0]
                cols_maxmin[i].markdown(f"""
                ### {sensor}
                🔺 **Máx**: {max_val:,.2f} en `{fecha_max}`  
                🔻 **Mín**: {min_val:,.2f} en `{fecha_min}`
                """)
            st.info("📌 Aquí puedes ver cuándo se registraron los valores más altos y más bajos de cada sensor.")

        # --- 6. Distribución ---
        elif opcion == "Distribución":
            st.subheader("📊 Distribución de valores por sensor")
            col_hist1, col_hist2, col_hist3 = st.columns(3)
            with col_hist1:
                st.plotly_chart(px.histogram(df, x="P42", nbins=20, title="Distribución P42"), use_container_width=True)
            with col_hist2:
                st.plotly_chart(px.histogram(df, x="P43", nbins=20, title="Distribución P43"), use_container_width=True)
            with col_hist3:
                st.plotly_chart(px.histogram(df, x="P55", nbins=20, title="Distribución P55"), use_container_width=True)
            st.info("📌 Histogramas que muestran la frecuencia de valores medidos por cada sensor.")

        # --- 7. Proporción Total ---
        elif opcion == "Proporción Total":
            st.subheader("📌 Porcentaje que representa cada sensor del total")
            total = df[["P42", "P43", "P55"]].sum()
            fig_pie = px.pie(
                names=total.index,
                values=total.values,
                title="Proporción del total por sensor",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            st.info("📌 Este gráfico muestra cuánto contribuye cada sensor al total general del periodo.")

        # --- Conclusión individual por hoja ---
        st.markdown("---")
        st.header("🤖 Conclusión General Generada con IA")
        if st.button("📝 Generar Conclusión"):
            with st.spinner("Generando conclusión con IA..."):
                prompt = textwrap.dedent(f"""
                Tengo datos de sensores con las siguientes sumas totales:
                P42: {df['P42'].sum():,.2f}
                P43: {df['P43'].sum():,.2f}
                P55: {df['P55'].sum():,.2f}

                El rango de fechas va desde {df['Fecha'].min().strftime('%Y-%m-%d')} hasta {df['Fecha'].max().strftime('%Y-%m-%d')}.
                
                También hay datos de máximos y mínimos para cada sensor.

                Por favor, genera una conclusión general que resuma las tendencias, valores relevantes y posibles observaciones útiles para un análisis rápido.
                """)
                conclusion = llm.predict(prompt)
                st.write(conclusion)

    else:
        st.warning("⚠️ La hoja seleccionada no tiene una columna 'Fecha'.")
