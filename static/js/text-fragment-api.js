import { franc, francAll } from 'https://esm.sh/franc@6?bundle';

// Set by default value of server
const full = location.host;
$('#txtServer').val(full);
$('#selScheme').val(location.protocol.split(':'));

async function setInputs(infoAPIURL) {
    let response = await fetch(infoAPIURL);
    let data = await response.json()
    //////////////////////////////
    // Populate mode
    // Clear select element
    $('#selMode').empty();
    $.each(data.modes, function (index, value) {
        $('#selMode').append($('<option>').text(value).attr('value', value));
    });

    //////////////////////////////
    // Populate Quality
    // Clear select element
    $('#selQuality').empty();
    $.each(data.qualities, function (index, value) {
        $('#selQuality').append($('<option>').text(value).attr('value', value));
    });

    //////////////////////////////
    // Populate Format
    // Clear select element
    $('#selFormat').empty();
    $.each(data.formats, function (index, value) {
        $('#selFormat').append($('<option>').text(value).attr('value', value));
    });

    // Set the selected attribute for the first option
    $('select option:first').attr('selected', 'selected');
}

async function fetchInput() {
    $('.textarea').val('')
    $('.textarea').addClass('loading')
    let scheme = $('#selScheme').val()
    let server = $('#txtServer').val()
    let prefix = $('#selPrefix').val()
    let identifier = $('#txtIdentifier').val()
    let version = $('#txtVersion').val()
    let fragment = $('#txtFragment').val()

    let mode = $('#selMode').val()
    let quality = $('#selQuality').val()
    let format = $('#selFormat').val()



    let print_url = `${scheme}://${server}/${prefix}/${identifier}/${version}/${mode}/${fragment}/${quality}.${format}`
    $('#divActualAPIURL').html(`<pre
    class="m-0">Requested URL: <code>${print_url}</code></pre>`)

    let url = `${scheme}://${server}/${prefix}/${identifier}/${version}/${mode}/${fragment}/${quality}.${format === 'tei' ? 'xml' : format}`
    
    let resp = await callAPI(url)
    if (!resp.toLowerCase().includes('text fragment api error') && !resp.toLocaleLowerCase().includes('typeerror: ')) {
        if (format === 'txt') {
            $('.info-counters').show()
            $('.word-density').show()
            $('.textarea').val(resp)
            applyWordDensity(resp)
        }
        else {
            $('.info-counters').hide()
            $('.word-density').hide()
            $('.textarea').val(resp);
        }
    }
    else {
        $('.info-counters').hide()
        $('.textarea').val('')
        $('#keywordDensityList').html('');
    }

    $('.textarea').removeClass('loading')
}

async function callAPI(url) {
    let response = await fetch(url);
    let data = await response.text()
    return data;
}

function applyWordDensity(text) {
    if (text !== '') {
        let chars = countCharactersWSpace(text)
        let spaces = countSpaces(text)
        let sentences = countSentences(text)
        let paras = countParagraphs(text)
        let words = countWords(text)
        $('.spChar').html(chars)
        $('#spSpaces').html(spaces)
        $('#spSent').html(sentences)
        $('#spPara').html(paras)
        $('.spWord').html(words)

        // Use the franc function to detect the language
        var languageCode = franc(text);
        let keywords = keywordDensity(text, languageCode === 'und' ? 'eng' : languageCode);
    }
}

function countCharactersWSpace(text) {
    if (text.replace("\n").length == 0) {
        return text.replace(/\n/g, "").length;
    } else {
        return text.replace(/\n/g, "").length;
    }
}

function countSpaces(text) {
    if (text.split(" ").length - 1 <= 1) {
        return text.split(" ").length - 1;
    } else {
        return text.split(" ").length - 1;
    }
}

function countSentences(text) {
    var amount = 0;
    if (text == "") {
        amount = 0;
    } else if ((text.substring(text.length - 1, text.length) == "?") || (text.substring(text.length - 1, text.length) == "!") || (text.substring(text.length - 1, text.length) == ".")) {
        amount = text.replace(/(\.|!|\?)+|(\.|!|\?)+$|(\.|!|\?)+/g, "#").split("#").length - 1;
    } else {
        amount = text.replace(/(\.|!|\?)+|(\.|!|\?)+$|(\.|!|\?)+/g, "#").split("#").length;
    }
    if (amount > 1) {
        return amount;
    } else {
        return amount;
    }
}

function countWords(text) {
    var amount = 0;
    if (text == "") {
        amount = 0;
    } else if ((text.substring(text.length - 1, text.length) == "?") || (text.substring(text.length - 1, text.length) == "!") || (text.substring(text.length - 1, text.length) == " ") || (text.substring(text.length - 1, text.length) == ".")) {
        amount = text.replace(/(\.|!|\?| )+|(\.|!|\?| )+$|(\.|!|\?| )+/g, "#").split("#").length - 1;
    } else {
        amount = text.replace(/(\.|!|\?| )+|(\.|!|\?| )+$|(\.|!|\?| )+/g, "#").split("#").length;
    }
    if (amount > 1) {
        return amount;
    } else {
        return amount;
    }
}

function countParagraphs(text) {
    var amount = 0;
    if (text == "") {
        amount = 0;
    } else if (text.substring(text.length - 1, text.length) == "\n") {
        amount = text.replace(/\n+|\n+$|(\n)+/g, "#").split("#").length - 1;
    } else {
        amount = text.replace(/\n+|\n+$|(\n)+/g, "#").split("#").length;
    }
    if (amount > 1) {
        return amount;
    } else {
        return amount;
    }
}

function keywordDensity(text, langCode) {
    let language = window['languageFullName'][langCode]
    if (language === undefined)
        language = window['languageFullName']['eng']

    var stopwords = window[language.toLowerCase()];
    var textTemp = [];
    text = text.split(" ");
    var found = 0;
    var position = '';
    if (stopwords.length > 0) {
        for (var i = 0; i < stopwords.length; i++) {
            while (text.indexOf(stopwords[i]) >= 0) {
                position = text.indexOf(stopwords[i]);
                text.splice(position, 1);
            }
        }
    }
    for (var i = 0; i < text.length; i++) {
        if (text[i]) {
            textTemp.push(text[i]);
        }
    }
    text = textTemp;
    var allWords = text.length;
    var keywords = [];
    var keywordList = [];
    var word = '';
    var wordPosition = '';
    for (var i = 0; i < text.length; i++) {
        word = text[i];
        wordPosition = keywordList.indexOf(word);
        if (wordPosition >= 0) {
            keywords[wordPosition]['count'] += 1;
            keywords[wordPosition]['percent'] = Math.round((keywords[wordPosition]['count'] / allWords) * 100);
        } else {
            keywords.push({
                "word": word,
                "count": 1,
                "percent": Math.round((1 / allWords) * 100)
            });
            keywordList.push(word);
        }
    }
    var allSorted = [];
    var sortedIndexes = Object.keys(keywords).sort(function (keyA, keyB) {
        return keywords[keyB].count - keywords[keyA].count;
    });
    for (var i = 0; i < sortedIndexes.length; i++) {
        allSorted.splice(i, 0, {
            "word": keywords[sortedIndexes[i]]['word'],
            "count": keywords[sortedIndexes[i]]['count'],
            "percent": keywords[sortedIndexes[i]]['percent']
        });
    }
    keywords = allSorted;
    var keywordHTML = document.getElementById("keywordDensityList");
    keywordHTML.innerHTML = '';
    for (var i = 0; i < keywords.length; i++) {
        keywordHTML.innerHTML = keywordHTML.innerHTML + '<li><span class="word-text">' + keywords[i]['word'] + '</span><span class="word-count">' + keywords[i]['count'] + '</span><span class="word-percent">' + keywords[i]['percent'] + '%</span><div class="clear"></div></li>';
    }
}

$('input[type="text"], select').on('input', e => {
    fetchInput();
})


async function callAPIOnLoad() {
    let scheme = $('#selScheme').val()
    let server = $('#txtServer').val()
    let prefix = $('#selPrefix').val()
    let identifier = $('#txtIdentifier').val()
    let version = $('#txtVersion').val()
    let infoAPIURL = `${scheme}://${server}/${prefix}/${identifier}/${version}/textinfo.json`

    await setInputs(infoAPIURL);
    await fetchInput();
}

callAPIOnLoad();
