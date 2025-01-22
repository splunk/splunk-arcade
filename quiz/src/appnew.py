from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import random

quiz = open('questions.json','r')
data = json.load(quiz)


app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def question_fetch(module):
  seed = random.randint(0,  len(data[module])-1)

  print(data[module][seed])
  return data[module][seed]






@app.get("/{module}/")
async def quizreturn(module) -> JSONResponse:
  return JSONResponse(content=question_fetch(module))