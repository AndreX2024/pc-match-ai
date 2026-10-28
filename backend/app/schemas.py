from pydantic import BaseModel, Field
from typing import Optional, Literal


class UsuarioIn(BaseModel):
    presupuesto: float = Field(
        gt=0,
        description="Presupuesto en COP"
    )

    uso_principal: str

    uso_secundario: Optional[str] = None

    resolucion: Literal[
        "1080p",
        "1440p",
        "4K"
    ]

    fps_objetivo: int = Field(
        gt=0
    )

    juego: Optional[str] = None

    software: Optional[str] = None

    preferencia_marca: Optional[
        Literal[
            "AMD",
            "Intel",
            "NVIDIA"
        ]
    ] = None

    cantidad: int = Field(
        5,
        ge=1,
        le=10
    )