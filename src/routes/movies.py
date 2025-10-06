import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import MovieDetailResponseSchema, MovieListResponseSchema, MovieNotFoundErrorSchema


router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": MovieNotFoundErrorSchema,
            "content": {
                "application/json": {
                    "example": {"detail": "No movies found."},
                },
            },
        },
    },
)
async def get_movies(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    result = await db.execute(
        select(MovieModel).offset((page - 1) * per_page).limit(per_page).order_by(MovieModel.id)Collapse comment
    )
    movies = result.scalars().all()
    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    result = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = result.scalar_one()
    total_pages = math.ceil(total_items / per_page)

    return MovieListResponseSchema(
        movies=[MovieDetailResponseSchema.model_validate(movie) for movie in movies],
        prev_page=str(request.url.replace_query_params(page=page - 1, per_page=per_page)) if page > 1 else None,
        next_page=(
            str(request.url.replace_query_params(page=page + 1, per_page=per_page))
            if page < total_pages else None
        )
    total_pages = total_pages,
    total_items = total_items,
    )

    @router.get(
        "/movies/{movie_id}/",
        response_model=MovieDetailResponseSchema,
        responses={
            status.HTTP_404_NOT_FOUND: {
                "model": MovieNotFoundErrorSchema,
                "content": {
                    "application/json": {
                        "example": {"detail": "Movie with the given ID was not found."},
                    },
                },
            },
        },
    )
    async def get_movie(
            movie_id: int,
            db: AsyncSession = Depends(get_db),
    ) -> MovieDetailResponseSchema:
        result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
        movie = result.scalar_one_or_none()
        if movie is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie with the given ID was not found.",
            )
        return MovieDetailResponseSchema.model_validate(movie)
