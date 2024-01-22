import re
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from loguru import logger
from requests import HTTPError

MAX_PAGES = 50

DOMAINS = {"CA": "ca", "US": "com"}


def __response_hook(r, *args, **kwargs):
    try:
        r.raise_for_status()
    except HTTPError as e:
        # raise ValueError(r.text) from e
        raise ValueError(BeautifulSoup(r.text).text) from e


session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/111.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}
session.hooks = {"response": __response_hook}


# @retry(stop_after_attempt(5), wait=wait_random(min=1, max=2))
def get(url, **kwargs):
    return session.get(url, headers=headers, **kwargs)


app = FastAPI()


@app.get("/api/ping")
def ping():
    return {"pong": True}


@app.get("/api/search")
@cache(expire=600)
def search(q: str, ctry: str = "CA"):
    domain = DOMAINS[ctry]
    site = f"amazon.{domain}"
    url = f"https://{site}/s?k={q}"

    soup = BeautifulSoup(get(url).content, "html.parser")
    pages = int(soup.find_all("span", "s-pagination-item")[-1].text)

    if pages > MAX_PAGES:
        pages = MAX_PAGES

    def get_results(page: int):
        soup = BeautifulSoup(get(url, params={"page": page}).content, "html.parser")
        divs = soup.find_all("div", attrs={"data-component-type": "s-search-result"})

        if not divs:
            logger.error(f"No results found  in HTML: {soup}")
            return

        results = []
        for div in divs:
            try:
                result = {}
                asin = div["data-asin"]
                result["asin"] = asin
                result["img"] = div.find("img", "s-image")["src"]
                result["description"] = [h2.text.strip() for h2 in div.find_all("h2")]
                result["link"] = f"https://{site}/dp/{asin}"
                price = div.find("span", "a-price")
                if price:
                    result["price"] = price.find("span", "a-offscreen").text

                rating = div.find(
                    "span",
                    attrs={
                        "aria-label": lambda l: l
                        and re.fullmatch(".* out of .* stars", l)
                    },
                )
                if rating:
                    result["rating"] = float(rating["aria-label"].split(" ")[0])
                number_of_reviews = div.find(
                    "a", href=lambda h: h.endswith("#customerReviews")
                )
                if number_of_reviews:
                    result["number_of_reviews"] = int(
                        number_of_reviews.text.strip()
                        .replace(",", "")
                        .replace("(", "")
                        .replace(")", "")
                    )

                yield result
                # results.append(result)
            except Exception as e:
                raise RuntimeError(f"Failed to process div: {div}") from e

        return results

    with ThreadPoolExecutor() as t:
        return [t for l in t.map(get_results, range(1, pages + 1)) for t in l]


app.mount("/", StaticFiles(directory="dist", html=True), name="static")


@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend())
