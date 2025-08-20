import os
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
import time
import imutils
import cv2
import csv
from app.vision.dino.preprocessor import preProcessing
from app.utils import removeUnwanted
import glob

digiDots = '0123456789,.'

def mainHeures(image_path, cv_client):
    # Loop over each file
    allResults = []
    roi = False

    # Check if the file is an image (you can adjust the extensions)
    #if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):

    image = cv2.imread(image_path)
    resized_image = imutils.resize(image, height=1250, inter=cv2.INTER_CUBIC)

    # Save the cropped image
    temp_images_dir = "temp_images"
    os.makedirs(temp_images_dir, exist_ok=True)
    name = 'temp.jpg'
    temp_image_path = os.path.join(temp_images_dir, name)
    cv2.imwrite(temp_image_path, resized_image)

    try:
        image_byte, roi = preProcessing(temp_image_path)
        read_response = cv_client.read_in_stream(open(temp_image_path, 'rb'), language='en', raw=True)
        #read_response = cv_client.read_in_stream(copy.deepcopy(byte_stream), reading_order='natural', raw=True)
        hours = extraction(cv_client, read_response, roi)
    
    except Exception as e:
        print(e)
        read_response = cv_client.read_in_stream(open(temp_image_path, 'rb'), language='en', raw=True)
        hours = extraction(cv_client, read_response, roi)
    
    if (hours == 0 or all(elem not in digiDots for elem in hours)) and roi != False:
        read_response = cv_client.read_in_stream(open(image_byte, 'rb'), language='en', raw=True)
        hours = extraction(cv_client, read_response, False)
    allResults.append(str(hours))

    #toCSV(allResults)
    filesToDel = glob.glob('cropped_images/*')
    for f in filesToDel:
        os.remove(f)
    filesToDel = glob.glob('temp_images/*')
    for f in filesToDel:
        os.remove(f)
        
    return allResults


def extraction(cv_client, read_response, roi):
        # Call API with image file

    # Get the operation ID from the response header
    operation_location = read_response.headers["Operation-Location"]
    operation_id = operation_location.split("/")[-1]

    # Wait for the operation to complete
    while True:
        read_result = cv_client.get_read_result(operation_id)
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    res_array = []
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
    conditions = [False, False, True, False, False] # [prefix detected, suffix detected, all acceptable char, commadot already detected, at least 1 digit]

    res_array = []
    for text in array:
        res_array.append(text.lower())

    accepted = '0123456789.,hms()[]operatinghoursheuresdefonct:' 
    res_array = removeUnwanted(res_array, accepted)
    id = -1
    length = len(res_array)
    for text in res_array:
        id += 1

        dots = '.,'
        digits = '0123456789'
        otherAccepted = '(h)[]ms'
        h = ['(h)', '[h]', '(h]','[h)', 'h']
        if 'operatinghours' in res_array[id] or 'heuresdefonct' in res_array[id] :
                conditions[0] = True
                continue

        conditions[4] = False
        conditions[3] = False
        conditions[2] = True

        for elem in text:
            if elem not in digits and elem not in otherAccepted:
                if elem in dots and conditions[3] == False:
                    conditions[3] = True
                else : 
                    conditions[2] = False
            elif elem in digits:
                conditions[4] = True
        
        if conditions[2] == True and conditions[4] == True:
            
            if res_array[(id + 1)%length] == 'kwh' or 'kwh' in text:
                    continue
                    
            elif conditions[0] == False and conditions[1] == False:
                hours = text

            if conditions[0] == True :
                for helem in h:
                    if res_array[(id + 1)%length] == helem and length != 1:
                        hours = text
                        conditions[1] = True
                        break
                    elif helem in text:
                        hours = text.split(helem)[0]
                        conditions[1] = True
                        break
                    else:
                        hours = text
                return hours

            for helem in h:
                if res_array[(id + 1)%length] == helem and length != 1:
                    hours = text
                    conditions[1] = True
                    return hours
                elif helem in text:
                    hours = text.split(helem)[0]
                    conditions[1] = True
                    return hours
    return hours

def toCSV(allResults):
    # If we found any potential hours, add them to the CSV

        # Save results to CSV
    with open("output/heures_values.csv", "w", newline="") as csvfile:
        fieldnames = ["filename", "counter_value"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in allResults:
            writer.writerow(result)
    
    return