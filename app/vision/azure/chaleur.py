import os
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
import time
from app.utils import removeUnwanted


digiDots = '0123456789'

def mainAzure(cv_client, roi):

    # Save the cropped image
    temp_images_dir = "temp_images"
    name = 'temp.jpg'
    temp_image_path = os.path.join(temp_images_dir, name)

    cropped_images_dir = 'cropped_images'
    name = 'crop.jpg'
    roi_path = os.path.join(cropped_images_dir, name)

    read_response = cv_client.read_in_stream(open(temp_image_path, 'rb'), language='en', raw=True)
    hours = extraction(cv_client, read_response, roi)
    
    
    if (hours == 0 or all(elem not in digiDots for elem in hours)) and roi != False:
        read_response = cv_client.read_in_stream(open(roi_path, 'rb'), language='en', raw=True)
        hours = extraction(cv_client, read_response, False)
    hours = str(hours)
    hours = ''.join([char for char in hours if char.isdigit()])
    return hours


def extraction(cv_client, read_response, roi):
        # Call API with image file

    # Get the operation ID from the response header
    operation_location = read_response.headers["Operation-Location"]
    operation_id = operation_location.split("/")[-1]

    # Wait for the operation to complete

    while True:
        read_result = cv_client.get_read_result(operation_id)
        if (read_result.status not in ['notStarted', 'running']):
            break
        time.sleep(1)

    res_array = []
    #roi = False
    # Print the detected text, including numbers
    if read_result.status == OperationStatusCodes.succeeded:
        for text_result in read_result.analyze_result.read_results:
            for line in text_result.lines:
                bbox = line.bounding_box
                x_coords = bbox[::2]  # Extract x coordinates [x1, x2, x3, x4]
                y_coords = bbox[1::2] # Extract y coordinates [y1, y2, y3, y4]
                if roi == False :
                    text = line.text
                    text = text.replace(" ", "")
                    res_array.append(text)

                elif all(roi['x_min'] <= x <= roi['x_max'] for x in x_coords) and all(roi['y_min'] <= y <= roi['y_max'] for y in y_coords):
                    text = line.text
                    text = text.replace(" ", "")
                    res_array.append(text)
    hours = findData(res_array)
    return hours


def findData(array):


    hours = 0
    conditions = [False, False, False, False] # [prefix detected, suffix detected, all acceptable char, commadot already detected]

    res_array = []
    for text in array:
        res_array.append(text.lower())

    accepted = '0123456789.,kwhm' 
    res_array = removeUnwanted(res_array, accepted)
    id = -1
    length = len(res_array)
    for text in res_array:
        id += 1

        dots = '.,'
        digits = '0123456789'
        otherAccepted = '(h)[]ms'
        wh = ['kwh', 'mwh']

        conditions[3] = False
        conditions[2] = False

        for elem in text:
            if elem in digits:
                conditions[2] = True
            elif elem not in digits:
                if elem in dots and conditions[3] == False:
                    #conditions[3] = True
                    text = text.replace('.', '')
                    text = text.replace(',', '')
                elif elem not in 'kmwh': 
                    conditions[2] = False
                    break
        
        if conditions[2] == True:
                    
            if conditions[0] == False and conditions[1] == False:
                hours = text

            for helem in wh:
                if helem in res_array[(id + 1)%length] and length!=1:
                    hours = text
                    conditions[1] = True
                    return hours
                elif helem in text:
                    hours = text.split(helem)[0]
                    conditions[1] = True
                    return hours
    return hours