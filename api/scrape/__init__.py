import html
import json
from urllib.parse import quote, urlencode, quote_plus

import requests
from bs4 import BeautifulSoup as bs

BASEURL_GOOGLE = "https://www.google.com/search?q={query}&tbm=isch"
BASEURL_BING = "https://bing.com/images/search?q={query}"
basic_headers = {
    "Accept-Encoding": "gzip,deflate",
    "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 10.0; en-US) AppleWebKit/604.1.38 (KHTML, like Gecko) Chrome/68.0.3325.162",
    "Upgrade-Insecure-Requests": "1",
    "dnt": "1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
}
sess = requests.Session()


def get_data_bing(url, adl=False):
    bing_base_adlt_url = "https://bing.com/settings.aspx?pref_sbmt=1&adlt_set=off&adlt_confirm=1&is_child=0&"
    # print("[Bing]Fetching:", url)
    page = sess.get(url, headers=basic_headers, allow_redirects=True)
    cookies = dict(page.cookies)
    data = []
    soup = bs(page.text, "html.parser")
    if adl:
        _ru = soup.find(attrs={"id": "ru"})
        _guid = soup.find(attrs={"id": "GUID"})
        # print(page.url)
        if _ru is None or _guid is None:
            raise Exception("Could Not verify age")
        ru = _ru.attrs.get("value")
        guid = _guid.attrs.get("value")
        new_url = bing_base_adlt_url + urlencode({"ru": ru, "GUID": guid})
        req = sess.get(
            new_url, headers=basic_headers, cookies=cookies, allow_redirects=True
        )
        if "/images/" not in req.url:
            raise Exception("Could not Find Images")
        soup = bs(req.text, "html.parser")
        # print("[Bing]Age-Verified")
    atags = soup.find_all(attrs={"class": "iusc"}) or soup.find_all(attrs={"m": True})
    for tag in atags:
        m = tag.attrs.get("m")
        if m:
            js_data = json.loads(html.unescape(m))
            img = js_data["murl"]
            link = js_data["purl"]
            fallback = js_data.get("turl")
            title = link
            # print("[Bing]Found", img)
            if img not in str(data):
                data.append(
                    {"img": img, "link": link, "title": title, "fallback": fallback}
                )
    return data


def api(query):
    query = quote_plus(query)
    bing = get_data_bing(BASEURL_BING.format(query=query), adl=True)
    google = get_data_google(BASEURL_GOOGLE.format(query=query))
    json_data = {"bing": bing, "google": google}
    return json.dumps(json_data)


def get_data_google(url):
    data = []
    # print("[Google]Fetching URL")
    page = sess.get(url, headers=basic_headers, allow_redirects=True)
    page.raise_for_status
    soup = bs(page.text, "html.parser")
    divs = soup.find_all("div", attrs={"class": "rg_meta notranslate"})
    for div in divs:
        meta = json.loads(div.text)
        img = meta.get("ou")
        title = meta.get("pt") or meta.get("s")
        link = meta.get("ru")
        fallback = meta.get("tu")
        if img:
            # print("[Google]Found:", img)
            if img not in str(data):
                data.append(
                    {"img": img, "link": link, "title": title, "fallback": fallback}
                )

    return data


if __name__ == "__main__":
    query = input("Enter Query:")
    safe = input("Remove safe(Bing)?(y/n):").lower()
    if safe == "y":
        adl = True
    else:
        # print("safe set to false")
        adl = False
    get_data_bing(BASEURL_BING.format(query=query), adl=adl)
    get_data_google(BASEURL_GOOGLE.format(query=query))
