import re
import textwrap
from multiprocessing.pool import ThreadPool

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from loguru import logger
from requests import HTTPError
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

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


# @st.cache_data(ttl=600)
def search_iter(q: str, ctry: str = "CA"):
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
                result["description"] = ": ".join(
                    h2.text.strip() for h2 in div.find_all("h2")
                )
                result["link"] = f"https://{site}/dp/{asin}"
                price = div.find("span", "a-price")
                if price:
                    result["price"] = float(
                        price.find("span", "a-offscreen").text.replace("$", "")
                    )

                rating = div.find(
                    "span",
                    attrs={
                        "aria-label": lambda l: l
                        and re.fullmatch(".* out of .* stars.*", l)
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
            except Exception as e:
                raise RuntimeError(f"Failed to process div: {div}") from e

        return results

    with ThreadPool() as t:
        yield from (t for l in t.imap(get_results, range(1, pages + 1)) for t in l)


@st.cache_data(ttl=60 * 60)
def search(q: str, ctry: str = "CA"):
    return pd.DataFrame(search_iter(q, ctry))


product_renderer = JsCode(
    textwrap.dedent(
        """
        class ProductRenderer {
            init(params) {
                const div = document.createElement("div");
                div.style = "display: flex; gap: 10px;";
                div.innerHTML = `
                <div style="min-width: 128px; display: flex; justify-content: center; background: white;">
                    <a href="${params.data.link}" target="_blank">
                        <img src="${params.data.img}" style="max-height: 128px; max-width: 128px"/>
                    </a>
                </div>
                <a href="${params.data.link}" target="_blank">${params.data.description}</a>`;
                this.eGui = div;
            }

            getGui() {
                return this.eGui;
            }
        }
        """
    )
)

st.set_page_config(page_title="ASearch", page_icon="static/favicon.png", layout="wide")

col1, col2 = st.columns([8, 2])

col1.markdown("# ![](/app/static/favicon_64x64.png) ASearch")
country = col2.selectbox(
    "Country",
    DOMAINS.keys(),
    label_visibility="collapsed",
    format_func={"CA": "🇨🇦 Canada", "US": "🇺🇸 United States"}.get,
)
domain = DOMAINS[country]

with st.form("form", border=False):
    col1, col2 = st.columns([9, 1])

    query = col1.text_input(
        "Search",
        label_visibility="collapsed",
        placeholder=f"Search Amazon.{domain}",
    )

    submitted = col2.form_submit_button(
        "Search", type="primary", use_container_width=True
    )
    if submitted:
        logger.info(f"Searching Amazon.{domain}: {query}")

        results = search(query, country)

        logger.debug(f"Results: {len(results)}")

        gb = GridOptionsBuilder()
        gb.configure_default_column(resizable=False, filter=True, width=100)
        gb.configure_column(
            "description",
            "Product",
            cellRenderer=product_renderer,
            wrapText=True,
            autoHeight=True,
            flex=1,
            resizable=True,
        )
        gb.configure_column(
            "price",
            "Price",
            valueFormatter=JsCode(
                """function(params) { return params.value != null ? "$" + params.value : "" }"""
            ),
        )
        gb.configure_column("rating", "Rating")
        gb.configure_column("number_of_reviews", "Reviews")
        go = gb.build()

        AgGrid(
            results,
            gridOptions=go,
            allow_unsafe_jscode=True,
            height=1000,
            enable_enterprise_modules=False,
        )
