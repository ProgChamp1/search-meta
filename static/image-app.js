(() => {
  if (typeof self === "undefined") {
    var self = window;
  }
  const { h, render, useState, useCallback, useEffect, useRef } = self.uiLib;

  const _ls = localStorage.getItem("data-config");

  const prefs = _ls ? JSON.parse(_ls) : { saveData: false, slideShow: false };

  const root = document.getElementById("root");

  const { bing: bingData, google: googleData, query } = self._initialData;

  let observer;
  const listenerMap = new WeakMap();
  let createObserver = function () {
    if (!observer) {
      observer = new IntersectionObserver((e) => {
        e.forEach((entry) => {
          const fn = listenerMap.get(entry.target);
          fn && fn(entry.isIntersecting);
        });
      });
      createObserver = function () {};
    }
  };
  function LazyImage(props) {
    createObserver();
    const [intersecting, setIntersecting] = useState(false);
    const [shouldLoad, setLoad] = useState(false);
    const imgRef = useRef();
    const $src = useRef(props.src);
    useEffect(() => {
      const oldSrc = $src.current;
      const currSrc = props.src;
      if (!intersecting && oldSrc != currSrc) {
        setLoad(false);
      }
      $src.current = currSrc;
    }, [props.src, intersecting]);
    useEffect(() => {
      const current = imgRef.current;
      if (current) {
        observer.observe(current);
        const listener = (value) => {
          setIntersecting(value);
          setLoad((prev) => value || prev);
        };
        listenerMap.set(current, listener);
      }
      return () => listenerMap.delete(current);
    }, [imgRef.current]);
    const { src, ...rest } = props;
    return h(
      "img",
      Object.assign({}, rest, { src: shouldLoad ? src : null, ref: imgRef })
    );
  }

  function updateLocalstorage(key, val) {
    prefs[key] = val;
    localStorage.setItem("data-config", JSON.stringify(prefs));
  }

  const App = () => {
    const [slideShow, setSlideShow] = useState(prefs.slideShow);
    const [saveData, setSaveData] = useState(prefs.saveData);

    return h(
      "div",
      { class: "image-root" },
      h(
        "form",
        { action: "/images/search/" },
        h("input", {
          class: "paper-input",
          placeholder: "Search",
          name: "q",
          value: query || null,
        }),
        h("button", { class: "sbm-btn" }, "Search")
      ),
      h(
        "div",
        { style: "display:flex" },
        h(
          "button",
          {
            class: "pref-button",
            onClick: () => {
              updateLocalstorage("saveData", !saveData);
              setSaveData(!saveData);
            },
          },
          "Data Saver is ",
          saveData ? "On" : "Off"
        ),
        h(
          "button",
          {
            class: "pref-button",
            onClick: () => {
              updateLocalstorage("slideShow", !slideShow);
              setSlideShow(!slideShow);
            },
          },
          "Slide show is ",
          slideShow ? "On" : "Off"
        )
      ),
      query
        ? [
            h("div", null, "Search Results For: ", query),
            h(ImageViewer, {
              bingData,
              googleData,
              saveData,
              slideShow,
              setSlideShow: (value) => {
                updateLocalstorage("slideShow", value);
                setSlideShow(value);
              },
            }),
          ]
        : h("div", null, "Enter your search above")
    );
  };

  function ImageViewer(props) {
    const slideShow = props.slideShow;
    const saveData = props.saveData;
    const [index, setIndex] = useState(0);

    const startSlideShow = useCallback((e) => {
      const isGoogleImage = +e.target.dataset.group === 1;
      const offset = isGoogleImage ? bingData.length : 0;
      const idx = +e.target.dataset.idx + offset;
      setIndex(idx);

      props.setSlideShow(!slideShow);
    });

    if (slideShow) {
      const allImages = bingData.concat(googleData);
      return h(SlideShow, {
        saveData,
        images: allImages,
        index,
        closeSlideShow: () => {
          setIndex(0);
          props.setSlideShow(false);
        },
      });
    }

    const data = { bing: bingData, google: googleData };
    return h(
      "div",
      { class: "image-view" },
      ["bing", "google"].map((x, i) =>
        h(
          "div",
          null,
          h("div", { style: { "font-weight": "bold" } }, `${x} Images`),
          h(
            "div",
            { class: "image-store" },
            h(ImageGrid, { imgs: data[x], saveData, startSlideShow, group: i })
          )
        )
      )
    );
  }
  function ImageGrid(props) {
    const { saveData, imgs, startSlideShow, group } = props;

    const onClick = startSlideShow;

    return imgs.map((x, i) =>
      h(Image$, {
        saveData,
        onClick,
        "data-idx": i,
        "data-group": group,
        ...x,
      })
    );
  }
  function Image$(props) {
    const { img, link, fallback, saveData, ...rest } = props;

    const init = () => (saveData ? fallback : img);
    const [src, setSrc] = useState(init);

    useEffect(() => setSrc(init), [saveData, img, fallback]);

    const onError = useCallback(() => {
      if (src === img) {
        setSrc(fallback);
      }
    }, [src]);

    return h("img", {
      loading: "lazy",
      class: "grid-image hoverable",
      src,
      onError,
      ...rest,
    });
  }

  function SlideShow(props) {
    const { images, index: receivedIndex, closeSlideShow } = props;
    const [index, setIndex] = useState(receivedIndex);
    const [showLinkAndTitle, setShowLinkAndTitle] = useState(true);
    const imageLen = images.length;
    useEffect(() => index != receivedIndex && setIndex(receivedIndex), [
      receivedIndex,
    ]);

    const onClick = (e) => {
      const clickTarget = e.target;
      const clickTargetWidth = clickTarget.offsetWidth;
      const xCoordInClickTarget =
        e.clientX - clickTarget.getBoundingClientRect().left;
      let newIndex;
      if (clickTargetWidth / 2 > xCoordInClickTarget) {
        newIndex = index - 1;
        if (newIndex < 0) newIndex = 0;
      } else {
        newIndex = index + 1;
        if (newIndex >= imageLen) {
          newIndex = 0;
        }
      }
      setIndex(newIndex);
    };
    const data = images[index];

    return h(
      "div",
      { class: "img-slideshow-box" },

      h(
        "div",
        { class: "title-link-ss" },
        h(
          "a",
          {
            target: "_blank",
            href: data.link,
            class: `link-title-top${showLinkAndTitle ? "" : " hide"}`,
          },
          data.title
        ),
        h("div", {
          class: `action-button back-button${
            showLinkAndTitle ? "" : " rotate"
          }`,
          onClick: () => setShowLinkAndTitle(!showLinkAndTitle),
        })
      ),
      h(
        "div",
        {
          class: "title-link-ss",
          style: { left: "unset", right: 0, padding: 0 },
        },
        h("div", {
          class: "action-button close-button",
          style: { margin: 0 },
          onClick: closeSlideShow,
        })
      ),
      h(Image$, {
        ...data,
        class: "slideshow-image",
        saveData: props.saveData,
        onClick: onClick,
      })
    );
  }
  render(h(App), root);
})();
