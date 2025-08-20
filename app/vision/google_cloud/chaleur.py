import os
import io
import json
import csv
import cv2
import imutils
from google.cloud import vision
import glob
from dino.preprocessor import preProcessing
from utils import removeUnwanted
from azure.chaleur import mainAzure


# Load Google Cloud credentials
credentials = json.load(open('go4green-435412-6555fb2e2af1.json'))
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'go4green-435412-6555fb2e2af1.json'

# Initialize the Google Cloud Vision client
client = vision.ImageAnnotatorClient()

digiDots = '0123456789'

def mainChaleur(image_path, cv_client):
    # Loop over each file
    allResults = []

    roi = False


    image = cv2.imread(image_path)
    resized_image = imutils.resize(image, height=750, inter=cv2.INTER_CUBIC)

    # Save the cropped image
    temp_images_dir = "temp_images"
    os.makedirs(temp_images_dir, exist_ok=True)
    name = 'temp.jpg'
    temp_image_path = os.path.join(temp_images_dir, name)
    temp_image_path = f'{temp_images_dir}/{name}'
    cv2.imwrite(temp_image_path, resized_image)

    try:
        
        roi_path, roi = preProcessing(temp_image_path)

        # Read the image file for Google Vision OCR
        with io.open(roi_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        image_context = vision.ImageContext(language_hints=['en'])
        response = client.text_detection(image=image, image_context = image_context)
        texts = response.text_annotations
        hours = extraction(texts, False)

    except Exception as e:
        print(e)
        with io.open(temp_image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations
        hours = extraction(texts, roi)

    if (hours == 0 or all(elem not in digiDots for elem in str(hours))) and roi != False:
        with io.open(temp_image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations
        hours = extraction(texts, roi)

    hours2 = mainAzure(cv_client, roi)
    
    allResults.append(str(hours))
    allResults.append(str(hours2))

    filesToDel = glob.glob('cropped_images/*')
    for f in filesToDel:
        os.remove(f)
    filesToDel = glob.glob('temp_images/*')
    for f in filesToDel:
        os.remove(f)

    #toCSV(allResults)
    return allResults

def extraction(texts, roi):
    res_array = []

    # Process the detected text
    if len(texts) > 0:
        for text in texts[1:]:  # First element is the full text, subsequent ones are lines or words
            x_coords = [vertex.x for vertex in text.bounding_poly.vertices]
            y_coords = [vertex.y for vertex in text.bounding_poly.vertices]

            if roi == False:
                res_array.append(text.description.replace(" ", ""))
            elif all(roi['x_min'] <= x <= roi['x_max'] for x in x_coords) and all(roi['y_min'] <= y <= roi['y_max'] for y in y_coords):
                res_array.append(text.description.replace(" ", ""))
    
    hours = findData(res_array)
    return hours

def findData(array):
    hours = 0
    conditions = [False, False, False, False]  # [prefix detected, suffix detected, all acceptable char, commadot already detected]

    res_array = [text.lower() for text in array]

    accepted = '0123456789.,'
    res_array = removeUnwanted(res_array, accepted)
    id = -1
    res_array = [''.join(res_array)]
    length = len(res_array)
    
    for text in res_array:
        id += 1

        dots = '.,'
        digits = '0123456789'
        wh = ['kwh', 'mwh']
        

        conditions[3] = False
        conditions[2] = False

        for elem in text:
            if elem in digits:
                conditions[2] = True
            elif elem in dots and not conditions[3]:
                conditions[3] = True
                text = text.replace('.', '')
            elif elem not in 'kmwh':
                conditions[2] = False
                break

        if conditions[2]:
            if conditions[0] == False and conditions[1] == False:
                hours = text


            for helem in wh:
                if helem in res_array[(id + 1) % length] and length != 1:
                    hours = text
                    conditions[1] = True
                    return hours
                elif helem in text:
                    hours = text.split(helem)[0]
                    conditions[1] = True
                    return hours
    return hours

def toCSV(allResults):
    # Save results to CSV
    with open("output/chaleur_values.csv", "w", newline="") as csvfile:
        fieldnames = ["filename", "counter_value", "counter_value2"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in allResults:
            writer.writerow(result)

    return
