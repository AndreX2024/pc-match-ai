import os
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool

from .schemas import UsuarioIn
from . import recommender


MONEDA = os.getenv("MONEDA_CATALOGO", "USD")
TASA = float(os.getenv("TASA_USD_COP", "0")) or None


app = FastAPI(title="PC-Match AI")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "https://pc-match-ai.onrender.com"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "modelo": recommender._art["nombre"]
    }


@app.post("/recomendar")
async def recomendar(datos: UsuarioIn):

    usuario = datos.model_dump(exclude={"cantidad"})

    try:
        df = await run_in_threadpool(
            recommender.recomendar,
            usuario,
            cantidad=datos.cantidad,
            tasa_usd_cop=TASA,
            moneda_precios=MONEDA,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )

    registros = json.loads(
        df.to_json(
            orient="records",
            force_ascii=False
        )
    )

    return {
        "total": len(registros),
        "configuraciones": registros
    }