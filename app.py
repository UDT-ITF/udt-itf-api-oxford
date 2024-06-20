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
            if request_data['fragment'] == 'full':
                full_text = getFullText(request_data, fileName)
                return full_text
            
            if request_data['mode'] == 'char':
                if request_data['quality'] == 'raw':
                    sub_text = callCharModeWithRaw(fileName, request_data)
                else:
                    all_text_info = getAllTextInfo(fileName)
                    sub_text = callCharMode(all_text_info, request_data)

                return returnResponseWithSpecificFormat(sub_text, request_data)
            elif request_data['mode'] == 'token':
                if request_data['quality'] == 'raw':
                    return returnResponseWithSpecificFormat("***** Feature in progress... *****", request_data)
                else:
                    all_text_info = getAllTextInfo(fileName)
                    tokens_string = callTokenMode(all_text_info,request_data)

                return returnResponseWithSpecificFormat(tokens_string, request_data)
            elif request_data['mode'] == 'book':
                if request_data['quality'] == 'raw':
                    return returnResponseWithSpecificFormat("***** Feature in progress... *****", request_data)
                else:
                    all_text_info = getAllTextInfo(fileName)
                    book_string = callBookMode(all_text_info,request_data)
                
                return returnResponseWithSpecificFormat(book_string, request_data)
        else:
            return returnResponseWithSpecificFormat('Text Fragment API Error: Identifier not found.', request_data)
    except Exception as e:
        return returnResponseWithSpecificFormat('Text Fragment API Error: Invalid Request. ', request_data)
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
            ext = os.path.splitext(fileName)[1]
            if ext == '.xml':
                data = {
                        "identifier": identifier, 
                        "versioning": version, 
                        "modes": ["char", "token", "book"], 
                        "qualities": ["raw", "plaintext", "compact"], 
                        "formats": [ "txt", "tei", "html", "md" ]
                    }
            elif ext == '.pdf':
                data = {
                        "identifier": identifier, 
                        "versioning": version, 
                        "modes": ["char", "token", "book"], 
                        "qualities": ["plaintext", "compact"], 
                        "formats": [ "txt", "tei", "html", "md" ]
                    }
            
            return json.dumps(data, sort_keys=False)
        else:
            return returnResponseWithSpecificFormat('Error: Identifier not found.', request_data)
    except Exception as e:
        return returnResponseWithSpecificFormat('Error: Invalid Request.', request_data)
        # return returnResponseWithSpecificFormat(repr(e), request_data)

def getFullText(request_data, filename):
    ext = os.path.splitext(filename)[1]
    all_text = ''

    if ext == '.xml':
        tree = ET.parse(filename)
        root = tree.getroot()
        # Find all elements as strings
        elements = [ET.tostring(child, encoding='unicode') for child in root.findall('.//module[@type="readtraces"]/*')]
        # Print the elements
        for element in elements:
           all_text = all_text + element
    elif ext == '.pdf':
        all_text = read_pdf(filename)

    return all_text

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
    page_num = 1
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
                        "pageNo": str(page_num).strip(),
                        "xmlPageNo": str(page.find('.//Pagenumber').text).strip(),
                        "Dimensions": f'{str(page.find(".//Dimensions/width").text).strip()} x {str(page.find(".//Dimensions/height").text).strip()}'
                    })
                    page_num = page_num + 1

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
    if not '0,' in request_data['fragment'] and not '0' in request_data['fragment'][0]:
        texts = [obj["text"] for obj in all_text_info]
        combined_texts = " ".join(texts)

    return getFragments(request_data, combined_texts)

def callCharModeWithRaw(fileName, request_data):
    if not '0,' in request_data['fragment'] and not '0' in request_data['fragment'][0]:
        tree = ET.parse(fileName)
        root = tree.getroot()
        combinedText = ''
        # Define an empty list to store modified elements
        modified_elements = []      
        done = False
        readtraces_module = root.find('.//module[@type="readtraces"]')
        if readtraces_module is not None:
            # Extract <Extracts> elements from the found module
            for page in readtraces_module.findall('.//page'):
                for zone in page.findall('.//zone'):
                    if ',' in request_data["fragment"]:
                        frange = request_data["fragment"].split(',')
                        if frange[0] != '' and frange[1] != '':
                            extract_element = zone.find('.//rn/Extracts')
                            # print(extract_element.text)
                            if extract_element is not None:
                                if len(combinedText) + int(frange[0]) < int(frange[1]):
                                    combinedText = combinedText + (str(extract_element.text).strip())[int(frange[0]) -1 : int(frange[1])]
                                    extract_element.text = (str(extract_element.text).strip())[int(frange[0]) -1 : int(frange[1])]
                                    modified_elements.append(page)
                                else:
                                    done = True
                                    break
                        elif frange[0] == '': #,2
                            if len(combinedText) < int(frange[1]):
                                extract_element = zone.find('.//rn/Extracts')
                                # print(extract_element.text)
                                if extract_element is not None:
                                    combinedText = combinedText + (str(extract_element.text).strip())[0:int(frange[1])]
                                    extract_element.text = (str(extract_element.text).strip())[0:int(frange[1])]
                                    modified_elements.append(page)
                            else:
                                done = True
                                break
                    elif '+' in request_data["fragment"]:
                        frange = request_data["fragment"].split('+')
                        extract_element = zone.find('.//rn/Extracts')
                            # print(extract_element.text)
                        if extract_element is not None:
                            if len(combinedText)+int(frange[0]) < int(frange[1]):
                                combinedText = combinedText + (str(extract_element.text).strip())[int(frange[0]) - 1: (int(frange[0]) - 1) + int(frange[1])]
                                extract_element.text = (str(extract_element.text).strip())[int(frange[0]) - 1: (int(frange[0]) - 1) + int(frange[1])]
                                modified_elements.append(page)
                            else:
                                done = True
                                break
                    else:
                        extract_element = zone.find('.//rn/Extracts')
                            # print(extract_element.text)
                        if extract_element is not None:
                            if len(combinedText) > int(request_data["fragment"]):
                                last_page_element = modified_elements[len(modified_elements) - 1]
                                modified_zone = last_page_element.find('.//zone')
                                modified_element = modified_zone.find('.//rn/Extracts')
                                modified_element.text = combinedText[int(request_data["fragment"]) - 1]
                                modified_elements = []
                                modified_elements.append(last_page_element)
                                done = True
                                break
                            else:
                                combinedText += str(extract_element.text).strip() + ' '
                                modified_elements.append(page)
                if done:
                    break

    final_xml = ''
    if "".join([ET.tostring(elem, encoding='unicode', method='xml') for elem in modified_elements]) != "":
        final_xml = "<module n='4' type='readtraces'>\n\t" + "".join([ET.tostring(elem, encoding='unicode', method='xml') for elem in modified_elements]) + "\n</module>"

    return final_xml 

def callBookMode(all_text_info, request_data):
    texts = ''
    lines_texts = ''
    page_texts = ''
    if not 'p0,' in request_data['fragment'] and not 'p0' in request_data['fragment'][0]:
        if 'p' in request_data['fragment']:
            fragment = getPageFragmentOnly(request_data['fragment']).replace('p', '')
            if ',' in fragment: 
                frange = fragment.split(',')
                if frange[0] != '' and frange[1] != '': #p1,p2
                        for x in range(int(frange[0]) - 1, int(frange[1])):
                            texts = texts + all_text_info[x]['text'] + '\n'
                elif frange[0] == '': #,p2
                        for x in range(0, int(frange[1])):
                            texts = texts + all_text_info[x]['text'] + '\n'
                #return texts
            elif '+' in fragment:
                frange = fragment.split('+')
                for x in range(int(frange[0]) - 1, int(frange[1])):
                    texts = texts + all_text_info[x]['text'] + '\n'
                #return texts
            else:
                texts = all_text_info[int(fragment)-1]['text']
                #return texts
        
        page_texts = texts

        if 'l' in request_data['fragment']:
            lines_texts = ''
            fragment = getLineFragmentOnly(request_data['fragment']).replace('l', '')
            lines = texts.split('\n')
            if ',' in fragment: 
                frange = fragment.split(',')
                if frange[0] != '' and frange[1] != '': #l1,l2
                        lines_texts = ' '.join(lines[int(frange[0]) - 1:int(frange[1])])
                elif frange[0] == '': #,l2
                        lines_texts =  ' '.join(lines[0:int(frange[1])])
            elif '+' in fragment:
                frange = fragment.split('+')
                lines_texts = ' '.join(lines[int(frange[0]) - 1:int(frange[1])])
            else:
                lines_texts = lines[int(fragment)-1]
                
            texts = lines_texts

        if 'c' in request_data['fragment']:
            fragmentLine = getLineFragmentOnly(request_data['fragment']).replace('l', '')
            lines = page_texts.split('\n')
            charTexts = ''
            fragmentChar = getCharacterFragmentOnly(request_data['fragment']).replace('c', '')
            if ',' in fragmentLine:
                print('getLineFragmentOnly(request_data["fragment"])', getLineFragmentOnly(request_data['fragment']))
                frange = fragmentLine.split(',')
                if frange[0] != '' and frange[1] != '': #l1,l2 
                    for i in range(int(frange[0]) - 1, int(frange[1]) + 1): 
                        if ',' in fragmentChar:
                            crange = fragmentChar.split(',')
                            if crange[0] != '' and crange[1] != '': #c1,c2
                                if i == (int(frange[0]) - 1):
                                    charTexts = charTexts + lines[i][int(crange[0])-1:]
                                elif i == int(frange[1]):
                                    charTexts = charTexts + lines[i][:int(crange[1])]
                                else:
                                    charTexts = charTexts + lines[i]
                elif frange[0] == '':
                    for i in range(0, int(frange[1]) + 1): 
                        if ',' in fragmentChar:
                            crange = fragmentChar.split(',')
                            if crange[0] != '' and crange[1] != '': #c1,c2
                                if i == (int(frange[0]) - 1):
                                    charTexts = charTexts + lines[i][int(crange[0])-1:]
                                elif i == int(frange[1]):
                                    charTexts = charTexts + lines[i][:int(crange[1])]
                                else:
                                    charTexts = charTexts + lines[i]
                            elif crange[0] == '': #,c2
                                if i == int(frange[1]):
                                    charTexts = charTexts + lines[i][:int(crange[1])]
                                else:
                                    charTexts = charTexts + lines[i]
            else:
                if '+' in fragmentChar: 
                    crange = fragmentChar.split('+')
                    charTexts = lines[int(fragmentLine)-1][int(crange[0]) -
                          1: (int(crange[0]) - 1) + int(crange[1])]
                else:
                    charTexts = lines[int(fragmentLine)-1][int(fragmentChar) - 1]

            texts = charTexts
        
    return texts        

def getPageFragmentOnly(input_fragment):
    # Split the string by commas
    parts = input_fragment.split(',')

    # Extract the part before the first semicolon for each segment
    result = [part.split(';')[0] for part in parts]

    # Join the result back into a string separated by commas
    result_string = ','.join(result)

    # Print the resultant string
    return result_string

def getLineFragmentOnly(input_fragment):
    # Split the string by commas
    parts = input_fragment.split(',')

    # Initialize a list to hold the extracted l parts
    l_parts = []

    # Iterate over each part
    for part in parts:
        # Split each part by semicolons
        sub_parts = part.split(';')

        # Check if there's an l part to extract
        if len(sub_parts) > 1:
            l_parts.append(sub_parts[1])

    # Join the result back into a string separated by commas
    result_string = ','.join(l_parts)
    # If the original string starts with a comma, ensure the result does too
    if input_fragment.startswith(',') and not result_string.startswith(','):
        result_string = ',' + result_string

    return result_string

def getCharacterFragmentOnly(input_fragment):
    # Split the string by commas
    parts = input_fragment.split(',')

    # Initialize a list to hold the extracted c parts
    c_parts = []

    # Iterate over each part
    for part in parts:
        # Split each part by semicolons
        sub_parts = part.split(';')

        # Check if there's a c part to extract (it should be the third element if present)
        if len(sub_parts) > 2:
            c_parts.append(sub_parts[2])
        elif len(sub_parts) == 3:
            # Handle case where c1 and c2 are combined with '+'
            combined_c_parts = sub_parts[2].split('+')
            c_parts.extend(combined_c_parts)

    # Join the result back into a string separated by commas
    result_string = ','.join(c_parts)

    # If the original string starts with a comma, ensure the result does too
    if input_fragment.startswith(',') and not result_string.startswith(','):
        result_string = ',' + result_string
    
    return result_string

def getFragments(request_data, inputData):
    text = ''
    if ',' in request_data["fragment"]:
        range = request_data["fragment"].split(',')
        if range[0] != '' and range[1] != '':
            text = inputData[int(range[0]) - 1: int(range[1])]
        elif range[0] == '':
            text = inputData[:int(range[1])]

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
    print('fragment: ' + request_data["fragment"][0])
    
    if ',' in request_data["fragment"]:
        range = request_data["fragment"].split(',')
        if range[0] != '' and range[1] != '':
            text = original_text[int(range[0]): int(range[1])]
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
    # if request_data['quality'] == 'raw':
    #     return response
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
