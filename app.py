from flask import Flask, request, jsonify, Response, render_template, send_from_directory
import xml.etree.ElementTree as ET
# import required modules
#from bs4 import BeautifulSoup
import xml.dom.minidom
import os
import fitz
import re
import json

app = Flask(__name__)


@app.route('/')
def index():
    # Render the HTML page
    return render_template('index.html')


@app.route('/text_fragment_api')
def text_fragment_api():
    return render_template('text-fragment-api.html')


@app.route('/text_info_api')
def text_info_api():
    return render_template('text-info-api.html')

#Following URL is for Text Fragment API
@app.route('/<identifier>/<version>/<mode>/<fragment>/<quality>.<format>', defaults={'prefix': None}, methods=['GET'], endpoint='func2')
@app.route('/<prefix>/<identifier>/<version>/<mode>/<fragment>/<quality>.<format>', methods=['GET'], endpoint='func2')
def text_api(prefix, identifier, version, mode, fragment, quality, format):
    # prefix = request.args.get('prefix')
    try:
        request_data = {
            "identifier": identifier,
            "version": version,
            "mode": mode,
            "fragment": fragment,
            "quality": quality,
            "format": format,
            "prefix": prefix
        }

        fileName = find_file_in_folder('data/', request_data["identifier"])
        if fileName:
            all_text_info = getAllTextInfo(fileName)
            if request_data['mode'] == 'char':
                sub_text = callCharMode(all_text_info, request_data)
                return returnResponseWithSpecificFormat(sub_text, request_data)
            elif request_data['mode'] == 'token':
                tokens_string = callTokenMode(all_text_info,request_data)
                return returnResponseWithSpecificFormat(tokens_string, request_data)
        else:
            return returnResponseWithSpecificFormat('Text Fragment API Error: Identifier not found.', request_data)
    except Exception as e:
        return returnResponseWithSpecificFormat('Text Fragment API Error: Invalid Request. ')
        # return returnResponseWithSpecificFormat(repr(e), request_data)

#Following URL is for Text Info API
@app.route('/<identifier>/<version>/<info>.json', defaults={'prefix': None}, methods=['GET'], endpoint='func1')
@app.route('/<prefix>/<identifier>/<version>/<info>.json', methods=['GET'], endpoint='func1')
def text_info_api(prefix, identifier, version, info):
    # prefix = request.args.get('prefix')
    try:
        request_data = {
            "identifier": identifier,
            "version": version,
            "info": info,
            "format": format,
            "prefix": prefix
        }

        fileName = find_file_in_folder('data/', request_data["identifier"])
        if fileName:
            # jsonData = """ 
            #     {
            #         "identifier" : "1E34750D-38DB-4825-A38A-B60A345E591C",
            #         "versioning" : "date",
            #         "date" : "2023-11-24"
            #         "modes" : [ "char", "token", "book", "prose" ],
            #         "custom_modes" : [ "prose" ],
            #         "qualities" : ["compact", "plaintext"],
            #         "formats" : [ "txt" ],
            #         "first_release" : "2022-05-07",
            #         "releases" : [
            #             "2022-05-07",
            #             "2023-01-06",
            #             "2023-11-24"
            #         ] 
            #     }
            # """
            data = {
                    "identifier": identifier, 
                    "versioning": version, 
                    "modes": ["char", "token", "book"], 
                    "qualities": ["raw", "compact"], 
                    "formats": [ "txt", "tei", "html", "md" ]
                    }
            return json.dumps(data, sort_keys=False)
        else:
            return returnResponseWithSpecificFormat('Error: Identifier not found.', request_data)
    except Exception as e:
        return returnResponseWithSpecificFormat('Error: Invalid Request.', request_data)
        # return returnResponseWithSpecificFormat(repr(e), request_data)


def getAllTextInfo(filename):
    ext = os.path.splitext(filename)[1]
    all_text = ''

    if ext == '.xml':
        all_text = getAllTextFromXML(filename)
    elif ext == '.pdf':
        all_text = read_pdf(filename)

    return all_text


def getAllTextFromXML(filename):
    xml_file = filename
    # Parse XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    extracts = []
    readtraces_module = root.find('.//module[@type="readtraces"]')
    if readtraces_module is not None:
        # Extract <Extracts> elements from the found module
        for page in readtraces_module.findall('.//page'):
            for zone in page.findall('.//zone'):
                extract_element = zone.find('.//rn/Extracts')
                # print(extract_element.text)
                if extract_element is not None:
                    extracts.append({
                        "text": str(extract_element.text).strip(),
                        "pageNo": str(page.find('.//Pagenumber').text).strip(),
                        "Dimensions": f'{str(page.find(".//Dimensions/width").text).strip()} x {str(page.find(".//Dimensions/height").text).strip()}'
                    })

    return extracts

def read_pdf(file_path):
    text = ""
    extracts = []
    with fitz.open(file_path) as pdf_file:
        for page_num in range(len(pdf_file)):
            page = pdf_file[page_num]
            #text += page.get_text()
            extracts.append({
                        "text": str(page.get_text()).strip(),
                        "pageNo": str(page_num).strip()
                    })

    return extracts

def callCharMode(all_text_info, request_data):
    # sub_texts = []
    # for text_info in all_text_info:
    #     sub_text = getSubstring(request_data, text_info["text"])
    #     if sub_text != '':
    #         sub_texts.append({
    #             sub_text
    #         })
    texts = [obj["text"] for obj in all_text_info]
    combined_texts = " ".join(texts)

    return getFragments(request_data, combined_texts)


def getFragments(request_data, inputData):
    text = ''
    if ',' in request_data["fragment"]:
        range = request_data["fragment"].split(',')
        if range[0] != '' and range[1] != '':
            text = inputData[int(range[0]) - 1: int(range[1]) + 1]
        elif range[0] == '':
            text = inputData[:int(range[1]) + 1]

        return text
    elif '+' in request_data["fragment"]:
        range = request_data["fragment"].split('+')
        text = inputData[int(range[0]) -
                              1: (int(range[0]) - 1) + int(range[1])]
        return text
    else:
        text = inputData[int(request_data["fragment"])]
        return text


def getSubstring(request_data, original_text):
    text = ''
    isCompleted = False
    print('fragment: ' + request_data["fragment"])
    if ',' in request_data["fragment"]:
        range = request_data["fragment"].split(',')
        if range[0] != '' and range[1] != '':
            text = original_text[int(range[0]) - 1: int(range[1]) + 1]
        elif range[0] == '':
            text = original_text[:int(range[1]) + 1]

        if len(text) < int(range[1]) + 1:
            request_data["fragment"] = str(
                1) + ',' + str((int(range[1]) + 1) - len(text))
            return isCompleted, request_data["fragment"], text
        elif len(text) >= int(range[1]):
            isCompleted = True
            return isCompleted, request_data["fragment"], text
    elif '+' in request_data["fragment"]:
        range = request_data["fragment"].split('+')
        text = original_text[int(range[0]) -
                             1: (int(range[0]) - 1) + int(range[1])]
        isCompleted = True
        return isCompleted, request_data["fragment"], text
    else:
        text = original_text[int(request_data["fragment"])]
        isCompleted = True
        return isCompleted, request_data["fragment"], text

#=====================================================================================================
# Token Mode
def callTokenMode(all_text_info, request_data):
    texts = [obj["text"] for obj in all_text_info]
    combined_texts = " ".join(texts)
    # Tokenize the long string using whitespace and punctuation
    tokens = re.findall(r'\w+|[^\w\s]', combined_texts)
    #print('printing tokens:')
    #print(tokens)
    return_fragments = getFragments(request_data, tokens)
    if not isinstance(return_fragments, list):
        return return_fragments
    return ' '.join(return_fragments)

#=====================================================================================================
def returnResponseWithSpecificFormat(response, request_data):
    #============================== Quality =================
    if(request_data['quality'] == 'compact'):
        #response = ' '.join(response)
        split_response = response.split(' ')
        cleared_string = [s for s in split_response if s and s != '/\n']
        response = ' '.join(cleared_string)
        response = re.sub(r'\\[^\s]|\\r\\n', '', response)
    #=======================================================
    if request_data["format"] == 'txt':
        return Response(response, mimetype='text/plain; charset=UTF-8')
    elif request_data["format"] == 'html':
        return Response(f'<p>{response}</p>', mimetype='text/html; charset=utf-8')
    elif request_data["format"] == 'xml':  # application/tei+xml
        stringXML = f'<?xml version="1.0" encoding="UTF-8"?><content><textNode>{response}</textNode></content>'
        dom = xml.dom.minidom.parseString(stringXML)
        # Prettify XML
        prettified_xml = dom.toprettyxml()
        return Response(prettified_xml, mimetype='text/plain; charset=UTF-8')
    elif request_data["format"] == 'md':
        return Response(response, mimetype='text/markdown; charset=utf-8')

def find_file_in_folder(folder_path, file_name):
    # Walk through the directory tree
    for root, dirs, files in os.walk(folder_path):
        # Check if the file exists in the current directory
        for f in files:
            if os.path.splitext(f)[0] == file_name:
                return os.path.join(root, f)

    return None


if __name__ == '__main__':
    app.run(debug=True)
