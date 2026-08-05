# Deployment — Render

## API (FastAPI)

**Service type:** Web Service  
**Runtime:** Python 3  
**Root directory:** *(must be blank — the repo root, NOT `api/`)*

> ⚠️ **Vanlig feil:** hvis Root Directory settes til `api/` feiler builden med
> *"does not appear to be a Python project: neither setup.py nor pyproject.toml found"*  
> fordi `pyproject.toml` ligger i repo-roten, og `core/`-modulen installeres
> derfra. Root Directory **må være blank**.

**Build Command:**
```
pip install -e . && pip install -r api/requirements.txt
```

**Start Command:**
```
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

`api/requirements.txt` inneholder alle API-spesifikke avhengigheter:
- `fastapi` — web framework
- `uvicorn[standard]` — ASGI server
- `python-multipart` — filopplasting (FormData)
- `pdfplumber` — PDF tekstlag-uttrekk (PDF / JPG tab i /faktura/ny)

> **Viktig:** uten `api/requirements.txt` i build-kommandoen installeres ikke `pdfplumber`,
> og alle PDF-opplastinger returnerer «no_text_layer» selv om filen har tekstlag.

## Next.js frontend (web/)

**Service type:** Web Service  
**Root directory:** `web`

**Build Command:**
```
npm ci && npm run build
```

**Start Command:**
```
npm start
```

**Environment variable:**
```
NEXT_PUBLIC_API_URL=https://<api-service>.onrender.com
```
