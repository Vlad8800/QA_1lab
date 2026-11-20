"""Common error envelope for the three documented API operations."""
import os
import json
from pathlib import Path
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException

CONTRACT_PATHS = {"/api/v1/shipping/policy", "/api/v1/orders/calculate", "/api/policy-gate/check"}

def configure_contract_support(app):
    """Use explicit documentation origins and normalize documented errors."""
    origins = os.getenv("DOCS_CORS_ORIGINS", "http://127.0.0.1:8001,http://localhost:8001").split(",")
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-Correlation-ID"])

    @app.get('/contract/openapi.json', include_in_schema=False)
    def published_contract():
        """Serve exactly the same contract file used by MkDocs and SDK generation."""
        contract=Path(__file__).resolve().parents[1]/'docs/api/openapi.yaml'
        return json.loads(contract.read_text(encoding='utf-8'))

    @app.get('/contract-docs', include_in_schema=False)
    def contract_docs():
        return get_swagger_ui_html(openapi_url='/contract/openapi.json',title='QA_1lab API-first contract')

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        if request.url.path in CONTRACT_PATHS:
            return JSONResponse(status_code=422, content={"code": "VALIDATION_ERROR", "detail": "Request validation failed"})
        from fastapi.exception_handlers import request_validation_exception_handler
        return await request_validation_exception_handler(request, exc)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        if request.url.path in CONTRACT_PATHS:
            return JSONResponse(status_code=exc.status_code, content={"code": "HTTP_ERROR", "detail": str(exc.detail)}, headers=exc.headers)
        from fastapi.exception_handlers import http_exception_handler
        return await http_exception_handler(request, exc)

    @app.exception_handler(Exception)
    async def internal_error(request, exc):
        return JSONResponse(status_code=500, content={"code": "INTERNAL_ERROR", "detail": "Internal server error"})
