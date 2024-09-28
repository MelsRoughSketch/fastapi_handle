import traceback
from logging import getLogger
from typing import Callable

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarlettedHTTPException

from function import func_a, func_b, func_c

app = FastAPI()

logger = getLogger(__name__)

RESPONSE_TRACEBACK = False


@app.middleware("http")
def middleware(request: Request, call_next: Callable):
    request.state.progress_stack = []
    request.state.progress_stack.append(
        f"{request.url.path}: calling by {request.client.host}"
    )
    response = call_next(request)
    return response


@app.exception_handler(Exception)
def unhandle_exception_handler(request: Request, e: Exception):
    if isinstance(e, HTTPException):
        custum_http_exception_handler(request, e)
    response = ["!CAUTION: UNHANDLE EXCEPTIONS ARE OCCURRING!"]
    tb_list = traceback.format_exception(type(e), e, e.__traceback__)

    for tb in tb_list:
        tb = tb.strip("\n")
        if "\n" in tb:
            response.extend(tb.split("\n"))
        else:
            response.append(tb)
    logger.error("\n".join(response))

    if RESPONSE_TRACEBACK:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": response},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(e)},
    )


@app.exception_handler(StarlettedHTTPException)
def custum_http_exception_handler(request: Request, e: HTTPException):
    logger.error("\n".join(request.state.progress_stack))
    if not RESPONSE_TRACEBACK:
        e.detail = [line for line in e.detail if not line.startswith(">>")]
    return JSONResponse(status_code=e.status_code, content={"detail": e.detail})


@app.get("/ok/")
def suc(request: Request):
    func_a(1, 2, log_list=request.state.progress_stack)
    func_b(1, 2, log_list=request.state.progress_stack)
    request.state.progress_stack.append(f"{request.url.path}:execution > last_function")
    func_c(1, 2, log_list=request.state.progress_stack)
    x = 1 / 0  # unhandle exception
    return request.state.progress_stack


@app.get("/exc/")
def exc(request: Request):
    func_a(1, 2, log_list=request.state.progress_stack)
    func_b(1, 2, log_list=request.state.progress_stack)

    try:
        request.state.progress_stack.append(
            f"{request.url.path}:execution > last_function:"
        )
        func_c(1, 0, log_list=request.state.progress_stack)  # exception
    except:
        request.state.progress_stack.append(
            f"{request.url.path}: Detect execution failure. re-execute last_function:"
        )
        func_c(1, 0, log_list=request.state.progress_stack)  # exception
        raise
    return request.state.progress_stack
