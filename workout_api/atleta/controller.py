from typing import Optional
from uuid import uuid4
from datetime import datetime
from fastapi import APIRouter, Body, Query, HTTPException, status
from fastapi_pagination import Page, paginate
from pydantic import UUID4
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from workout_api.atleta.schemas import AtletaIn, AtletaOut, AtletaUpdate, AtletaCustom
from workout_api.atleta.models import AtletaModel
from workout_api.categoria.models import CategoriaModel
from workout_api.categoria.schemas import CategoriaOut
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.centro_treinamento.schemas import CentroTreinamentoOut
from workout_api.contrib.dependencies import DataBaseDependency

router = APIRouter()


@router.post(
    "/", summary="Criar novo atleta", status_code=status.HTTP_201_CREATED, response_model=AtletaOut
)
async def post(
    db_session: DataBaseDependency,
    atleta_in: AtletaIn = Body(...),
) -> AtletaOut:
    nome_categoria = atleta_in.categoria.nome
    categoria: CategoriaOut = (
        ((await db_session.execute(select(CategoriaModel).filter_by(nome=nome_categoria))))
        .scalars()
        .first()
    )
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A categoria '{nome_categoria}' não foi encontrada.",
        )

    nome_centro_treinamento = atleta_in.centro_treinamento.nome
    centro_treinamento: CentroTreinamentoOut = (
        (
            (
                await db_session.execute(
                    select(CentroTreinamentoModel).filter_by(nome=nome_centro_treinamento)
                )
            )
        )
        .scalars()
        .first()
    )
    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O centro de treinamento '{nome_centro_treinamento}' não foi encontrado.",
        )
    atleta_out = AtletaOut(id=uuid4(), created_at=datetime.now(), **atleta_in.model_dump())
    atleta_model = AtletaModel(**atleta_out.model_dump(exclude={"categoria", "centro_treinamento"}))
    atleta_model.categoria_id = categoria.pk_id
    atleta_model.centro_treinamento_id = centro_treinamento.pk_id

    try:
        db_session.add(atleta_model)
        await db_session.commit()
    except IntegrityError:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f"Já existe um atleta cadastrado com o cpf: {atleta_in.cpf}.",
        )
    return atleta_out


@router.get(
    "/",
    summary="Consultar todos os atletas",
    status_code=status.HTTP_200_OK,
    response_model=Page[AtletaCustom],
)
async def get(
    db_session: DataBaseDependency,
    nome: Optional[str] = Query(None, description="Nome do atleta"),
    cpf: Optional[str] = Query(None, description="CPF do atleta"),
) -> list[AtletaCustom]:

    query = select(AtletaModel)

    if nome:
        query = query.filter_by(nome=nome)
    elif cpf:
        query = query.filter_by(cpf=cpf)

    atletas = (await db_session.execute(query)).scalars().all()
    if not atletas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum atleta encontrado.",
        )

    return paginate([AtletaCustom.model_validate(atleta) for atleta in atletas])


@router.get(
    "/{id}",
    summary="Consultar atleta pelo id",
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def get(db_session: DataBaseDependency, id: UUID4) -> AtletaModel:
    atleta: AtletaModel = (
        ((await db_session.execute(select(AtletaModel).filter_by(id=id)))).scalars().first()
    )
    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atleta não encontrada no id: {id}",
        )
    return atleta


@router.patch(
    "/{id}",
    summary="Atualizar atleta pelo id",
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def get(
    db_session: DataBaseDependency, id: UUID4, atleta_up: AtletaUpdate = Body(...)
) -> AtletaModel:
    atleta: AtletaModel = (
        ((await db_session.execute(select(AtletaModel).filter_by(id=id)))).scalars().first()
    )
    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atleta não encontrada no id: {id}",
        )

    atleta_update = atleta_up.model_dump(exclude_unset=True)
    for key, value in atleta_update.items():
        setattr(atleta, key, value)

    await db_session.commit()
    await db_session.refresh(atleta)

    return atleta


@router.delete(
    "/{id}",
    summary="Deletar atleta pelo id",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def get(db_session: DataBaseDependency, id: UUID4) -> None:
    atleta: AtletaModel = (
        ((await db_session.execute(select(AtletaModel).filter_by(id=id)))).scalars().first()
    )
    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atleta não encontrada no id: {id}",
        )
    await db_session.delete(atleta)
    await db_session.commit()
