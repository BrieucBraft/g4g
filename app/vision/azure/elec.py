import os
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
import time
import csv
from utils import removeUnwanted, removePrefix

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

    if (hours == '0' or all(elem not in digiDots for elem in str(hours))) and roi != False:
        read_response = cv_client.read_in_stream(open(roi_path, 'rb'), language='en', raw=True)
        hours = extraction(cv_client, read_response, False)

    return str(hours)


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
    hours = removePrefix(str(hours))
    return hours


def findData(array):
    '''
    INPUT : Array res_array with all the words and numbers extracted on the picture. Every time there is a space on the picture, 
            a new element is added to the array
    
    Additional info : The amount of operating hours is a number of 4 or 5 digits before the comma or dot.

                    The desired number is sometimes preceded by "operatinghours:", sometimes by "heuresdefonct.:" (caps don't matter)
                    Sometimes it is preceded by nothing.

                    It is also sometimes followed by 'h' or by 'H' or by '(h)', consider the case where the detection confuses
                    a parenthesis with bracket.

                    Be careful, there are also some other unwanted numbers on the image, such as numbers followed by 'kWh' 
                    or other numbers followed by 'h' or 'H'

    OUTPUT : Update the hours.csv file by adding a line with the amount of operating hours.

    '''

    # Regex pattern to find relevant numbers (4 or 5 digits, followed by optional comma or dot and more digits)
    #pattern = re.compile(r'\b\d{4,5}([.,]\d{1,2})?\b')  # Match 4 or 5 digits, followed by an optional comma or dot and 1 or 2 digits

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
        if 'operatinghours' in res_array[id] or 'heuresdefonct' in res_array[id] :
                conditions[0] = True
                continue

        conditions[3] = False
        conditions[2] = False

        for elem in text:
            if elem in digits:
                conditions[2] = True
            elif elem not in digits:
                if elem in dots and conditions[3] == False:
                    conditions[3] = True
                    text = text.replace('.', '')
                elif elem not in 'kmwh': 
                    conditions[2] = False
                    break
        
        if conditions[2] == True:
            
            #if len(text) >= 7 and all(elem in digits for elem in text):
            #    continue
                    
            if conditions[0] == False and conditions[1] == False:
                hours = text

            if conditions[0] == True :
                for helem in wh:
                    if res_array[(id + 1)%length] == helem and length!=1:
                        hours = text
                        conditions[1] = True
                        break
                    elif helem in text:
                        #hours = text.replace(helem, '')
                        hours = text.split(helem)[0]
                        conditions[1] = True
                        break
                    else:
                        hours = text
                return hours

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

def toCSV(allResults):
    # If we found any potential hours, add them to the CSV

        # Save results to CSV
    with open("output/elec_values.csv", "w", newline="") as csvfile:
        fieldnames = ["filename", "counter_value"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in allResults:
            writer.writerow(result)
    
    return