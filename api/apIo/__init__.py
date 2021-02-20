"""
Creates Simple APIs For some major websites
that make scraping easy,request a website or create a pull request at
https://github.com/hydrophobefireman/apIo/ 

Goal:support youtube,google,bing,duckduckgo,wikipedia and reddit(read data only)
Example:
Get google searches:
>>> from apIo import Api
>>> api=Api()
>>> extractor = api.google
>>> query="Python"
>>> data=extractor(query) #The data will be returned in a dict
>>> data[0]['link']
https://www.python.org
>>> data[0]['heading']
The Home of Python
"""
import requests
from bs4 import BeautifulSoup as bs
import json
import re
from urllib.parse import quote_plus, urlencode, urlparse
import html
from warnings import warn

_useragent = "Mozilla/5.0 (Windows; U; Windows NT 10.0; en-US) AppleWebKit/604.1.38 (KHTML, like Gecko) Chrome/68.0.3325.162"
basic_headers = {
    "Accept-Encoding": "gzip,deflate",
    "User-Agent": _useragent,
    "Upgrade-Insecure-Requests": "1",
    "dnt": "1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
}


class ExtractorError(BaseException):
    pass


def _onlyId(soup):
    return list(
        filter(
            lambda x: "refinements" not in x.lower(),
            map(
                lambda x: x.attrs.get("data-id"),
                soup.find_all("div", attrs={"data-id": True}),
            ),
        )
    )


json_data_reg = r"AF_initDataCallback\({.*?data:(\[.+\])(?=.?(}\);|,\s?sideChannel))"


def search_regex(x):
    s = x.string
    if not s:
        return
    ret = re.search(json_data_reg, x.string, re.DOTALL)
    x = json.loads(ret.groups()[0]) if ret else None
    # print(x)
    return x


class Api(object):
    """main class for all searches"""

    def google(self, query, pages=1, page_start=0):
        """Google Text based search currently an average search gives
        out 7-8 links per page so it is recommended to set pages=2"""
        if pages >= 100 or page_start >= 1000:
            raise ValueError(
                "Google does not show more than (usually)900 responses for a query"
            )
        start = 0
        _urls = []
        if not page_start:
            for j in range(pages):
                i = j + 1
                if i == 1:
                    google_base = (
                        "https://www.google.com/search?q={q}&oq={q}&ie=UTF-8".format(
                            q=quote_plus(query)
                        )
                    )
                else:
                    start += 10
                    google_base = "https://www.google.com/search?q={q}&oq={q}&ie=UTF-8&start={start}".format(
                        q=quote_plus(query), start=start
                    )
                _urls.append(google_base)
        else:
            google_base = "https://www.google.com/search?q={q}&oq={q}&ie=UTF-8&start={start}".format(
                q=quote_plus(query), start=page_start
            )
            _urls.append(google_base)
        results = {}
        results["query"] = query
        results["urls"] = _urls
        results["data"] = []
        sess = requests.Session()
        for url in _urls:
            page = sess.get(url, headers=basic_headers)
            _results_class = "tF2Cxc"
            _webcache_class = "fl"
            _description_class = "aCOpRe"
            soup = bs(page.text, "html.parser")
            _results = soup.find_all(attrs={"class": _results_class})
            for res in _results:
                _link = res.findChild("a", attrs={"href": True, "data-ved": True})
                if _link is None:
                    _link = res.findChild("cite")
                    if _link is None:
                        continue
                    link = _link.text
                    heading = link
                else:
                    link = _link.attrs.get("href")
                    heading = _link.find("h3").text
                _cached = res.findChildren("a", attrs={"class": _webcache_class})
                cached = [
                    s.attrs["href"]
                    for s in _cached
                    if "webcache" in str(s.attrs.get("href"))
                ]
                cached = cached[0] if cached else None
                _text = res.findChild(attrs={"class": _description_class})
                if _text is None:
                    text = res.text.replace(link, "").replace("Cached", "")
                else:
                    text = _text.text
                text = text.replace("\xa0", " ")
                results["data"].append(
                    {"link": link, "heading": heading, "cached": cached, "text": text}
                )
        if len(results["data"]):
            return results
        raise ExtractorError("No Links Found")

    def bing(self, query, pages=1, page_start=0):
        """
        Bing Search Results
        """
        results = {}
        results["query"] = query
        start = 0
        _urls = []
        if not page_start:
            for j in range(pages):
                i = j + 1
                if i == 1:
                    bing_base = "https://www.bing.com/search?q={q}".format(
                        q=quote_plus(query)
                    )
                else:
                    start += 10
                    bing_base = (
                        "https://www.bing.com/search?q={q}&first={start}".format(
                            q=quote_plus(query), start=start
                        )
                    )
                _urls.append(bing_base)
        else:
            bing_base = "https://www.bing.com/search?q={q}&first={start}".format(
                q=quote_plus(query), start=page_start
            )
            _urls.append(bing_base)
        results["urls"] = _urls
        results["data"] = []
        _results_class = "b_algo"
        _caption_class = "b_caption"
        sess = requests.Session()
        cache_template = "http://cc.bingj.com/cache.aspx?q={query}&d={d}&mkt=nl-NL&setlang=en-GB&w={w}"
        for url in _urls:
            page = sess.get(url, headers=basic_headers)
            soup = bs(page.text, "html.parser")
            _results = soup.find_all(attrs={"class": _results_class})
            for res in _results:
                _cached = res.findChild(
                    attrs={"class": "b_attribution b_nav"}
                ) or res.findChild(attrs={"class": "b_attribution"})
                _cachedata = _cached.attrs.get("u") if _cached else None
                if _cachedata:
                    caches_d, caches_w = (
                        _cachedata.split("|")[-2],
                        _cachedata.split("|")[-1],
                    )
                    cached = cache_template.format(
                        query=quote_plus(query), d=caches_d, w=caches_w
                    )
                else:
                    cached = None
                _link = (
                    res.findChild("a")
                    if res.findChild("a").parent.name[0] == "h"
                    else None
                )
                if _link is None:
                    _link = res.findChild("cite")
                    if _link is None:
                        raise ExtractorError(
                            "No Links Found on page 1 of search results"
                        )
                    link = _link.text
                    heading = link
                else:
                    link = _link.attrs.get("href")
                    heading = _link.text
                _caption = res.findChild(attrs={"class": _caption_class})
                text = (
                    _caption.findChild("p").string
                    if _caption and _caption.findChild("p")
                    else None
                )
                text = text if text else None
                results["data"].append(
                    {"link": link, "heading": heading, "cached": cached, "text": text}
                )
        return results

    def bing_images(self, query, adult=True):
        bing_base_adlt_url = "https://bing.com/settings.aspx?pref_sbmt=1&adlt_set=off&adlt_confirm=1&is_child=0&"
        data, _urls = [], []
        results = {}
        results["query"] = query
        sess = requests.Session()
        url = "https://bing.com/images/search?q={q}".format(q=quote_plus(query))
        page = sess.get(url, headers=basic_headers, allow_redirects=True)
        soup = bs(page.text, "html.parser")
        if adult:
            _ru = soup.find(attrs={"id": "ru"})
            _guid = soup.find(attrs={"id": "GUID"})
            if _ru is None or _guid is None:
                raise Exception("Could Not verify age")
            ru = _ru.attrs.get("value")
            guid = _guid.attrs.get("value")
            new_url = bing_base_adlt_url + urlencode({"ru": ru, "GUID": guid})
            req = sess.get(new_url, headers=basic_headers, allow_redirects=True)
            if "/images/" not in req.url:
                raise Exception("Could not Find Images")
            soup = bs(req.text, "html.parser")
        atags = soup.find_all(attrs={"class": "iusc"}) or soup.find_all(
            attrs={"m": True}
        )
        for tag in atags:
            m = tag.attrs.get("m")
            if m:
                js_data = json.loads(html.unescape(m))
                if not js_data.get("murl"):
                    continue
                img = js_data["murl"]
                link = js_data.get("purl")
                fallback = js_data.get("turl")
                title = link
                if img not in str(data):
                    data.append(
                        {"img": img, "link": link, "title": title, "fallback": fallback}
                    )
        results["data"] = data
        return results

    def google_images(self, query, pages=1, page_start=0, debug=False):
        """
        Google Image Searches,on average one page returns 100 results
        It also returns a fallback useful when the original image link dies
        """
        if pages * 100 >= 900 or page_start >= 1000:
            raise ValueError(
                "Google does not show more than (usually)900 responses for a query"
            )
        data, _urls, start = [], [], 0
        results = {}
        results["query"] = query
        sess = requests.Session()
        if not page_start:
            for j in range(pages):
                i = j + 1
                if i == 1:
                    google_base = "https://www.google.com/search?q={q}&oq={q}&ie=UTF-8&tbm=isch".format(
                        q=quote_plus(query)
                    )
                else:
                    start += 100
                    google_base = "https://www.google.com/search?q={q}&oq={q}&ie=UTF-8&start={start}&tbm=isch".format(
                        q=quote_plus(query), start=start
                    )
                _urls.append(google_base)
        else:
            google_base = "https://www.google.com/search?q={q}&oq={q}&ie=UTF-8&start={start}&tbm=isch".format(
                q=quote_plus(query), start=page_start
            )
            _urls.append(google_base)
        results["urls"] = _urls
        for url in _urls:
            page = sess.get(url, headers=basic_headers, allow_redirects=True)
            txt = page.text
            if debug:
                return txt
            soup = bs(txt, "html.parser")
            reg = r"""(?<=_defd\('defd).*?(?='\);)"""
            additional_defs = bs(
                "\n".join(
                    list(
                        map(
                            lambda x: x.split("'")[-1]
                            .encode()
                            .decode("unicode_escape")
                            .replace("\\", ""),
                            re.findall(reg, txt),
                        )
                    )
                ),
                "html.parser",
            )

            required_ids = [*_onlyId(soup)[1:], *_onlyId(additional_defs)]
            try:
                json_data = list(
                    filter(bool, (search_regex(x) for x in soup.find_all("script")))
                )[-1][31][0][12][2]
                # yeah....
                for element in map(lambda x: x[1], json_data):
                    if not element:
                        continue
                    if element[1] in required_ids:
                        try:
                            data.append(
                                {
                                    "fallback": element[2][0],
                                    "img": element[3][0],
                                    "title": element[9]["2003"][3],
                                    "link": element[9]["2003"][2],
                                }
                            )
                        except:
                            continue
            except Exception as e:
                data = [{"error": str(e)}]
                pass
        results["data"] = data
        return results

    def youtube_channel(self, channel_url):
        """Gets videos of a channel..currently only page 1 support has been added..
        page 2 support will be added very soon"""
        parsed_url = urlparse(channel_url)
        results = {}
        results["channel_url"] = channel_url
        results["videos"] = []
        path = parsed_url.path
        req = channel_url
        if "/videos" not in path:
            req = channel_url + "/videos/"
        req = channel_url
        htm = requests.get(req, headers=basic_headers).text
        reg = json.loads(
            re.search(
                r"(?s)ytInitialData\"\]\s=\s(?P<id>{.*?});", htm, re.IGNORECASE
            ).group("id")
        )
        contents = reg["contents"]["twoColumnBrowseResultsRenderer"]
        _videos = contents["tabs"]  # list
        for _tab in _videos:
            renderer = _tab.get("tabRenderer")
            if not renderer:
                continue
            if renderer["title"] != "Videos":
                continue
            vid_content = renderer["content"]["sectionListRenderer"]["contents"][0][
                "itemSectionRenderer"
            ]["contents"][0]["gridRenderer"]["items"]
            for _vid in vid_content:
                renderer = _vid["gridVideoRenderer"]
                _vid = renderer["videoId"]
                _url = "https://www.youtube.com/watch?v=" + _vid
                _thumbnail = "https://i.ytimg.com/vi/" + _vid + "/hqdefault.jpg"
                _title = renderer["title"]["simpleText"]
                _publish_time = renderer["publishedTimeText"]["simpleText"]
                _view_count = renderer["viewCountText"]["simpleText"]
                _video_length = renderer["thumbnailOverlays"][0][
                    "thumbnailOverlayTimeStatusRenderer"
                ]["text"]["simpleText"]
                results["videos"].append(
                    {
                        "url": _url,
                        "thumbnail": _thumbnail,
                        "title": _title,
                        "publish_time": _publish_time,
                        "view_count": _view_count,
                        "video_length": _video_length,
                    }
                )
        return results

    def youtube(self, query=None, trending=False):
        """Youtube search results and trending results multiple pages not suported as of now"""
        if not query and not trending:
            raise RuntimeError(
                "No Value provided..please specify query or set trending=True"
            )
        if query and trending:
            warn("Both query and trending have been specified..defaulting to query")
            trending = False
        if query:
            req = "https://youtube.com/results?search_query=" + quote_plus(query)
        else:
            req = "https://youtube.com/feed/trending/"
        htm = requests.get(req, headers=basic_headers).text
        reg = json.loads(
            re.search(
                r"(?s)ytInitialData\"\]\s=\s(?P<id>{.*?});", htm, re.IGNORECASE
            ).group("id")
        )
        json_data = {}
        json_data["data"] = []
        videos = []
        if not trending:
            contents = reg["contents"]["twoColumnSearchResultsRenderer"][
                "primaryContents"
            ]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]
            for opt in contents:
                if opt.get("videoRenderer"):
                    videos.append(opt)
        else:
            temp_ = []
            data = reg["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0][
                "tabRenderer"
            ]["content"]["sectionListRenderer"]["contents"]
            for part in data:
                key = list(
                    part["itemSectionRenderer"]["contents"][0]["shelfRenderer"][
                        "content"
                    ]
                )[0]
                temp_ = [
                    s
                    for s in part["itemSectionRenderer"]["contents"][0][
                        "shelfRenderer"
                    ]["content"][key]["items"]
                ]
                videos += temp_
        for vid in videos:
            vid_keys = list(vid.keys())[0]
            videoId = vid[vid_keys]["videoId"]
            thumb = "https://i.ytimg.com/vi/%s/hqdefault.jpg" % (videoId)
            title = (
                vid[vid_keys]["title"]["simpleText"].replace("'", "").replace('"', "")
            )
            channel_name = vid[vid_keys]["shortBylineText"]["runs"][0]["text"]
            _description = vid[vid_keys].get("descriptionSnippet")
            if _description:
                description = _description.get("simpleText")
            else:
                try:
                    description = (
                        vid[vid_keys]["descriptionSnippet"]["runs"][0]["text"]
                        + " "
                        + vid[vid_keys]["descriptionSnippet"]["runs"][1]["text"]
                    )
                except:
                    description = None
            try:
                publish_time = vid[vid_keys]["publishedTimeText"]["simpleText"]
                video_length = vid[vid_keys]["lengthText"]["simpleText"]
                view_count = vid[vid_keys]["viewCountText"]["simpleText"]
            except:
                publish_time = "NA"
                video_length = "NA"
                view_count = "NA"
            try:
                channel_thumbnail = vid[vid_keys]["channelThumbnail"]["thumbnails"][0][
                    "url"
                ]
            except:
                continue
            channel_url = (
                "https://youtube.com"
                + vid[vid_keys]["shortBylineText"]["runs"][0]["navigationEndpoint"][
                    "commandMetadata"
                ]["webCommandMetadata"]["url"]
            )
            try:
                preview = vid[vid_keys]["richThumbnail"]["movingThumbnailRenderer"][
                    "movingThumbnailDetails"
                ]["thumbnails"][0]["url"]
            except:
                preview = None
            video_url = "https://youtu.be/%s" % (videoId)
            json_data["query"] = query
            json_data["trending"] = trending
            json_data["data"].append(
                {
                    "url": video_url,
                    "thumb": thumb,
                    "title": title,
                    "description_snippet": description,
                    "publish_time": publish_time,
                    "video_length": video_length,
                    "view_count": view_count,
                    "channel_thumbnail": channel_thumbnail,
                    "channel": channel_name,
                    "channel_url": channel_url,
                    "preview": preview,
                }
            )
        return json_data
