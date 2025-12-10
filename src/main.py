from re import S
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
from typing import Callable

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class LinkRequest(BaseModel):
    links: str
    methods: List[str]


class MethodResult(BaseModel):
    method_name: str
    result: str


class LinkResponse(BaseModel):
    success: bool
    message: str
    results: List[MethodResult]


class MethodInfo(BaseModel):
    id: str
    name: str


class MethodsResponse(BaseModel):
    methods: List[MethodInfo]


class Method:
    def __init__(self, name: str, function: Callable):
        self.name = name
        self.function = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


class Validate:
    def __init__(self) -> None:
        pass

    @classmethod
    def validate_string(cls, string):
        # TODO: валидация строки(url, дописать мб стоит с помощью регулярок)
        if string == "":
            return False
        return True

    def __call__(self, string):
        return self.validate_string(string)


METHODS = [
    Method("reverse", lambda s: s[::-1]),
    Method("uppercase", lambda s: s.upper()),
    Method("lowercase", lambda s: s.lower()),
    Method("remove_spaces", lambda s: s.replace(" ", "")),
    Method("capitalize", lambda s: s.capitalize()),
]
METHODS_DICT = {method.name: method for method in METHODS}

validate = Validate()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/methods", response_model=MethodsResponse)
async def get_methods():
    methods = [
        MethodInfo(id=method.name, name=method.name) 
        for method in METHODS
    ]
    return MethodsResponse(methods=methods)


@app.post("/api/process-links", response_model=LinkResponse)
async def process_links(request: LinkRequest):
    input_link = request.links.strip()
    if not validate(input_link):
        return LinkResponse(
            success=False, message="Ссылка не предоставлена", results=[]
        )

    if not request.methods:
        return LinkResponse(success=False, message="Методы не выбраны", results=[])

    results = []
    for method in request.methods:
        if method in METHODS_DICT:
            try:
                obj = METHODS_DICT[method]
                processed_result = obj(input_link)
                results.append(
                    MethodResult(
                        method_name=obj.name,
                        result=processed_result,
                    )
                )
            except Exception as e:
                results.append(
                    MethodResult(
                        method_name=obj.name,
                        result=f"Ошибка: {str(e)}",
                    )
                )

    return LinkResponse(
        success=True, message=f"Обработано методов: {len(results)}", results=results
    )
