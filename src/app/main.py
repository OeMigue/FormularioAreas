import gc
import time
import uuid
import locale
import threading
import pythoncom
import pandas as pd
import xlwings as xw
import streamlit as st
from datetime import datetime

RUTA_CSS = r"O:\Gerencia Contraloria\Analitica Contraloria\Automatiaciones Ambiente Pruebas\Carpeta Miguel Cardona\FormularioAreas\styles\STYLES.css"
RUTA_ICON = r"O:\Gerencia Contraloria\Analitica Contraloria\Automatiaciones Ambiente Pruebas\Carpeta Miguel Cardona\FormularioAreas\images\gco_ico.svg"
RUTA_IMAGE = r"O:\Gerencia Contraloria\Analitica Contraloria\Automatiaciones Ambiente Pruebas\Carpeta Miguel Cardona\FORMULARIOS\images\GContraloria.png"
RUTA_ARCHIVO = r"O:\Gerencia Contraloria\Analitica Contraloria\Automatiaciones Ambiente Pruebas\Carpeta Miguel Cardona\FormularioAreas\input\Ingreso Datos Informe Gerencia Contraloria - Eficiencias y Volumetria.xlsm"
RUTA_ICON_MARCAS = r"O:\Gerencia Contraloria\Analitica Contraloria\Automatiaciones Ambiente Pruebas\Carpeta Miguel Cardona\FormularioAreas\images\footer_marcas.svg"
RUTA_BIENVENIDA_GCO = r"O:\Gerencia Contraloria\Analitica Contraloria\Automatiaciones Ambiente Pruebas\Carpeta Miguel Cardona\FormularioAreas\images\bienvenidaGCO.png"

locale.setlocale(locale.LC_ALL, '')  # Usa configuración local del sistema

CREDENCIALES = {
    "Miguel Cardona": ["mcardona", "777"],
    "Jorge Herrera": ["jorgeeh", "1212"],
    "Alberto Cortés": ["albertoc", "2323"],
    "Oscar Yepes": ["oscardy", "3434"],
    "Dora Gómez": ["doragc", "4545"],
    "Zaneida Restrepo": ["zrestrepo", "5656"],
    "Ana Romero": ["anamr", "6767"],
}

AREAS = {
    "mcardona": "Admin",
    "jorgeeh": "Analítica de Contraloría",
    "albertoc": "Control de Operaciones",
    "oscardy": "Administrativa",
    "doragc": "Riesgos y Cumplimiento",
    "zrestrepo": "Impuestos",
    "anamr": "Contabilidad",
}

MESES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

@st.cache_data
def cargar_excel():
    return pd.read_excel(
        io=RUTA_ARCHIVO,
        sheet_name="Parámetros",
        skiprows=1,
    )

df = cargar_excel()
# ============================================ FUNCTIONS ========================================

def sincronizar_filas(conceptos_seleccionados):
    # eliminar filas de conceptos deseleccionados
    st.session_state.filas = [
        f for f in st.session_state.filas
        if f["concepto"] in conceptos_seleccionados
    ]

    # 🚫 si venimos de eliminar, NO recrear filas
    if st.session_state.saltarse_sync:
        st.session_state.saltarse_sync = False
        return

    # crear fila base SOLO para conceptos nuevos del multiselect
    existentes = {f["concepto"] for f in st.session_state.filas}

    for concepto in conceptos_seleccionados:
        if concepto not in existentes:
            st.session_state.filas.append({
                "concepto": concepto,
                "id": str(uuid.uuid4())
            })


def parametros(area):
    lista_especificaciones = df.iloc[:,14].dropna().drop_duplicates().tolist()
    lista_ciudades = df.iloc[:,16].dropna().drop_duplicates().tolist()

    if area == "Analítica de Contraloría" or area == "Admin":
        lista_concepto_nuevo = df.iloc[:,18].dropna().drop_duplicates().tolist()
        diccionario_unidades = dict(zip(df.iloc[:,18].dropna().drop_duplicates(), df.iloc[:,20].dropna()))

    elif area == "Control de Operaciones":
        lista_concepto_nuevo = df.iloc[:,34].dropna().drop_duplicates().tolist()
        diccionario_unidades = dict(zip(df.iloc[:,34].dropna().drop_duplicates(), df.iloc[:,36].dropna()))

    elif area == "Administrativa":
        lista_concepto_nuevo = df.iloc[:,6].dropna().drop_duplicates().tolist()
        diccionario_unidades = dict(zip(df.iloc[:,6].dropna().drop_duplicates(), df.iloc[:,8].dropna()))

    elif area == "Riesgos y Cumplimiento":
        lista_concepto_nuevo = df.iloc[:,50].dropna().drop_duplicates().tolist()
        diccionario_unidades = dict(zip(df.iloc[:,50].dropna().drop_duplicates(), df.iloc[:,52].dropna()))

    elif area == "Impuestos":
        lista_concepto_nuevo = df.iloc[:,42].dropna().drop_duplicates().tolist()
        diccionario_unidades = dict(zip(df.iloc[:,42].dropna().drop_duplicates(), df.iloc[:,44].dropna()))

    elif area == "Contabilidad":
        lista_concepto_nuevo = df.iloc[:,26].dropna().drop_duplicates().tolist()
        diccionario_unidades = dict(zip(df.iloc[:,26].dropna().drop_duplicates(), df.iloc[:,28].dropna()))

    return lista_especificaciones, lista_ciudades, lista_concepto_nuevo, diccionario_unidades

def cerrar_instancia_xlwings(app):
    """
    Cierra únicamente la instancia de Excel creada por xlwings,
    sin cerrar otras instancias abiertas por el usuario,
    limpiando COM y memoria.
    """

    if app is None:
        return

    try:
        # Cierra todos los libros abiertos en esa instancia
        for wb in app.books:
            try:
                wb.close()
            except:
                pass

        # Cierra solo esta instancia
        app.quit()
    except:
        pass

    # Eliminar referencia
    try:
        del app
    except:
        pass

    # Limpiar COM y memoria
    try:
        pythoncom.CoUninitialize()
    except:
        pass

    gc.collect()

    print("Instancia de Excel cerrada correctamente sin afectar otras.")


def insertar_multiples_registros(ruta_archivo, hoja_objetivo, columnas, lista_datos, contrasena):
    """Inserta múltiples registros en Excel de una sola vez"""
    app = xw.App(visible=False)
    app.api.EnableEvents = False
    wb = app.books.open(ruta_archivo)
    hoja = wb.sheets[hoja_objetivo]

    hoja.api.Unprotect(Password=contrasena)

    # Encontrar la última fila con datos
    ultima_fila = 1
    for col in columnas:
        col_obj = hoja.range((1, col)).expand('down')
        filas_con_datos = [c.row for c in col_obj if c.value not in [None, ""]]
        if filas_con_datos:
            ultima_fila = max(ultima_fila, max(filas_con_datos))

    # Insertar todos los registros
    for idx, datos in enumerate(lista_datos):
        nueva_fila = ultima_fila + idx + 1
        for i, col in enumerate(columnas):
            hoja.cells(nueva_fila, col).value = datos[i]

    hoja.api.Protect(Password=contrasena)
    app.api.EnableEvents = True
    wb.save()
    wb.close()
    cerrar_instancia_xlwings(app)

def ejecutar_guardar_multiples(registros, usuario_actual):
    """Guarda múltiples registros en Excel de una sola vez"""

    # Elegimos la hoja según el usuario
    if usuario_actual == "jorgeeh":
        hoja = "Analítica de Contraloría"
    elif usuario_actual == "albertoc":
        hoja = "Control de Operaciones"
    elif usuario_actual == "oscardy":
        hoja = "Administrativa"
    elif usuario_actual == "doragc":
        hoja = "Riesgos y Cumplimiento"
    elif usuario_actual == "zrestrepo":
        hoja = "Impuestos"
    elif usuario_actual == "anamr":
        hoja = "Contabilidad"
    else:
        hoja = "Admin"

    # Guardamos todos los datos en el archivo Excel
    insertar_multiples_registros(
        ruta_archivo=RUTA_ARCHIVO,
        hoja_objetivo=hoja,
        columnas=[1, 2, 4, 7, 8, 11],
        lista_datos=registros,
        contrasena="54312"
    )

# ===============================================================================================

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

def mostrar_login():
    # Configuración de la página
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
                            @st.dialog('Para nosotros es un honor tenerte aquí')
                            def ventana_login():
                                st.success(f"Bienvenido(a) {nombre}. Inicio de sesión completo", icon = ":material/how_to_reg:")
                                time.sleep(0.5)
                                st.rerun()
                            ventana_login()
                    st.divider()
                    st.error("Usuario o contraseña incorrectos")

def mostrar_formulario():
    # Limpiar campos si se indica en session_state
    if st.session_state.get("limpiar_campos", False):
        st.session_state.año_input = None
        st.session_state.mes_input = None
        st.session_state.concepto_input = None
        st.session_state.especificacion_input = None
        st.session_state.ciudad_input = None
        st.session_state.valor_input = 0
        st.session_state.limpiar_campos = False
    
    lista_especificaciones, lista_ciudades, lista_concepto_nuevo, diccionario_unidades = parametros(
        AREAS.get(st.session_state.usuario_actual)
    )
    lista_especificaciones_ordenadas = sorted(lista_especificaciones, key=lambda x: x != "No aplica")
    lista_ciudades_ordenadas = sorted(lista_ciudades, key=lambda x: x != "No aplica")

    # Configuración de la página
    st.set_page_config(
        page_title="GCO | Contraloría",
        page_icon=RUTA_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    container = st.container()
    with container:
        div1, div2 = st.columns([8, 2])
        with div1:
            # Mostrar usuario actual
            st.success("_" * 10+ f"Bienvenido(a), {st.session_state.nombre_usuario} ✌️"+ "_" * 10, icon = ":material/how_to_reg:")
        with div2:
            cerrar_sesion = st.button("Cerrar Sesión", width='stretch')
        if cerrar_sesion:
            @st.dialog('¿Está seguro(a) de cerrar sesión?')
            def ventana_cerrar_sesion():
                if st.button('Confirmar Cerrar Sesión', icon=":material/logout:"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
            ventana_cerrar_sesion()
    st.markdown(
        f"""
            <div class="h2-form" style='text-align: center; border-radius: 30px;'>
                <h2>Formulario {AREAS.get(st.session_state.usuario_actual)}</h2>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    concepto = st.container()

    if "saltarse_sync" not in st.session_state:
        st.session_state.saltarse_sync = False

    if "conceptos_buffer" not in st.session_state:
        st.session_state.conceptos_buffer = []

    with concepto:
        conceptos_seleccinados= st.multiselect(
            label="Conceptos",
            options=lista_concepto_nuevo,
            placeholder="💡Por favor seleccione los conceptos...",
            key="select_concepto",
            default=st.session_state.conceptos_buffer
        )
        st.session_state.conceptos_buffer = conceptos_seleccinados

        sincronizar_filas(conceptos_seleccinados)



    inputs_form = st.container()
    concepto_select, año_select, mes_select, especificacion_select, ciudad_select, valor_select, guia, duplicar, eliminar = st.columns([4,2.5,2.665,3,3,3,4,1,1])
    año_actual = datetime.now().year
    años = [int(año_actual) -2, int(año_actual) - 1, int(año_actual)]
    mes_actual = datetime.now().month
    mes_defecto = mes_actual - 1

    años_seleccionados = []
    meses_seleccionados = []
    especificaciones_seleccionadas = []
    ciudades_seleccionadas = []
    valores_selecionados = []
    # contador = 0
    
    with inputs_form:
        if conceptos_seleccinados:
            with concepto_select:
                st.write("Conceptos")
            with año_select:
                st.write("Año")
            with mes_select:
                st.write("Mes")
            with especificacion_select:
                st.write("Especificación")
            with ciudad_select:
                st.write("Ciudad")
            with valor_select:
                st.write("Valores")
            with guia:
                st.write("Guía")
# ====
        if "filas" not in st.session_state:
            st.session_state.filas = []

            
        for fila in st.session_state.filas:
            concepto = fila["concepto"]
            fila_id = fila["id"]
# ====

        for idx, fila in enumerate(st.session_state.filas):
            concepto = fila["concepto"]
            fila_id = fila["id"]
            # contador = contador + 1

            with concepto_select:
                st.badge(concepto)
            with año_select:
                año = st.selectbox(
                    label="Año",
                    label_visibility="collapsed",
                    options=años,
                    index=2,
                    placeholder="Seleccione una opción...",
                    key=f"select_año_{fila_id}"
                )
                años_seleccionados.append(año)

            with mes_select:
                mes = st.selectbox(
                    label="Mes",
                    label_visibility="collapsed",
                    options=MESES,
                    index=mes_defecto,
                    placeholder="Selecciones una opcón...",
                    key=f"select_mes_{fila_id}",
                )
                meses_seleccionados.append(mes)

            with especificacion_select:
                especificacion = st.selectbox(
                    label="Especificacion",
                    label_visibility="collapsed",
                    options=lista_especificaciones_ordenadas,
                    index=0,
                    placeholder="Selecciones una opcón...",
                    key=f"select_especificacion_{fila_id}"
                )
                especificaciones_seleccionadas.append(especificacion)

            with ciudad_select:
                ciudad = st.selectbox(
                    label="Ciudad",
                    label_visibility="collapsed",
                    options=lista_ciudades_ordenadas,
                    index=0,
                    placeholder="Selecciones una opcón...",
                    key=f"select_ciudad_{fila_id}"
                )
                ciudades_seleccionadas.append(ciudad)

            with valor_select:
                tipo_valor = diccionario_unidades.get(concepto, "")

                if tipo_valor == "Cantidad":
                    valor = st.number_input(
                        label=f"Unidades:",
                        label_visibility="collapsed",
                        format="%d",
                        step=1,
                        key=f"select_valor_{fila_id}",
                        icon = ":material/dataset:"
                    )
                    valores_selecionados.append(valor)
                    valor_formateado = locale.format_string("%.0f", valor, grouping=True)
                    with guia:
                        st.badge(f"Unidades: {valor_formateado}")

                elif tipo_valor == "Pesos":
                    valor = st.number_input(
                        label="Valor",
                        label_visibility="collapsed",
                        format="%d",
                        step=1,
                        key=f"select_valor_{fila_id}",
                        icon = ":material/payments:"
                    )
                    valores_selecionados.append(valor)
                    valor_formateado = locale.format_string("%.0f", valor,grouping=True)
                    with guia:
                        st.badge(f"Valor: ${valor_formateado}")

                elif tipo_valor == "Porcentaje":
                    valor = st.number_input(
                        label="Porcentaje",
                        label_visibility="collapsed",
                        format="%f",
                        step=1.0,
                        key=f"select_valor_{fila_id}",
                        icon = ":material/percent:"
                    )
                    valores_selecionados.append(valor)
                    valor_formateado = locale.format_string("%.0f", valor)
                    with guia:
                        st.badge(f"Porcentaje: {valor}%")

                elif tipo_valor == "Toneladas":
                    valor = st.number_input(
                        label=f"Toneladas:",
                        label_visibility="collapsed",
                        format="%f",
                        step=1.0,
                        key=f"select_valor_{fila_id}",
                        icon = ":material/weight:"
                    )
                    valores_selecionados.append(valor)
                    valor_formateado = locale.format_string("%.0f", valor, grouping=True)
                    with guia:
                        st.badge(f"Toneladas: {valor_formateado}")

            with duplicar:
                if st.button(
                    label="", 
                    key=f"dup_{fila_id}",
                    icon = ":material/control_point_duplicate:",
                    width='stretch',
                    help="Duplicar"
                ):
                # 🔑 duplicar ESTA fila, no la última
                    st.session_state.filas.insert(
                        idx + 1,
                        {
                            "concepto": concepto,
                            "id": str(uuid.uuid4())
                        }
                    )
                    st.rerun()

            with eliminar:
                total_concepto = sum(
                    1 for f in st.session_state.filas
                    if f["concepto"] == concepto
                )

                puede_eliminar = total_concepto > 1

                if st.button(
                    label="",
                    key=f"del_{fila_id}",
                    icon=":material/delete:",
                    disabled=not puede_eliminar,
                    help="Eliminar" if puede_eliminar else "Para eliminar este concepto, deselecciónelo desde el multiselect"
                ) and puede_eliminar:
                    # 1️⃣ borrar keys del session_state de esa fila
                    for k in list(st.session_state.keys()):
                        if k.endswith(fila_id):
                            del st.session_state[k]

                    # 2️⃣ eliminar SOLO esta fila
                    st.session_state.filas = [
                        f for f in st.session_state.filas
                        if f["id"] != fila_id
                    ]

                    st.rerun()
    
    
    total_registros = len(st.session_state.filas)
    if conceptos_seleccinados:
        btn_enviar = st.button(
            label=f"Enviar Todo ({total_registros})",
            key="btn_enviar",
            width='stretch',
            icon=":material/send:")
        if btn_enviar:
            @st.dialog('¿Está seguro(a) de enviar los registros?')
            def ventana_enviar_todo():
                if st.button("Enviar registros"):
                    with st.spinner('Enviando registros...'):
                        registros = []
                        for idx, fila in enumerate(st.session_state.filas):
                            registros.append((
                                años_seleccionados[idx],
                                meses_seleccionados[idx],
                                fila["concepto"],
                                especificaciones_seleccionadas[idx],
                                ciudades_seleccionadas[idx],
                                valores_selecionados[idx],
                            ))
                        hilo_guardar = threading.Thread(
                            target=ejecutar_guardar_multiples,
                            args=(registros, st.session_state.usuario_actual)
                        )
                        hilo_guardar.start()

                        barra_carga = st.progress(0)
                        progreso = 0
                        while hilo_guardar.is_alive():
                            progreso = min(progreso + 10, 95)
                            barra_carga.progress(progreso)
                            time.sleep(0.4)

                        barra_carga.progress(100)
                        time.sleep(0.2)
                        barra_carga.empty()

                        st.toast('Registros enviados y guardados con éxito', icon=":material/folder_check:")
                        st.success(f"Se enviaron {total_registros} registro(s)")

                        # Limpiar filas y multiselect después de guardar
                        st.session_state.filas = []
                        st.session_state.conceptos_buffer = []

                        for k in list(st.session_state.keys()):
                            if (
                                k.startswith("select_año_") or
                                k.startswith("select_mes_") or
                                k.startswith("select_especificacion_") or
                                k.startswith("select_ciudad_") or
                                k.startswith("select_valor_")
                            ):
                                del st.session_state[k]
                        
                        st.session_state.select_concepto = []
                        time.sleep(0.5)
                        st.rerun()
            ventana_enviar_todo()

# ============================================================================================================================================
def main():
    aplicar_css()

    # Inicializar session_state
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if "usuario_actual" not in st.session_state:
        st.session_state.usuario_actual = ""
    if "registros_tabla" not in st.session_state:
        st.session_state.registros_tabla = []
    if "limpiar_campos" not in st.session_state:
        st.session_state.limpiar_campos = False
    if "saltarse_sync" not in st.session_state:
        st.session_state.saltarse_sync = False
    if "select_concepto" not in st.session_state:
        st.session_state.select_concepto = []

    st.sidebar.image(RUTA_IMAGE)

    if st.session_state.autenticado:
        mostrar_formulario()
    else:
        mostrar_login()

    st.divider()
    st.image(RUTA_ICON_MARCAS, width='stretch')

if __name__ == "__main__":
    main()
