import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import MovieListResponseSchema, MovieDetailResponseSchema

router = APIRouter()


async def get_num_movies(db: AsyncSession):
    num = select(func.count()).select_from(MovieModel)
    return await db.scalar(num)


# Write your code here
@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_all_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20)
):
    if page < 1 or per_page < 1:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", "page"],
                    "msg": "ensure this value is greater than or equal to 1",
                    "type": "value_error.number.not_ge"
                }
            ])
    else:
        total_items = await get_num_movies(db=db)
        total_pages = math.ceil(total_items / per_page)
        offset = (page - 1) * per_page

        movies_per_page = await db.execute(select(MovieModel).order_by(MovieModel.id).limit(per_page).offset(offset))
        movies_to_show = movies_per_page.scalars().all()

        if movies_to_show:
            prev_page = f"/api/v1/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
            next_page = f"/api/v1/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

            fields = ["id", "name", "date", "score", "genre",
                      "overview", "crew", "orig_title", "status",
                      "orig_lang", "budget", "revenue", "country"]
            result = [{field: getattr(obj, field, None) for field in fields} for obj in movies_to_show]

            return MovieListResponseSchema(
                movies=result,
                prev_page=prev_page,
                next_page=next_page,
                total_pages=total_pages,
                total_items=total_items
            )
        else:
            raise HTTPException(status_code=404, detail="No movies found.")


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if movie:
        return movie
    else:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
