// Set by default value of server
const full = location.host;
$('#txtServer').val(full)
$('#selScheme').val(location.protocol.split(':'));

async function fetchInput() {
    let scheme = $('#selScheme').val()
    let server = $('#txtServer').val()
    let prefix = $('#selPrefix').val()
    let identifier = $('#txtIdentifier').val()
    let version = $('#txtVersion').val()
    let info = $('#selInfo').val()

    let url = `${scheme}://${server}/${prefix}/${identifier}/${version}/${info}.json`
    $('#divActualAPIURL').html(`<pre
    class="m-0">Requested URL: <code>${url}</code></pre>`)

    let resp = await callAPI(url)
    if (!resp.toLowerCase().includes('error')) {
        //let jsonData = JSON.parse(resp);
        // initialize
        //var editor = new JsonEditor('#json-display', resp);

        //$('.textarea').val(resp)
        var input = eval('(' + resp + ')');
        $('#json-display').json_viewer(input)
    }
    else {
        $('.textarea').val('')
    }
}

async function callAPI(url) {
    let response = await fetch(url);
    let data = await response.text()
    return data;
}

function process(str) {
    var div = document.createElement('div');
    div.innerHTML = str.trim();
    return format(div, 0).innerHTML;
}

function format(node, level) {
    var indentBefore = new Array(level++ + 1).join('  '),
        indentAfter = new Array(level - 1).join('  '),
        textNode;

    for (var i = 0; i < node.children.length; i++) {

        textNode = document.createTextNode('\n' + indentBefore);
        node.insertBefore(textNode, node.children[i]);

        format(node.children[i], level);

        if (node.lastElementChild == node.children[i]) {
            textNode = document.createTextNode('\n' + indentAfter);
            node.appendChild(textNode);
        }
    }

    return node;
}

$('input[type="text"], select').on('input', e => {
    fetchInput();
})

fetchInput()
