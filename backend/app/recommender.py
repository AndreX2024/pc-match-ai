from pathlib import Path
from itertools import product
import re
import joblib
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

BASE = Path(__file__).resolve().parent.parent

archivos_componentes = {
    'cpu': 'cpu.csv',
    'cpu-cooler': 'cpu-cooler.csv',
    'motherboard': 'motherboard.csv',
    'memory': 'memory.csv',
    'internal-hard-drive': 'internal-hard-drive.csv',
    'video-card': 'video-card.csv',
    'power-supply': 'power-supply.csv',
    'case': 'case.csv'
}


# ============================================================
# CARGAR MODELO ENTRENADO
# ============================================================

_art = joblib.load(
    BASE / "artifacts" / "modelo.joblib"
)

mejor_modelo = _art["model"]

# Columnas que el modelo utilizó durante el entrenamiento.
# Se guardaron desde train.py.
FEATURE_COLUMNS = _art["columns"]


# ============================================================
# CARGAR CATÁLOGOS DE COMPONENTES
# ============================================================

componentes = {
    k: pd.read_csv(
        BASE / "data" / "componentes" / v
    )
    for k, v in archivos_componentes.items()
}


# Guardar los precios originales para poder realizar
# posteriormente la conversión USD -> COP.
for t in componentes.values():
    t["price_original"] = pd.to_numeric(
        t["price"],
        errors="coerce"
    )


# ============================================================
# INFERIR SOCKET DE CPU
# ============================================================

# Inferencias sencillas aplicadas únicamente a los candidatos.
# Son aproximaciones de prototipo, no certificaciones del fabricante.

def inferir_socket_cpu(nombre):
    texto = str(nombre).upper()

    ryzen = re.search(
        r'RYZEN\s+[3579]\s+(\d{4})',
        texto
    )

    if ryzen:
        generacion = int(ryzen.group(1)[0])

        if generacion in (7, 8, 9):
            return 'AM5'

        if generacion in (1, 2, 3, 4, 5):
            return 'AM4'

    if re.search(
        r'CORE\s+ULTRA\s+[579]\s+2\d{2}',
        texto
    ):
        return 'LGA1851'

    intel = re.search(
        r'CORE\s+I[3579]-?(\d{4,5})',
        texto
    )

    if intel:
        model = intel.group(1)

        gen = (
            int(model[:2])
            if len(model) == 5
            else int(model[0])
        )

        if gen in (12, 13, 14):
            return 'LGA1700'

        if gen in (10, 11):
            return 'LGA1200'

        if gen in (6, 7, 8, 9):
            return 'LGA1151'

    return None


# ============================================================
# INFERIR TIPO DE RAM
# ============================================================

def inferir_tipo_ram(fila):
    prefijo = str(
        fila.get('speed', '')
    ).strip().split(',')[0]

    nombre = str(
        fila.get('name', '')
    ).upper()

    if prefijo == '5' or 'DDR5' in nombre:
        return 'DDR5'

    if prefijo == '4' or 'DDR4' in nombre:
        return 'DDR4'

    return None


# ============================================================
# INFERIR TIPO DE RAM DE LA MOTHERBOARD
# ============================================================

def inferir_ram_motherboard(fila):
    socket = str(
        fila.get('socket', '')
    ).upper()

    nombre = str(
        fila.get('name', '')
    ).upper()

    if socket in ('AM5', 'LGA1851'):
        return 'DDR5'

    if socket == 'AM4':
        return 'DDR4'

    if socket == 'LGA1700':

        if 'DDR4' in nombre:
            return 'DDR4'

        if 'DDR5' in nombre:
            return 'DDR5'

    return None


# ============================================================
# PARSEAR MÓDULOS DE RAM
# ============================================================

def parsear_modulos(valor):
    partes = str(valor).replace(
        ' ',
        ''
    ).split(',')

    if len(partes) != 2:
        return None, None

    try:
        cantidad, capacidad = (
            int(p)
            for p in partes
        )

    except ValueError:
        return None, None

    if cantidad < 1 or capacidad < 1:
        return None, None

    return cantidad, cantidad * capacidad


# ============================================================
# ESTIMAR TDP DE GPU
# ============================================================

def estimar_tdp_gpu(chipset):
    texto = str(chipset).upper()

    m = re.search(
        r'(?:RTX|GTX)\s*(\d{4})',
        texto
    )

    if m:
        n = int(m.group(1))

        tier = (n // 10) % 10

        if n >= 4000:
            return {
                0: 75,
                5: 130,
                6: 160,
                7: 230,
                8: 320,
                9: 450
            }.get(tier, 200)

        if n >= 1600:
            return {
                0: 75,
                5: 100,
                6: 125,
                7: 175,
                8: 250
            }.get(tier, 160)

        return {
            0: 75,
            5: 120,
            6: 150,
            7: 180,
            8: 250,
            9: 300
        }.get(tier, 160)

    m = re.search(
        r'RX\s*(\d{4})',
        texto
    )

    if m:
        return {
            5: 160,
            6: 175,
            7: 250,
            8: 300,
            9: 350
        }.get(
            int(m.group(1)) // 100 % 10,
            200
        )

    if any(
        x in texto
        for x in (
            'GT 710',
            'GT710',
            'QUADRO',
            'ARC A'
        )
    ):
        return 100

    return None


# ============================================================
# FORMATOS COMPATIBLES DE CASE
# ============================================================

def formatos_case(tipo):
    texto = str(tipo).upper().replace(
        '-',
        ' '
    )

    if (
        'MICROATX' in texto
        or 'MICRO ATX' in texto
    ):
        return {
            'MICRO ATX',
            'MINI ITX'
        }

    if 'ATX' in texto:
        return {
            'ATX',
            'MICRO ATX',
            'MINI ITX'
        }

    if 'MINI ITX' in texto:
        return {
            'MINI ITX'
        }

    return set()


# ============================================================
# TAMAÑO MÁXIMO ESTIMADO DE GPU PARA EL CASE
# ============================================================

def max_gpu_case_estimada(tipo):
    texto = str(tipo).upper()

    if 'FULL TOWER' in texto:
        return 420

    if 'MID TOWER' in texto:
        return 360

    if 'MINI TOWER' in texto:
        return 320

    if 'MINI ITX' in texto:
        return 300

    return 330


# ============================================================
# SELECCIONAR CANDIDATOS
# ============================================================

def seleccionar_candidatos(
    usuario,
    limite=6,
    tasa_usd_cop=None,
    moneda_precios='USD'
):
    presupuesto = float(
        usuario['presupuesto']
    )

    if presupuesto <= 0:
        raise ValueError(
            'El presupuesto debe ser mayor que cero.'
        )

    moneda = str(
        moneda_precios
    ).upper()

    if moneda == 'USD':

        if (
            tasa_usd_cop is None
            or not np.isfinite(
                float(tasa_usd_cop)
            )
            or float(tasa_usd_cop) <= 0
        ):
            raise ValueError(
                'Indica una tasa_usd_cop positiva '
                'y vigente para precios en USD.'
            )

    elif moneda != 'COP':

        raise ValueError(
            "moneda_precios debe ser 'USD' o 'COP'."
        )

    # Porcentaje máximo aproximado del presupuesto
    # destinado a cada tipo de componente.
    topes = {
        'cpu': 0.30,
        'cpu-cooler': 0.08,
        'motherboard': 0.20,
        'memory': 0.18,
        'internal-hard-drive': 0.12,
        'video-card': 0.48,
        'power-supply': 0.15,
        'case': 0.12
    }

    resultado = {}

    for tipo, proporcion in topes.items():

        t = componentes[tipo].copy()

        t['price_original'] = pd.to_numeric(
            t['price_original'],
            errors='coerce'
        )

        # Conversión de precios.
        if moneda == 'USD':

            t['price'] = (
                t['price_original']
                * float(tasa_usd_cop)
            )

        else:

            t['price'] = t['price_original']

        # Filtrar precios válidos y que estén
        # dentro del porcentaje asignado.
        t = t.loc[
            t['price'].notna()
            & np.isfinite(t['price'])
            & t['price'].gt(0)
            & t['price'].le(
                presupuesto * proporcion
            )
        ].copy()

        # ----------------------------------------------------
        # CPU
        # ----------------------------------------------------

        if tipo == 'cpu':

            t = t.loc[
                t['name']
                .map(inferir_socket_cpu)
                .notna()
                &
                pd.to_numeric(
                    t['core_count'],
                    errors='coerce'
                ).ge(4)
            ]

            preferencia = usuario.get(
                'preferencia_marca'
            )

            if preferencia in (
                'AMD',
                'Intel'
            ):

                t = t.loc[
                    t['name']
                    .str.upper()
                    .str.startswith(
                        preferencia.upper()
                    )
                ]

        # ----------------------------------------------------
        # MOTHERBOARD
        # ----------------------------------------------------

        elif tipo == 'motherboard':

            t = t.loc[
                t['socket'].isin(
                    [
                        'AM4',
                        'AM5',
                        'LGA1700',
                        'LGA1851'
                    ]
                )
            ]

        # ----------------------------------------------------
        # MEMORY
        # ----------------------------------------------------

        elif tipo == 'memory':

            t['_gb'] = t['modules'].map(
                lambda x: parsear_modulos(x)[1]
            )

            t['_ram_type'] = t.apply(
                inferir_tipo_ram,
                axis=1
            )

            t = t.loc[
                t['_gb'].ge(16)
                &
                t['_ram_type'].notna()
            ]

        # ----------------------------------------------------
        # STORAGE
        # ----------------------------------------------------

        elif tipo == 'internal-hard-drive':

            t = t.loc[
                pd.to_numeric(
                    t['capacity'],
                    errors='coerce'
                ).ge(500)
            ]

            if str(
                usuario['uso_principal']
            ).casefold() in (
                'gaming',
                'programación',
                'programacion'
            ):

                t = t.loc[
                    t['type']
                    .astype(str)
                    .str.upper()
                    .eq('SSD')
                ]

        # ----------------------------------------------------
        # VIDEO CARD
        # ----------------------------------------------------

        elif tipo == 'video-card':

            vram_minima = (
                8
                if usuario['resolucion']
                in ('1440p', '4K')
                else 6
            )

            t = t.loc[
                pd.to_numeric(
                    t['memory'],
                    errors='coerce'
                ).ge(vram_minima)
                &
                t['chipset']
                .map(estimar_tdp_gpu)
                .notna()
            ]

            preferencia = usuario.get(
                'preferencia_marca'
            )

            if preferencia == 'NVIDIA':

                t = t.loc[
                    t['chipset'].str.contains(
                        'GeForce|NVIDIA',
                        case=False,
                        na=False
                    )
                ]

            elif preferencia == 'AMD':

                t = t.loc[
                    t['chipset'].str.contains(
                        'Radeon|AMD',
                        case=False,
                        na=False
                    )
                ]

        # ----------------------------------------------------
        # POWER SUPPLY
        # ----------------------------------------------------

        elif tipo == 'power-supply':

            t = t.loc[
                pd.to_numeric(
                    t['wattage'],
                    errors='coerce'
                ).ge(500)
            ]

        # ----------------------------------------------------
        # CASE
        # ----------------------------------------------------

        elif tipo == 'case':

            t = t.loc[
                t['type']
                .map(formatos_case)
                .map(bool)
            ]

        # Ordenar por precio y eliminar duplicados.
        t = (
            t.sort_values('price')
            .drop_duplicates('name')
        )

        # Seleccionar una cantidad limitada y
        # distribuida a lo largo del catálogo.
        if t.empty:

            resultado[tipo] = t

        else:

            ix = np.linspace(
                0,
                len(t) - 1,
                min(limite, len(t))
            ).round().astype(int)

            resultado[tipo] = t.iloc[
                np.unique(ix)
            ].copy()

    return resultado


# ============================================================
# VALIDAR CONFIGURACIÓN
# ============================================================

def validar_configuracion(c):

    cpu = c['cpu']
    cooler = c['cpu-cooler']
    mobo = c['motherboard']
    ram = c['memory']
    gpu = c['video-card']
    psu = c['power-supply']
    case = c['case']

    # --------------------------------------------------------
    # SOCKET CPU / MOTHERBOARD
    # --------------------------------------------------------

    socket = inferir_socket_cpu(
        cpu['name']
    )

    if (
        socket is None
        or socket != str(
            mobo['socket']
        ).upper()
    ):
        return (
            False,
            'Socket CPU/motherboard incompatible o desconocido.'
        )

    # --------------------------------------------------------
    # TIPO DE RAM
    # --------------------------------------------------------

    ram_type = inferir_tipo_ram(
        ram
    )

    if (
        ram_type is None
        or ram_type != inferir_ram_motherboard(
            mobo
        )
    ):
        return (
            False,
            'Tipo de RAM no coincide o no se pudo inferir.'
        )

    # --------------------------------------------------------
    # CAPACIDAD Y RANURAS DE RAM
    # --------------------------------------------------------

    count, gb = parsear_modulos(
        ram['modules']
    )

    if (
        count is None
        or count > int(
            mobo['memory_slots']
        )
        or gb > float(
            mobo['max_memory']
        )
    ):
        return (
            False,
            'RAM supera las ranuras/capacidad de motherboard.'
        )

    # --------------------------------------------------------
    # FORMATO MOTHERBOARD / CASE
    # --------------------------------------------------------

    form = str(
        mobo['form_factor']
    ).upper().replace(
        '-',
        ' '
    )

    if form not in formatos_case(
        case['type']
    ):
        return (
            False,
            'Formato motherboard no admitido por case.'
        )

    # --------------------------------------------------------
    # FUENTE DE PODER
    # --------------------------------------------------------

    gpu_w = estimar_tdp_gpu(
        gpu['chipset']
    )

    cpu_w = pd.to_numeric(
        cpu['tdp'],
        errors='coerce'
    )

    psu_w = pd.to_numeric(
        psu['wattage'],
        errors='coerce'
    )

    if (
        gpu_w is None
        or pd.isna(cpu_w)
        or pd.isna(psu_w)
        or psu_w < (
            float(cpu_w)
            + gpu_w
            + 100
        ) * 1.25
    ):
        return (
            False,
            'PSU insuficiente según estimación de consumo.'
        )

    # --------------------------------------------------------
    # LONGITUD DE GPU / CASE
    # --------------------------------------------------------

    gpu_length = pd.to_numeric(
        gpu.get('length'),
        errors='coerce'
    )

    if (
        not pd.isna(gpu_length)
        and gpu_length >
        max_gpu_case_estimada(
            case['type']
        )
    ):
        return (
            False,
            'GPU excede largo estimado de gabinete.'
        )

    # --------------------------------------------------------
    # COMPATIBILIDAD ESTIMADA DEL COOLER
    # --------------------------------------------------------

    name = str(
        cooler['name']
    ).upper()

    if (
        socket.startswith('AM')
        and re.search(
            r'LGA\s*\d{4}',
            name
        )
        and not any(
            x in name
            for x in (
                'AM4',
                'AM5'
            )
        )
    ):
        return (
            False,
            'Cooler indica socket Intel.'
        )

    if (
        socket.startswith('LGA')
        and re.search(
            r'AM[245]',
            name
        )
        and 'LGA' not in name
    ):
        return (
            False,
            'Cooler indica socket AMD.'
        )

    return (
        True,
        'Compatibilidad estimada: socket CPU inferido del nombre '
        '(sin validar BIOS/chipset), TDP GPU y límite de case '
        'son heurísticos; socket/capacidad del cooler no está en CSV.'
    )


# ============================================================
# PREPARAR CARACTERÍSTICAS PARA EL MODELO
# ============================================================

def preparar_X(c, usuario, costo):

    cpu = c['cpu']
    mobo = c['motherboard']
    ram = c['memory']
    gpu = c['video-card']
    drive = c['internal-hard-drive']

    _, gb = parsear_modulos(
        ram['modules']
    )

    chipset = str(
        gpu['chipset']
    )

    inter = str(
        drive['interface']
    ).upper()

    tipo = str(
        drive['type']
    )

    datos = {

        'presupuesto_disponible':
            float(usuario['presupuesto']),

        'costo_estimado':
            costo,

        'presupuesto_restante':
            float(usuario['presupuesto']) - costo,

        'porcentaje_presupuesto':
            costo /
            float(usuario['presupuesto']) *
            100,

        'uso_principal':
            usuario['uso_principal'],

        'uso_secundario':
            usuario.get(
                'uso_secundario'
            ) or 'No aplica',

        'resolucion':
            usuario['resolucion'],

        'fps_objetivo':
            usuario['fps_objetivo'],

        'juego':
            usuario.get(
                'juego'
            ) or 'No aplica',

        'software':
            usuario.get(
                'software'
            ) or 'No aplica',

        'preferencia_marca':
            usuario.get(
                'preferencia_marca'
            ) or 'Sin preferencia',

        'cpu':
            cpu['name'],

        'fabricante_cpu':
            'AMD'
            if str(
                cpu['name']
            ).upper().startswith('AMD')
            else 'Intel',

        'gpu':
            chipset,

        'fabricante_gpu':
            'NVIDIA'
            if any(
                x in chipset.upper()
                for x in (
                    'GEFORCE',
                    'NVIDIA'
                )
            )
            else 'AMD',

        'ram_gb':
            gb,

        'vram_gb':
            gpu['memory'],

        'placa_base':
            mobo['name'],

        'socket':
            mobo['socket'],

        'almacenamiento_gb':
            drive['capacity'],

        'tipo_almacenamiento':
            'SSD NVMe'
            if 'NVME' in inter
            else (
                'SSD'
                if 'SSD' in tipo.upper()
                else tipo
            ),

        'potencia_psu':
            c['power-supply']['wattage'],

        'formato_gabinete':
            mobo['form_factor']
    }

    # IMPORTANTE:
    # Aquí usamos FEATURE_COLUMNS y no X.columns,
    # porque X solamente existía en el notebook.
    faltan = [
        col
        for col in FEATURE_COLUMNS
        if col not in datos
    ]

    if faltan:
        raise ValueError(
            f'Faltan características para el modelo: {faltan}'
        )

    return {
        col: datos[col]
        for col in FEATURE_COLUMNS
    }


# ============================================================
# FORMATEAR PRECIOS EN COP
# ============================================================

def formatear_cop(valor):

    return (
        '$ '
        + f"{int(round(float(valor))):,}"
        .replace(',', '.')
        + ' COP'
    )


# ============================================================
# RECOMENDAR CONFIGURACIONES
# ============================================================

def recomendar(
    usuario,
    cantidad=5,
    candidatos_por_tipo=6,
    tasa_usd_cop=None,
    moneda_precios='USD'
):
    """
    Genera configuraciones de PC compatibles
    dentro del presupuesto y las evalúa con
    el modelo de Machine Learning.

    tasa_usd_cop:
        Se exige cuando los precios originales
        de los catálogos están en USD.

    moneda_precios:
        'USD' si los CSV tienen precios en dólares.
        'COP' si los CSV ya están en pesos colombianos.
    """

    # ========================================================
    # VALIDAR DATOS DEL USUARIO
    # ========================================================

    obligatorios = [
        'presupuesto',
        'uso_principal',
        'resolucion',
        'fps_objetivo'
    ]

    faltan = [
        k
        for k in obligatorios
        if k not in usuario
        or usuario[k] is None
    ]

    if faltan:
        raise ValueError(
            f'Faltan datos de usuario: {faltan}'
        )

    if (
        cantidad < 1
        or candidatos_por_tipo < 1
    ):
        raise ValueError(
            'cantidad y candidatos_por_tipo deben ser positivos.'
        )

    # ========================================================
    # SELECCIONAR CANDIDATOS
    # ========================================================

    cand = seleccionar_candidatos(
        usuario,
        candidatos_por_tipo,
        tasa_usd_cop,
        moneda_precios
    )

    vacios = [
        k
        for k, v in cand.items()
        if v.empty
    ]

    if vacios:

        print(
            f'No hay candidatos utilizables para: {vacios}'
        )

        return pd.DataFrame()

    print(
        'Candidatos seleccionados:',
        {
            k: len(v)
            for k, v in cand.items()
        }
    )

    # ========================================================
    # LISTAS PARA CONFIGURACIONES Y CARACTERÍSTICAS
    # ========================================================

    candidatas = []
    filas_X = []

    vistos = set()

    # Límite de seguridad para evitar generar
    # demasiadas configuraciones.
    MAX_CANDIDATAS = 3000

    detener_generacion = False

    # ========================================================
    # CONSTRUCCIÓN GUIADA DE CONFIGURACIONES
    # ========================================================

    # Construcción guiada por pares CPU/GPU.
    # Esto evita hacer directamente el producto
    # cartesiano de todos los catálogos.

    for _, cpu in cand['cpu'].iterrows():

        if detener_generacion:
            break

        socket = inferir_socket_cpu(
            cpu['name']
        )

        placas = cand['motherboard'].loc[
            cand['motherboard']['socket'] == socket
        ]

        for _, gpu in cand['video-card'].iterrows():

            if detener_generacion:
                break

            watts = estimar_tdp_gpu(
                gpu['chipset']
            )

            psus = cand['power-supply'].loc[
                pd.to_numeric(
                    cand['power-supply']['wattage'],
                    errors='coerce'
                ).ge(
                    (
                        float(cpu['tdp'])
                        + watts
                        + 100
                    ) * 1.25
                )
            ].nsmallest(
                2,
                'price'
            )

            for _, mobo in placas.iterrows():

                if detener_generacion:
                    break

                ram_tipo = inferir_ram_motherboard(
                    mobo
                )

                rams = cand['memory'].loc[
                    cand['memory']['_ram_type']
                    == ram_tipo
                ]

                formatos = formatos_case(
                    mobo['form_factor']
                )

                cases = cand['case'].loc[
                    cand['case']['type'].map(
                        lambda x:
                        bool(
                            formatos
                            & formatos_case(x)
                        )
                    )
                ].nsmallest(
                    2,
                    'price'
                )

                drives = cand[
                    'internal-hard-drive'
                ].nlargest(
                    2,
                    'capacity'
                )

                coolers = cand[
                    'cpu-cooler'
                ].nsmallest(
                    2,
                    'price'
                )

                for _, ram in rams.iterrows():

                    count, gb = parsear_modulos(
                        ram['modules']
                    )

                    if (
                        count is None
                        or count >
                        int(mobo['memory_slots'])
                        or gb >
                        float(mobo['max_memory'])
                    ):
                        continue

                    # ====================================================
                    # COMBINAR PSU + CASE + STORAGE + COOLER
                    # ====================================================

                    for (
                        (_, psu),
                        (_, case),
                        (_, drive),
                        (_, cooler)
                    ) in product(
                        psus.iterrows(),
                        cases.iterrows(),
                        drives.iterrows(),
                        coolers.iterrows()
                    ):

                        c = {
                            'cpu': cpu,
                            'cpu-cooler': cooler,
                            'motherboard': mobo,
                            'memory': ram,
                            'internal-hard-drive': drive,
                            'video-card': gpu,
                            'power-supply': psu,
                            'case': case
                        }

                        # =================================================
                        # VALIDAR COMPATIBILIDAD
                        # =================================================

                        ok, nota = validar_configuracion(
                            c
                        )

                        if not ok:
                            continue

                        # =================================================
                        # IDENTIFICAR CONFIGURACIÓN ÚNICA
                        # =================================================

                        key = tuple(
                            str(
                                c[t]['name']
                            )
                            for t in archivos_componentes
                        )

                        # =================================================
                        # CALCULAR COSTO
                        # =================================================

                        costo = sum(
                            float(
                                c[t]['price']
                            )
                            for t in archivos_componentes
                        )

                        # =================================================
                        # FILTRAR DUPLICADOS Y PRESUPUESTO
                        # =================================================

                        if (
                            key in vistos
                            or costo >
                            float(
                                usuario['presupuesto']
                            )
                        ):
                            continue

                        vistos.add(key)

                        # =================================================
                        # PREPARAR CARACTERÍSTICAS
                        # =================================================

                        fila_X = preparar_X(
                            c,
                            usuario,
                            costo
                        )

                        # Guardamos la configuración y
                        # sus características.
                        candidatas.append(
                            (
                                c,
                                costo,
                                nota
                            )
                        )

                        filas_X.append(
                            fila_X
                        )

                        # =================================================
                        # LÍMITE DE SEGURIDAD
                        # =================================================

                        if len(candidatas) >= MAX_CANDIDATAS:

                            detener_generacion = True
                            break

                    if detener_generacion:
                        break

                if detener_generacion:
                    break

            if detener_generacion:
                break

    # ========================================================
    # SI NO HAY CONFIGURACIONES
    # ========================================================

    if not candidatas:

        print(
            'No se encontraron configuraciones dentro '
            'del presupuesto con los filtros y reglas actuales.'
        )

        return pd.DataFrame()

    # ========================================================
    # PREDICCIÓN EN LOTE
    # ========================================================

    # En lugar de llamar predict() para cada configuración,
    # hacemos una sola predicción para todas.

    XX = pd.DataFrame(
        filas_X,
        columns=FEATURE_COLUMNS
    )

    cats = mejor_modelo.predict(
        XX
    )

    probs = mejor_modelo.predict_proba(
        XX
    )

    clases = list(
        mejor_modelo.classes_
    )

    # ========================================================
    # CONSTRUIR RESULTADOS
    # ========================================================

    filas = []

    for (
        (c, costo, nota),
        categoria,
        p
    ) in zip(
        candidatas,
        cats,
        probs
    ):

        prob = p[
            clases.index(categoria)
        ]

        cpu = c['cpu']
        cooler = c['cpu-cooler']
        mobo = c['motherboard']
        ram = c['memory']

        drive = c[
            'internal-hard-drive'
        ]

        gpu = c[
            'video-card'
        ]

        psu = c[
            'power-supply'
        ]

        case = c[
            'case'
        ]

        filas.append({

            # ------------------------------------------------
            # COMPONENTES
            # ------------------------------------------------

            'CPU':
                cpu['name'],

            'CPU Cooler':
                cooler['name'],

            'Motherboard':
                mobo['name'],

            'Memory':
                ram['name'],

            'Storage':
                drive['name'],

            'Video Card':
                gpu['name'],

            'Power Supply':
                psu['name'],

            'Case':
                case['name'],

            # ------------------------------------------------
            # PRECIO TOTAL
            # ------------------------------------------------

            'precio_total_cop':
                round(costo),

            'precio_total_formateado':
                formatear_cop(costo),

            # ------------------------------------------------
            # PRECIO POR COMPONENTE
            # ------------------------------------------------

            'precio_cpu_cop':
                formatear_cop(
                    cpu['price']
                ),

            'precio_cooler_cop':
                formatear_cop(
                    cooler['price']
                ),

            'precio_motherboard_cop':
                formatear_cop(
                    mobo['price']
                ),

            'precio_memory_cop':
                formatear_cop(
                    ram['price']
                ),

            'precio_storage_cop':
                formatear_cop(
                    drive['price']
                ),

            'precio_video_card_cop':
                formatear_cop(
                    gpu['price']
                ),

            'precio_power_supply_cop':
                formatear_cop(
                    psu['price']
                ),

            'precio_case_cop':
                formatear_cop(
                    case['price']
                ),

            # ------------------------------------------------
            # RESULTADO DEL MODELO
            # ------------------------------------------------

            'categoria':
                categoria,

            'probabilidad_estimada_categoria_pct':
                round(
                    float(prob) * 100,
                    2
                ),

            # ------------------------------------------------
            # COMPATIBILIDAD
            # ------------------------------------------------

            'compatibilidad':
                nota
        })

    # ========================================================
    # CREAR TABLA FINAL
    # ========================================================

    tabla = pd.DataFrame(
        filas
    )

    # Nivel numérico para ordenar las categorías.
    nivel = {
        'Ideal': 4,
        'Excelente': 3,
        'Aceptable': 2,
        'No recomendado': 1
    }

    tabla['_nivel'] = (
        tabla['categoria']
        .map(nivel)
        .fillna(0)
    )

    # Orden:
    # 1. Categoría
    # 2. Probabilidad
    # 3. Precio
    tabla = tabla.sort_values(
        [
            '_nivel',
            'probabilidad_estimada_categoria_pct',
            'precio_total_cop'
        ],
        ascending=[
            False,
            False,
            True
        ]
    )

    # ========================================================
    # SELECCIÓN DIVERSA
    # ========================================================

    elegidas = []

    pares = set()
    cpus = set()
    gpus = set()

    # --------------------------------------------------------
    # Primera pasada:
    # intentar no repetir CPU ni GPU.
    # --------------------------------------------------------

    for _, fila in tabla.iterrows():

        par = (
            fila['CPU'],
            fila['Video Card']
        )

        if (
            par in pares
            or fila['CPU'] in cpus
            or fila['Video Card'] in gpus
        ):
            continue

        elegidas.append(
            fila
        )

        pares.add(
            par
        )

        cpus.add(
            fila['CPU']
        )

        gpus.add(
            fila['Video Card']
        )

        if len(elegidas) >= cantidad:
            break

    # --------------------------------------------------------
    # Segunda pasada:
    # si no alcanzó la cantidad solicitada,
    # permitir repetir CPU/GPU pero no la pareja.
    # --------------------------------------------------------

    if len(elegidas) < cantidad:

        for _, fila in tabla.iterrows():

            par = (
                fila['CPU'],
                fila['Video Card']
            )

            if par in pares:
                continue

            elegidas.append(
                fila
            )

            pares.add(
                par
            )

            if len(elegidas) >= cantidad:
                break

    # ========================================================
    # TABLA DE SALIDA
    # ========================================================

    salida = pd.DataFrame(
        elegidas
    )

    salida['_nivel'] = (
        salida['categoria']
        .map(nivel)
        .fillna(0)
    )

    salida = salida.sort_values(
        [
            '_nivel',
            'probabilidad_estimada_categoria_pct',
            'precio_total_cop'
        ],
        ascending=[
            False,
            False,
            True
        ]
    )

    salida = salida.drop(
        columns='_nivel'
    ).reset_index(
        drop=True
    )

    # ========================================================
    # ID DE CONFIGURACIÓN
    # ========================================================

    salida.insert(
        0,
        'id_configuracion',
        [
            f'PC-{i:03d}'
            for i in range(
                1,
                len(salida) + 1
            )
        ]
    )

    # Avisar si no se pudo llegar a la cantidad solicitada.
    if len(salida) < cantidad:

        print(
            f'Se encontraron '
            f'{len(salida)} configuraciones '
            f'diferentes de '
            f'{cantidad} solicitadas.'
        )

    return salida