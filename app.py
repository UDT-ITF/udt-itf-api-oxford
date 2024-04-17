from flask import Flask, request, jsonify, Response
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

@app.route('/<identifier>/<version>/<mode>/<fragment>/<quality>.<format>', defaults={'prefix': None}, methods=['GET'])
@app.route('/<prefix>/<identifier>/<version>/<mode>/<fragment>/<quality>.<format>', methods=['GET'])
def text_api(prefix, identifier, version, mode, fragment, quality, format):
    #prefix = request.args.get('prefix')
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

        if find_file_in_folder('data/', request_data["identifier"]):
            if request_data['mode'] == 'char':
                response = callCharMode(request_data)

            return returnResponseWithSpecificFormat(response, request_data)
        else:
            return returnResponseWithSpecificFormat('Identifier not found.', request_data)
    #return jsonify(response)
    except Exception as e:
         return returnResponseWithSpecificFormat('Invalid Request.', request_data)
         #return returnResponseWithSpecificFormat(repr(e), request_data)

def callCharMode(request_data):
    xml_file = f'data/{request_data["identifier"]}.xml'

    # Parse XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()
    isCompleted = False

    # Extract <Extracts> elements
    extracts = ''
    readtraces_module = root.find('.//module[@type="readtraces"]')

    if readtraces_module is not None:
        # Extract <Extracts> elements from the found module
        for page in readtraces_module.findall('.//page'):
            for zone in page.findall('.//zone'):
                extract_element = zone.find('.//rn/Extracts')
                #print(extract_element.text)
                if extract_element is not None:
                    isCompleted, request_data["fragment"], text = getSubstring(request_data, str(extract_element.text))

                    if request_data['format'] == 'txt':
                        extracts += convertToPlainText(page, zone, text)
                    elif request_data['format'] == 'html':
                        extracts += convertToHTML(page, zone, text)
                    elif request_data['format'] == 'xml':
                        extracts += convertToTEIXML(page, zone, text)
                    elif request_data['format'] == 'md':
                        extracts += convertToMD(page, zone, text)
                    #extracts.append({"extract": str(extract_element.text).strip()})

                if isCompleted == True:
                    break
            if isCompleted == True:
                break
    
    return extracts

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
            request_data["fragment"] = str(1) + ',' + str((int(range[1]) + 1) - len(text))
            return isCompleted, request_data["fragment"], text
        elif len(text) >= int(range[1]):
            isCompleted = True
            return isCompleted, request_data["fragment"], text
    elif '+' in request_data["fragment"]:
        range = request_data["fragment"].split('+')
        text = original_text[int(range[0]) - 1: (int(range[0]) - 1) + int(range[1])]
        isCompleted = True
        return isCompleted, request_data["fragment"], text
    else:
        text = original_text[int(request_data["fragment"])]
        isCompleted = True
        return isCompleted, request_data["fragment"], text

def convertToPlainText(page, zone, extract_element):
    returnText = ''
    returnText += 'Page Number: ' + str(page.find('.//Pagenumber').text) + '\n'
    returnText += 'Dimensions (W x H): ' + str(page.find('.//Dimensions/width').text) + ' x ' + str(page.find('.//Dimensions/height').text)  + '\n'
    returnText += 'Text Fragment: ' + str(extract_element) + '\n'
    returnText += '---------------------------------------------------\n'
    return returnText

def convertToMD(page, zone, extract_element):
    returnText = ''
    returnText += '**Page Number:** ' + str(page.find('.//Pagenumber').text) + '\n'
    returnText += '**Dimensions (W x H):** ' + str(page.find('.//Dimensions/width').text) + ' x ' + str(page.find('.//Dimensions/height').text)  + '\n'
    returnText += '**Text Fragment:** ' + str(extract_element) + '\n'
    returnText += '___________________________________________________\n'
    return returnText

def convertToHTML(page, zone, extract_element):
    returnText = '<div>'
    returnText += 'Page Number: ' + str(page.find('.//Pagenumber').text) + '<br />'
    returnText += 'Dimensions (W x H): ' + str(page.find('.//Dimensions/width').text) + ' x ' + str(page.find('.//Dimensions/height').text)  + '<br />'
    returnText += 'Text Fragment: ' + str(extract_element) + '<br />'
    returnText += '</div><hr />'
    return returnText

def convertToTEIXML(page, zone, extract_element):
    returnText = '<content>'
    returnText += '<Pagenumber>' + str(page.find('.//Pagenumber').text) + '</Pagenumber>'
    returnText += '<Dimensions><width>' + str(page.find('.//Dimensions/width').text) + '</width> <height> ' + str(page.find('.//Dimensions/height').text)  + '</height></Dimensions>'
    returnText += '<textNode>' + str(extract_element) + '</textNode>'
    returnText += '</content>'
    return returnText

def returnResponseWithSpecificFormat(response, request_data):
    if request_data["format"] == 'txt':
        return Response(response, mimetype='text/plain; charset=UTF-8')
    elif request_data["format"] == 'html':
        return Response(f'<html><body><div>{response}</div></body></html>', mimetype='text/html; charset=utf-8')
    elif request_data["format"] == 'xml': #application/tei+xml
        return Response(f'<?xml version="1.0" encoding="UTF-8"?><items>{response}</items>', mimetype='application/tei+xml')
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