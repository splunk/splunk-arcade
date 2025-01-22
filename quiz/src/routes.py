from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.questions import _Questions

router = APIRouter()


@router.get("/alive")
def alive():
    return JSONResponse(content={"success": True})


@router.get("/question/{module}/")
async def get_question(module: str) -> JSONResponse:
    q = _Questions()
    return JSONResponse(content=q.random_question_for_module(module))
