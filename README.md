# PC-Match AI 🖥️

Sistema web de recomendación de configuraciones de computadores que genera alternativas según el presupuesto y las necesidades del usuario. PC-Match AI combina reglas de compatibilidad entre componentes con un modelo de Machine Learning que clasifica qué tan adecuada es cada configuración para el perfil solicitado.

## 🌐 Demo

- **Frontend:** https://pc-match-ai.onrender.com
- **API (backend):** https://pc-match-ai-api.onrender.com
- **Documentación interactiva de la API:** https://pc-match-ai-api.onrender.com/docs
- **Estado del backend:** https://pc-match-ai-api.onrender.com/health

> La primera petición al backend puede tardar si el servicio gratuito de Render estaba inactivo.

## ✨ Funcionalidades

- Captura las preferencias del usuario, como presupuesto, uso principal, resolución, FPS objetivo y preferencias opcionales.
- Genera varias configuraciones de PC dentro del presupuesto indicado.
- Evalúa reglas de compatibilidad antes de recomendar una configuración.
- Utiliza un modelo de Machine Learning para asignar una categoría de recomendación.
- Presenta los componentes seleccionados, sus precios y el costo total estimado en pesos colombianos (COP).
- Expone el recomendador mediante una API REST desarrollada con FastAPI.

### Categorías de recomendación

| Categoría | Descripción general |
|---|---|
| **No recomendado** | La configuración presenta una baja adecuación a las necesidades indicadas. |
| **Aceptable** | Puede cubrir parte de las necesidades, con posibles limitaciones. |
| **Excelente** | Presenta una buena adecuación al perfil solicitado. |
| **Ideal** | Es la categoría de mayor adecuación según el modelo. |

Las categorías son una estimación del modelo y no constituyen una garantía de rendimiento real. El resultado depende de los datos disponibles, las reglas implementadas y las características de cada componente.

## 🧠 ¿Cómo funciona?

1. **Entrada del usuario:** el frontend envía las preferencias al backend.
2. **Selección de componentes:** el recomendador explora candidatos de los catálogos disponibles.
3. **Validación:** se aplican reglas de compatibilidad para descartar configuraciones que no cumplen las condiciones implementadas.
4. **Presupuesto:** se descartan alternativas que superan el presupuesto disponible.
5. **Clasificación:** el modelo entrenado estima la categoría de cada configuración válida.
6. **Resultados:** la API devuelve las configuraciones recomendadas, sus componentes, precios y categoría para mostrarlas en la interfaz.

**Importante:** la compatibilidad se evalúa mediante reglas del sistema; no es una decisión que se delegue al modelo de Machine Learning. El modelo estima la adecuación de una configuración que ha pasado las validaciones implementadas.

## 🧰 Tecnologías

### Frontend
- Angular
- TypeScript
- Bootstrap
- CSS

### Backend y Machine Learning
- Python
- FastAPI
- Uvicorn
- Pandas y NumPy
- Scikit-learn
- Joblib

### Datos de componentes
El proyecto utiliza catálogos de componentes derivados del conjunto de datos [`docyx/pc-part-dataset`](https://github.com/docyx/pc-part-dataset), basado en datos de PCPartPicker. Consulta el repositorio original para conocer su procedencia, estructura y condiciones de uso.

## 🗂️ Estructura del proyecto

La estructura puede variar según los cambios realizados durante el desarrollo. La organización principal es:

```text
pcmatch/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── recommender.py
│   ├── artifacts/
│   │   └── modelo.joblib
│   ├── data/
│   │   ├── Pc_match_ia_dataset.csv
│   │   └── componentes/
│   │       ├── cpu.csv
│   │       ├── cpu-cooler.csv
│   │       ├── motherboard.csv
│   │       ├── memory.csv
│   │       ├── internal-hard-drive.csv
│   │       ├── video-card.csv
│   │       ├── power-supply.csv
│   │       └── case.csv
│   ├── requirements.txt
│   └── train.py
├── frontend/
│   ├── src/
│   ├── angular.json
│   ├── package.json
│   └── proxy.conf.json
├── .gitignore
└── README.md
```

- `backend/app/main.py`: crea la API y expone las rutas.
- `backend/app/schemas.py`: define y valida los datos de entrada.
- `backend/app/recommender.py`: carga los catálogos y el modelo, valida componentes y genera recomendaciones.
- `backend/train.py`: entrena y guarda el modelo.
- `backend/artifacts/modelo.joblib`: artefacto del modelo entrenado.
- `backend/data/componentes/`: catálogos utilizados por el recomendador.
- `backend/data/Pc_match_ia_dataset.csv`: conjunto de datos utilizado para entrenar el clasificador.
- `frontend/`: aplicación web Angular.

## ⚙️ Requisitos

Para ejecutar el proyecto localmente necesitas:

- Python y `pip`.
- Node.js y npm.
- Angular CLI compatible con la versión de Angular del proyecto.
- Git.

Se recomienda utilizar una versión de Python compatible con las versiones de `scikit-learn`, `pandas` y demás dependencias registradas en `backend/requirements.txt`.

## 🚀 Ejecución local

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd pcmatch
```

Reemplaza `<URL_DEL_REPOSITORIO>` por la URL del repositorio de GitHub.

### 2. Preparar el backend

Desde la raíz del repositorio, crea y activa un entorno virtual.

**Windows — PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows — Git Bash:**

```bash
python -m venv .venv
source .venv/Scripts/activate
```

Instala las dependencias:

```bash
cd backend
pip install -r requirements.txt
```

Comprueba que estén disponibles el modelo y los catálogos esperados en `backend/artifacts/` y `backend/data/componentes/`.

### 3. Configurar variables de entorno

El backend admite estas variables:

| Variable | Propósito | Valor de ejemplo |
|---|---|---|
| `MONEDA_CATALOGO` | Moneda original de los precios del catálogo. | `USD` |
| `TASA_USD_COP` | Tasa usada para convertir USD a COP. | `4000` |

Los valores anteriores son ejemplos, no una tasa de cambio actualizada. Si el catálogo ya está en COP, configura la moneda según lo que admita la implementación y evita aplicar una conversión adicional.

**Git Bash:**

```bash
MONEDA_CATALOGO=USD TASA_USD_COP=4000 uvicorn app.main:app --reload
```

**PowerShell:**

```powershell
$env:MONEDA_CATALOGO = "USD"
$env:TASA_USD_COP = "4000"
uvicorn app.main:app --reload
```

Ejecuta estos comandos desde la carpeta `backend`. La API estará disponible normalmente en `http://127.0.0.1:8000`.

Rutas útiles durante el desarrollo:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/recomendar` (método `POST`)

### 4. Ejecutar el frontend

Abre otra terminal y entra en la carpeta del frontend:

```bash
cd frontend
npm install
npm start
```

Si el proyecto no tiene un script `start`, utiliza:

```bash
npx ng serve
```

Durante el desarrollo, `frontend/proxy.conf.json` permite que las solicitudes a `/api` se dirijan al backend local. En producción, la configuración de Angular debe apuntar a la URL pública de la API.

## 🔌 API

### `GET /health`

Comprueba el estado del backend y devuelve el nombre del modelo cargado.

Ejemplo de respuesta:

```json
{
  "status": "ok",
  "modelo": "Regresión Logística"
}
```

### `POST /recomendar`

Recibe las preferencias del usuario y devuelve las configuraciones generadas.

Ejemplo de solicitud:

```json
{
  "presupuesto": 5000000,
  "uso_principal": "Gaming",
  "uso_secundario": null,
  "resolucion": "1440p",
  "fps_objetivo": 144,
  "juego": null,
  "software": null,
  "preferencia_marca": null,
  "cantidad": 5
}
```

Ejemplo ilustrativo de la estructura de respuesta:

```json
{
  "total": 1,
  "configuraciones": [
    {
      "id_configuracion": "PC-001",
      "categoria": "Excelente",
      "precio_total_cop": 4800000
    }
  ]
}
```

Los campos del ejemplo de respuesta son ilustrativos y no representan un resultado garantizado. La respuesta real incluye los campos que entrega la implementación del recomendador. Consulta `/docs` para revisar el esquema y probar la API.

## 🧪 Entrenamiento del modelo

El modelo se entrena a partir del conjunto de datos de clasificación ubicado en `backend/data/Pc_match_ia_dataset.csv`.

Para ejecutar el entrenamiento, entra en `backend` y ejecuta:

```bash
python train.py
```

El script debe guardar el artefacto entrenado en `backend/artifacts/modelo.joblib`, de acuerdo con su implementación actual. Antes de volver a entrenar, conserva una copia del artefacto funcional si necesitas comparar resultados.

El entrenamiento y la generación de recomendaciones son procesos distintos: para ejecutar el backend normalmente se carga el modelo guardado; no es necesario entrenarlo cada vez que se inicia la API.

## ☁️ Despliegue

La aplicación está desplegada en Render como dos servicios separados:

- **Frontend:** sitio estático Angular.
- **Backend:** servicio web FastAPI.

URLs públicas:

- Frontend: https://pc-match-ai.onrender.com
- Backend: https://pc-match-ai-api.onrender.com

### CORS

El backend debe permitir el origen del frontend publicado y, para desarrollo local, el origen local correspondiente, por ejemplo:

- `https://pc-match-ai.onrender.com`
- `http://localhost:4200`

## 📌 Alcance y limitaciones

- La calidad de las recomendaciones depende de los catálogos disponibles, las reglas implementadas y los datos usados para entrenar el modelo.
- Las comprobaciones de compatibilidad cubren las condiciones programadas; no garantizan que se hayan detectado todas las incompatibilidades posibles.
- Los precios y la disponibilidad de los componentes pueden cambiar y no deben considerarse cotizaciones en tiempo real salvo que se implemente una actualización de datos.
- La categoría estimada por Machine Learning no garantiza FPS específicos ni rendimiento real en juegos o aplicaciones.
