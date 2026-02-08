import os
from fastapi import FastAPI, Header, HTTPException

app = FastAPI(title="Competitor Price API", version="1.0.0")


def _check_auth(authorization: str | None) -> None:
    api_key = os.getenv("COMPETITOR_API_KEY", "")
    if not api_key:
        return
    expected = f"Bearer {api_key}"
    if authorization != expected:
        raise HTTPException(status_code=403, detail="Unauthorized")


@app.get("/price")
def get_price(q: str = "", sku: str = "", authorization: str | None = Header(default=None)):
    _check_auth(authorization)
    seed = len((q + sku).strip())
    price = round(49.9 + (seed % 200), 2)
    return {
        "price_net": price,
        "currency": "EUR",
        "source": "demo",
        "query": q,
        "sku": sku,
    }
