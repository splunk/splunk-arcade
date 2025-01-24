from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.questions import _Questions
from src.walkthroughs import _Walkthroughs

router = APIRouter()


@router.get("/alive")
def alive():
    return JSONResponse(content={"success": True})


@router.get("/quiz/question/{module}")
async def get_question(module: str) -> JSONResponse:
    q = _Questions()
    return JSONResponse(content=q.random_question_for_module(module))


@router.get("/walkthrough/{module}/{level}")
async def get_walkthrough(module: str, stage: int) -> JSONResponse:
    w = _Walkthroughs()

    try:
        return JSONResponse(w.get_module_stage(module=module, stage=stage))
    except IndexError:
        raise HTTPException(status_code=422, detail=f"stage {stage} not present for module {module}")
