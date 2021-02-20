const submit = document.getElementById("btn_s");
const input = document.getElementById("search");
const search_ghost = document.getElementById("search-ghost");
input.onclick = ({
    target
}) => {
    target.placeholder = '';
    search_ghost.style.visibility = 'visible';
}
document.body.onclick = ({
    target
}) => {
    if (input.value.length == 0 && target !== submit && target !== input) {
        input.placeholder = 'Search';
        search_ghost.style.visibility = 'hidden';
    }
}


function make_image_viewer(link, caption, src) {
    const text = document.createElement("div");
    const txtlink = document.createElement("a");
    txtlink.href = link;
    text.innerHTML = caption;
    txtlink.style.color = '#fff';
    text.style.color = '#fff';
    const viewer = document.getElementById("img-viewer");
    viewer.innerHTML = '';
    viewer.style.display = 'block';
    img = new Image();
    window.viewer_active = true;
    img.src = src;
    img.style.marginTop = '50px';
    img.style.height = '50%';
    txtlink.appendChild(img);
    txtlink.appendChild(text);
    viewer.appendChild(txtlink);
    const div = document.createElement("div");
    div.innerHTML = 'Close'
    div.className = 'closebtn';
    viewer.appendChild(div);
    div.onclick = () => {
        viewer.style.display = 'none';
        viewer.innerHTML = '';
    }
}