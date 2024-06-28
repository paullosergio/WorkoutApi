from uuid import uuid4
from fastapi import APIRouter, Body, status, HTTPException
from pydantic import UUID4
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError


from workout_api.centro_treinamento.schemas import (
    CentroTreinamentoIn,
    CentroTreinamentoOut,
    CentroTreinamentoUpdate,
)
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.contrib.dependencies import DataBaseDependency

router = APIRouter()


@router.post(
    "/",
    summary="Criar novo centro de treinamento",
    status_code=status.HTTP_201_CREATED,
    response_model=CentroTreinamentoOut,
)
async def post(
    db_session: DataBaseDependency, centro_treinamento_in: CentroTreinamentoIn = Body(...)
) -> CentroTreinamentoOut:
    centro_treinamento_out = CentroTreinamentoOut(id=uuid4(), **centro_treinamento_in.model_dump())
    centro_treinamento_model = CentroTreinamentoModel(**centro_treinamento_out.model_dump())

    try:
        db_session.add(centro_treinamento_model)
        await db_session.commit()
    except IntegrityError:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f"Já existe um centro de treinamento com esse nome: {centro_treinamento_in.nome}.",
        )
    return centro_treinamento_out


@router.get(
    "/",
    summary="Consultar todos os centros de treinamento",
    status_code=status.HTTP_200_OK,
    response_model=list[CentroTreinamentoOut],
)
async def get(
    db_session: DataBaseDependency,
) -> list[CentroTreinamentoOut]:
    centros_treinamento: list[CentroTreinamentoOut] = (
        (await db_session.execute(select(CentroTreinamentoModel))).scalars().all()
    )
    if not centros_treinamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Nenhum centro de treinamento encontrado."
        )
    return centros_treinamento


@router.get(
    "/{id}",
    summary="Consultar centro de treinamento pelo id",
    status_code=status.HTTP_200_OK,
    response_model=CentroTreinamentoOut,
)
async def get(db_session: DataBaseDependency, id: UUID4) -> CentroTreinamentoOut:
    centro_treinamento: CentroTreinamentoOut = (
        ((await db_session.execute(select(CentroTreinamentoModel).filter_by(id=id))))
        .scalars()
        .first()
    )
    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centro de treinamento não encontrada no id: {id}",
        )
    return centro_treinamento


@router.delete(
    "/{id}",
    summary="Deletar categoria pelo id",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def get(db_session: DataBaseDependency, id: UUID4) -> None:
    centro_treinamento: CentroTreinamentoModel = (
        ((await db_session.execute(select(CentroTreinamentoModel).filter_by(id=id))))
        .scalars()
        .first()
    )
    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centro de treinamento não encontrada no id: {id}",
        )
    try:
        await db_session.delete(centro_treinamento)
        await db_session.commit()
    except IntegrityError:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f"Centro de treinamento com id: '{id}' não pode ser excluído.",
        )


@router.patch(
    "/{id}",
    summary="Atualizar centro de treinamento pelo id",
    status_code=status.HTTP_200_OK,
    response_model=CentroTreinamentoOut,
)
async def get(
    db_session: DataBaseDependency,
    id: UUID4,
    centro_treinamento_up: CentroTreinamentoUpdate = Body(...),
) -> CentroTreinamentoModel:
    centro_treinamento: CentroTreinamentoModel = (
        ((await db_session.execute(select(CentroTreinamentoModel).filter_by(id=id))))
        .scalars()
        .first()
    )
    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centro de treinamento não encontrada no id: {id}",
        )

    centro_treinamento_update = centro_treinamento_up.model_dump(exclude_unset=True)
    for key, value in centro_treinamento_update.items():
        setattr(centro_treinamento, key, value)

    await db_session.commit()
    await db_session.refresh(centro_treinamento)

    return centro_treinamento
