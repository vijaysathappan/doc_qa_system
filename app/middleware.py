from fastapi import Request
from fastapi.responses import JSONResponse
async def global_exception_handler(request: Request,exc : Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error":"Internal server error",
            "message":"Something went wrong on our end",
            "path":str(request.url)
        }
    )
async def not_found_handler(request : Request, exc:Exception):
    return JSONResponse(
        status_code=404,
        content={
            "error":"Not Found",
            "message":"The resource you requested does not exist",
            "path":str(request.url)
        }
    )
