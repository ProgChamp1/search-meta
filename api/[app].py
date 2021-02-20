import html
import json
from urllib.parse import unquote, unquote_plus
from threading import Thread
from bs4 import BeautifulSoup as bs
from flask import (
    Flask,
    Response,
    abort,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
)

from os.path import isdir

try:
    from . import apIo
except ImportError:
    import apIo
try:
    from . import scrape
except ImportError:
    import scrape

api = apIo.Api()
app = Flask(__name__)
user_agent = apIo._useragent

if not isdir("static"):
    from os.path import join

    app.static_folder = join("..", "static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    query = request.args.get("q")
    _start = request.args.get("start") or 0
    start = int(_start)
    if not query:
        return render_template("index.html")
    query = html.unescape(query)
    return render_template("search.html", query=query, start=start)


@app.after_request
def cors___(res):
    res.direct_passthrough = False
    res.headers["Access-Control-Allow-Origin"] = "https://pycode.tk"
    res.headers["Access-Control-Allow-Headers"] = "*"
    vary = res.headers.get("Vary")
    if vary:
        if "accept-encoding" not in vary.lower():
            res.headers[
                "Vary"
            ] = "{}, Access-Control-Allow-Origin,Access-Control-Allow-Headers".format(
                vary
            )
    else:
        res.headers["Vary"] = "Access-Control-Allow-Origin,Access-Control-Allow-Headers"
    return res


@app.route("/images/search/", strict_slashes=False)
def images_():
    _query = request.args.get("q")
    query = html.unescape(_query) if _query else False
    if not query:
        return render_template("images.html", query="", bing={}, google={})
    google = api.google_images(query)["data"]
    bing = api.bing_images(query)["data"]
    return render_template(
        "images.html", query=query, bing=json.dumps(bing), google=json.dumps(google)
    )


@app.route("/images/get/", strict_slashes=False)
def get_images():
    query = request.args.get("q")
    if query is None or len(query) == 0:
        return "No"
    query = html.unescape(query)
    try:
        res = make_response(scrape.api(query))
    except Exception as e:
        return str(e)
    res.headers["Content-Type"] = "application/json"
    res.headers["Access-Control-Allow-Origin"] = "*"
    return res


# @app.route("/debug/images/", strict_slashes=False)
# def deb_img():
#     return api.google_images(html.unescape(request.args.get("q")), debug=True)


@app.route("/url")
def redirect_no_referer():
    url = request.args.get("url")
    if not url:
        abort(400)
    return render_template("redirect.html", url=url)


@app.before_request
def enforce_https():
    if (
        request.endpoint in app.view_functions
        and not request.is_secure
        and not "127.0.0.1" in request.url
        and not "localhost" in request.url
        and not "192.168." in request.url
        and request.url.startswith("http://")
    ):
        rd = request.url.replace("http://", "https://")
        if "?" in rd:
            rd += "&rd=ssl"
        else:
            rd += "?rd=ssl"
        return redirect(rd, code=307)


@app.route("/search/get_results/", methods=["GET"])
def scrape_results():
    query = request.args.get("q")
    if not query:
        return redirect("/search")
    query = html.unescape(query)
    _start = request.args.get("start") or 0
    start = int(_start) if _start.isdigit() else 0
    google = api.google(query, page_start=start)
    bing = api.bing(query, page_start=start)
    res = make_response(json.dumps({"google": google, "bing": bing}))
    res.headers["Content-Type"] = "application/json"
    return res


@app.route("/search/get/<_engine>/", strict_slashes=False)
def specific_engine(_engine):
    query = request.args.get("q")
    if not query:
        return redirect("/search")
    query = html.unescape(query)
    _start = request.args.get("start") or 0
    start = int(_start) if _start.isdigit() else 0
    engine = _engine.lower()
    if not hasattr(api, engine):
        return "None"
    data = getattr(api, engine)(query, page_start=start)
    res = make_response(json.dumps({engine: data}))
    res.headers["Content-Type"] = "application/json"
    return res


if __name__ == "__main__":
    app.run(debug=True)
