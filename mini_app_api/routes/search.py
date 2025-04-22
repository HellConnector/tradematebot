from fastapi import APIRouter, Depends, HTTPException

from mini_app_api.data_loader import ALL_SEARCH_ITEMS
from mini_app_api.dependencies import (
    get_web_app_init_data,
    get_client,
)
from mini_app_api.models import SearchItem

router = APIRouter(
    prefix="/api/search",
    dependencies=[Depends(get_web_app_init_data), Depends(get_client)],
)

MIN_QUERY_LENGTH = 3
MAX_QUERY_LENGTH = 100


@router.get(path="/")
async def search(query: str) -> list[SearchItem]:
    results = []
    query = query.strip().lower()
    if len(query) < MIN_QUERY_LENGTH or len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Query should be between {MIN_QUERY_LENGTH} "
                f"and {MAX_QUERY_LENGTH} characters."
            ),
        )
    words = query.split()
    for name, image_url in ALL_SEARCH_ITEMS.items():
        if all((word in name.lower()) for word in words):
            results.append(SearchItem(name=name, image_url=image_url))
    if len(results) >= 20:
        raise HTTPException(
            status_code=400,
            detail="Too many items found. Refine your request.",
        )
    results.sort(key=lambda item: item.name)
    return results


@router.get(path="/{item_name}/")
async def get_by_name(item_name: str) -> SearchItem:
    if item_name not in ALL_SEARCH_ITEMS:
        raise HTTPException(
            status_code=404, detail=f"Item [{item_name}] not found"
        )
    else:
        return SearchItem(
            name=item_name, image_url=ALL_SEARCH_ITEMS[item_name]
        )
