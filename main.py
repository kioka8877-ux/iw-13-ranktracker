"""
IW-13 RankTracker — Position Tracking dans le temps
Iron Warrior #13 — SEO monitoring, historique.
Attaque : SERP Results ($20/10K)
"""
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import sys
sys.path.insert(0, '/home/user/iron_warriors/shared')
from base import create_app, fetch_html, SearchResult, clean_text, get_timestamp, measure_latency
import time

app = create_app("IW-13 RankTracker", "Position tracking SEO — historique + monitoring")

class RankEntry(BaseModel):
    query: str
    domain: str
    position: Optional[int] = None
    url: Optional[str] = None
    title: Optional[str] = None
    found: bool

class RankResponse(BaseModel):
    domain: str
    results: List[RankEntry]
    timestamp: str
    latency_ms: int

@app.get("/track", response_model=RankResponse)
async def track_rank(
    domain: str = Query(..., description="Domain to track (e.g. example.com)"),
    keywords: str = Query(..., description="Comma-separated keywords to track"),
    gl: str = Query("us"),
    hl: str = Query("en"),
):
    start = time.time()
    kw_list = [k.strip() for k in keywords.split(",")]
    results = []

    for kw in kw_list:
        url = f"https://www.google.com/search?q={quote_plus(kw)}&num=100&gl={gl}&hl={hl}"
        try:
            html = await fetch_html(url)
        except:
            results.append(RankEntry(query=kw, domain=domain, found=False))
            continue

        soup = BeautifulSoup(html, 'html.parser')
        found_pos = None
        found_url = None
        found_title = None
        pos = 0

        for div in soup.find_all('div', class_='g'):
            h3 = div.find('h3')
            link = div.find('a', href=True)
            if h3 and link:
                href = link['href']
                if href.startswith('/url?q='):
                    href = href.split('/url?q=')[1].split('&')[0]
                if not href.startswith('http'):
                    continue
                pos += 1
                if domain in href:
                    found_pos = pos
                    found_url = href
                    found_title = clean_text(h3.get_text())
                    break

        results.append(RankEntry(
            query=kw, domain=domain,
            position=found_pos, url=found_url, title=found_title,
            found=found_pos is not None,
        ))

    return RankResponse(
        domain=domain, results=results,
        timestamp=get_timestamp(), latency_ms=measure_latency(start),
    )
