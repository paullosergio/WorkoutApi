from uuid import uuid4
from fastapi import APIRouter, Body, HTTPException, status
from pydantic import UUID4
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from workout_api.categoria.schemas import CategoriaIn, CategoriaOut
from workout_api.categoria.models import CategoriaModel
from workout_api.contrib.dependencies import DataBaseDependency

router = APIRouter()


@router.post(
    "/",
    summary="Criar nova categoria",
    status_code=status.HTTP_201_CREATED,
    response_model=CategoriaOut,
)
async def post(
    db_session: DataBaseDependency, categoria_in: CategoriaIn = Body(...)
) -> CategoriaOut:
    categoria_out = CategoriaOut(id=uuid4(), **categoria_in.model_dump())
    categoria_model = CategoriaModel(**categoria_out.model_dump())

    try:
        db_session.add(categoria_model)
        await db_session.commit()
    except IntegrityError:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f"Já existe uma categoria com esse nome: {categoria_in.nome}.",
        )
    return categoria_out


@router.get(
    "/",
    summary="Consultar todas as categorias",
    status_code=status.HTTP_200_OK,
    response_model=list[CategoriaOut],
)
async def get(
    db_session: DataBaseDependency,
) -> list[CategoriaOut]:
    categorias: list[CategoriaOut] = (
        (await db_session.execute(select(CategoriaModel))).scalars().all()
    )
    if not categorias:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma categoria encontrada."
        )
    return categorias


@router.get(
    "/{id}",
    summary="Consultar categoria pelo id",
    status_code=status.HTTP_200_OK,
    response_model=CategoriaOut,
)
async def get(db_session: DataBaseDependency, id: UUID4) -> CategoriaOut:
    categoria: CategoriaOut = (
        ((await db_session.execute(select(CategoriaModel).filter_by(id=id)))).scalars().first()
    )
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Categoria não encontrada no id: {id}"
        )
    return categoria

@router.delete(
    "/{id}",
    summary="Deletar categoria pelo id",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def get(db_session: DataBaseDependency, id: UUID4) -> None:
    categoria: CategoriaModel = (
        ((await db_session.execute(select(CategoriaModel).filter_by(id=id)))).scalars().first()
    )
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoria não encontrada no id: {id}",
        )
    try:
        await db_session.delete(categoria)
        await db_session.commit()
    except IntegrityError:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,        
            detail=f"Esta categoria contém atletas e não pode ser excluída.",
        )

@router.patch(
    "/{id}",
    summary="Atualizar categoria pelo id",
    status_code=status.HTTP_200_OK,
    response_model=CategoriaOut,
)
async def get(
    db_session: DataBaseDependency, id: UUID4, categoria_up: CategoriaIn = Body(...)
) -> CategoriaModel:
    categoria: CategoriaModel = (
        ((await db_session.execute(select(CategoriaModel).filter_by(id=id)))).scalars().first()
    )
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoria não encontrada no id: {id}",
        )

    categoria_update = categoria_up.model_dump(exclude_unset=True)
    for key, value in categoria_update.items():
        setattr(categoria, key, value)
    
    await db_session.commit()
    await db_session.refresh(categoria)

    return categoria