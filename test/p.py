import streamlit as st
import time
import pandas as pd

CREDENCIALES = {
    "Miguel Cardona": ["mcardona", "777"],
    "Jorge Herrera": ["jorgeeh", "1212"],
    "Alberto Cortés": ["albertoc", "2323"],
    "Oscar Yepes": ["oscardy", "3434"],
    "Dora Gómez": ["doragc", "4545"],
    "Zaneida Restrepo": ["zrestrepo", "5656"],
    "Ana Romero": ["anamr", "6767"],
}

RUTA_ICON = r"O:\Gerencia Contraloria\Analitica Contraloria\Automatiaciones Ambiente Pruebas\Carpeta Miguel Cardona\FormularioAreas\images\gco_ico.svg"
RUTA_BIENVENIDA_GCO = r"O:\Gerencia Contraloria\Analitica Contraloria\Automatiaciones Ambiente Pruebas\Carpeta Miguel Cardona\FormularioAreas\images\bienvenidaGCO.png"
RUTA_ARCHIVO = r"O:\Gerencia Contraloria\Analitica Contraloria\Automatiaciones Ambiente Pruebas\Carpeta Miguel Cardona\FormularioAreas\input\Ingreso Datos Informe Gerencia Contraloria - Eficiencias y Volumetria.xlsm"
RUTA_CSS = r"O:\Gerencia Contraloria\Analitica Contraloria\Automatiaciones Ambiente Pruebas\Carpeta Miguel Cardona\FormularioAreas\styles\STYLES.css"


@st.cache_data
def cargar_excel():
    return pd.read_excel(
        io=RUTA_ARCHIVO,
        sheet_name="Parámetros",
        skiprows=1,
    )

df = cargar_excel()

def aplicar_css():
    with open(RUTA_CSS, mode="r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(
        f""" 
    <style>
        {css}
    </style> 
    """,
        unsafe_allow_html=True,
    )

aplicar_css()


st.set_page_config(
        page_title="GCO | Inicio de Sesión",
        page_icon=RUTA_ICON,
        layout="centered",
        initial_sidebar_state="expanded",
    )
container = st.container()
with container:
    st.markdown(
        """
            <div class="h2" style='text-align: center; '>
                <h2>Formulario Informe de Gerencia</h2>
            </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    contenedor_inputs = st.container()
    
    with contenedor_inputs:
        col01, col02 = st.columns([5, 5])
        with col01:
            col1, col2, col3 = st.columns([12,1,1])
            with col1:
                st.image(RUTA_BIENVENIDA_GCO, width='stretch')
        with col02:
            
            usuario = st.text_input("Usuario:", placeholder="Ej: usuario", icon = ":material/account_circle:")
            contraseña = st.text_input(
                "Pin:", placeholder="Ej: 1234", type="password", icon = ":material/passkey:")
            enviar = st.button("Iniciar Sesión", icon =":material/login:")
    
        if enviar:
            if not usuario or not contraseña:
                st.divider()
                st.warning("Campos obligatorios")
            else:
                for nombre, datos_bd in CREDENCIALES.items():
                    if usuario == datos_bd[0] and contraseña == datos_bd[1]:
                        st.session_state.autenticado = True
                        st.session_state.usuario_actual = usuario
                        st.session_state.nombre_usuario = nombre
                        @st.dialog('Para nosotros es un gusto tenerte aquí')
                        def ventana_login():
                            st.success(f"Bienvenido(a) {nombre}. Inicio de sesión completo", icon = ":material/how_to_reg:")
                            time.sleep(0.5)
                        st.rerun()
                        ventana_login()
                st.divider()
                st.error("Usuario o contraseña incorrectos")