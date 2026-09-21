import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware
from kyc_agent import MAX_BYTES, validate_image
from offline import extract_offline, BINARY

ROOT = Path(__file__).parent
app = FastAPI(title='Agent Akshaya', docs_url=None, redoc_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', 'testserver'])

@app.middleware('http')
async def headers(request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' blob:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    return response

@app.get('/')
def index():
    return FileResponse(ROOT / 'static/index.html')

@app.get('/static/{name}')
def asset(name: str):
    if name not in ('app.js', 'styles.css', 'sample-document.png'):
        raise HTTPException(404)
    return FileResponse(ROOT / 'static' / name)

@app.get('/api/status')
def status():
    return {'configured': BINARY.is_file(), 'engine': 'offline'}

@app.post('/api/extract')
async def extract(request: Request):
    if request.headers.get('x-consent') != 'process-locally':
        raise HTTPException(400, 'Confirm permission to process the image locally.')
    if request.headers.get('content-type', '').split(';')[0] not in ('image/jpeg', 'image/png', 'image/webp'):
        raise HTTPException(415, 'Choose a JPEG, PNG, or WebP image.')
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > MAX_BYTES:
            raise HTTPException(413, 'Choose an image smaller than 10 MB.')
    try:
        validate_image(bytes(data))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    if not BINARY.is_file():
        raise HTTPException(503, 'Offline OCR is not built. Follow the native build step in README.md.')
    try:
        result = await run_in_threadpool(extract_offline, bytes(data))
        return result
    except Exception:
        return JSONResponse({'detail': 'The local OCR engine could not process this image. The sample test also fails in this environment; extraction is not yet operational.'}, status_code=502)
