from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)


# ============================================================
# 1. RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "data" / "Pc_match_ia_dataset.csv"
ARTIFACTS_DIR = BASE_DIR / "artifacts"


# ============================================================
# 2. CARGAR DATASET
# ============================================================

if not DATASET_PATH.is_file():
    raise FileNotFoundError(
        f"No se encontró el dataset: {DATASET_PATH}"
    )

df = pd.read_csv(DATASET_PATH)

print(f"Dataset cargado: {df.shape[0]} filas, {df.shape[1]} columnas.")


# ============================================================
# 3. DEFINIR X E Y
# ============================================================

objetivo = "categoria_match"

columnas_compatibilidad = [
    "compat_cpu_mobo",
    "compat_ram_mobo",
    "compat_gpu_psu",
    "compat_motherboard_case",
    "compat_cooling_cpu",
    "compatibilidad_tecnica"
]

columnas_excluir = [
    "id_configuracion",
    objetivo,
    *columnas_compatibilidad,
    "balance_cpu_gpu",
    "adecuacion_uso",
    "refrigeracion"
]

# Solo excluir columnas que realmente existan
columnas_excluir = [
    col for col in columnas_excluir
    if col in df.columns
]

X = df.drop(columns=columnas_excluir)

y = df[objetivo].astype(str)


print(f"Características utilizadas: {X.shape[1]}")
print(f"Configuraciones: {X.shape[0]}")


# ============================================================
# 4. IDENTIFICAR TIPOS DE VARIABLES
# ============================================================

variables_categoricas = X.select_dtypes(
    include=["object", "string", "category"]
).columns.tolist()

variables_numericas = X.select_dtypes(
    include=[np.number]
).columns.tolist()


print("Variables categóricas:", variables_categoricas)
print("Variables numéricas:", variables_numericas)


# ============================================================
# 5. DIVISIÓN TRAIN / TEST
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print()
print("Datos de entrenamiento:", X_train.shape)
print("Datos de prueba:", X_test.shape)


# ============================================================
# 6. PREPROCESAMIENTO
# ============================================================

preprocesador = ColumnTransformer(
    transformers=[
        (
            "categoricas",
            OneHotEncoder(handle_unknown="ignore"),
            variables_categoricas
        ),
        (
            "numericas",
            StandardScaler(),
            variables_numericas
        )
    ]
)


# ============================================================
# 7. REGRESIÓN LOGÍSTICA
# ============================================================

modelo_logistico = Pipeline(
    steps=[
        (
            "preprocesamiento",
            preprocesador
        ),
        (
            "modelo",
            LogisticRegression(
                max_iter=2000,
                random_state=42,
                class_weight="balanced"
            )
        )
    ]
)


# ============================================================
# 8. RANDOM FOREST
# ============================================================

modelo_random_forest = Pipeline(
    steps=[
        (
            "preprocesamiento",
            preprocesador
        ),
        (
            "modelo",
            RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                class_weight="balanced"
            )
        )
    ]
)


# ============================================================
# 9. KNN
# ============================================================

modelo_knn = Pipeline(
    steps=[
        (
            "preprocesamiento",
            preprocesador
        ),
        (
            "modelo",
            KNeighborsClassifier(
                n_neighbors=5,
                weights="distance"
            )
        )
    ]
)


# ============================================================
# 10. ENTRENAMIENTO
# ============================================================

print()
print("Entrenando modelos...")

modelo_logistico.fit(X_train, y_train)
print("Regresión Logística entrenada.")

modelo_random_forest.fit(X_train, y_train)
print("Random Forest entrenado.")

modelo_knn.fit(X_train, y_train)
print("KNN entrenado.")


# ============================================================
# 11. PREDICCIONES
# ============================================================

pred_logistico = modelo_logistico.predict(X_test)

pred_random_forest = modelo_random_forest.predict(X_test)

pred_knn = modelo_knn.predict(X_test)


# ============================================================
# 12. EVALUACIÓN
# ============================================================

def evaluar_modelo(nombre, predicciones):

    accuracy = accuracy_score(
        y_test,
        predicciones
    )

    precision = precision_score(
        y_test,
        predicciones,
        average="weighted",
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predicciones,
        average="weighted",
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predicciones,
        average="weighted",
        zero_division=0
    )

    print()
    print("=" * 60)
    print(nombre)
    print("=" * 60)

    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1-Score : {f1:.4f}")

    print()
    print("Reporte de clasificación:")

    print(
        classification_report(
            y_test,
            predicciones,
            zero_division=0
        )
    )

    return {
        "Modelo": nombre,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1-Score": f1
    }


# ============================================================
# 13. COMPARAR MODELOS
# ============================================================

resultados = []

resultados.append(
    evaluar_modelo(
        "Regresión Logística",
        pred_logistico
    )
)

resultados.append(
    evaluar_modelo(
        "Random Forest",
        pred_random_forest
    )
)

resultados.append(
    evaluar_modelo(
        "KNN",
        pred_knn
    )
)


resultados_df = pd.DataFrame(resultados)

resultados_df = resultados_df.sort_values(
    by="F1-Score",
    ascending=False
)


print()
print("=" * 60)
print("COMPARACIÓN DE MODELOS")
print("=" * 60)

print(
    resultados_df.to_string(index=False)
)


# ============================================================
# 14. SELECCIONAR EL MEJOR MODELO
# ============================================================

mejor_modelo_nombre = resultados_df.iloc[0]["Modelo"]


modelos_entrenados = {
    "Regresión Logística": modelo_logistico,
    "Random Forest": modelo_random_forest,
    "KNN": modelo_knn
}


mejor_modelo = modelos_entrenados[
    mejor_modelo_nombre
]


print()
print("=" * 60)
print("MODELO SELECCIONADO")
print("=" * 60)

print(
    f"Modelo seleccionado: {mejor_modelo_nombre}"
)


# ============================================================
# 15. GUARDAR MODELO
# ============================================================

ARTIFACTS_DIR.mkdir(
    exist_ok=True
)

modelo_path = ARTIFACTS_DIR / "modelo.joblib"


joblib.dump(
    {
        "model": mejor_modelo,
        "columns": X.columns.tolist(),
        "nombre": mejor_modelo_nombre
    },
    modelo_path
)


print()
print(f"Modelo guardado en:")
print(modelo_path)