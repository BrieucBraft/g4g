print("Importing libraries... 0% done")
import os
import csv
print("Importing libraries... 25% done")
from vision.azure import mainGaz
from vision.google_cloud import mainChaleur
print("Importing libraries... 50% done")
from vision.google_cloud import mainElec
from vision.azure import mainHeures
from utils import *
print("Importing libraries... 75% done")
import json
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
print("Importing libraries... 100% done")


def toGoodColumn(dropbox_folder, yearMonth, credential_path):
    local_temp_folder = f'all_images/{yearMonth}'  # Temp folder to store downloaded images
    output_csv = "output/temp/outputTemp.csv"
    # Create a local temp folder if not exists
    if not os.path.exists(local_temp_folder):
        os.makedirs(local_temp_folder)

    # List all images in the Dropbox folder
    image_files, dbx = list_dropbox_images(dropbox_folder)

    # Check if the output CSV file exists before opening it
    if os.path.exists(output_csv):
        with open(output_csv, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            data = list(reader)
    else:
        data = []  # No file, so we start with an empty list
        print("The file does not exist. Creating a new file.")

    valuesDict = {}
    fullPathDict = {}
    heureList = []
    earlier = False
    firstTimeRunning = False

    for image_file in image_files:
        try:
            identite, code, nom, dateHeure = get_info_from_name(image_file)
            identite = checkID(identite, data)

            heureList.append(translate_datetime(dateHeure))

            # Download image from Dropbox to local folder
            dropbox_image_path = os.path.join(dropbox_folder, image_file).replace("\\","/")
            local_image_path = os.path.join(local_temp_folder, image_file).replace('\\','/')
            if not os.path.exists(local_image_path):
                download_image_from_dropbox(dropbox_image_path, local_image_path, dbx)
                firstTimeRunning = True

            full_path = os.path.abspath(local_image_path)

        except Exception as e:
            print(f"Error processing file {image_file}: {e}")
            continue

        # Azure Credentials
        credentials = json.load(open(credential_path))
        API_KEY = credentials['API_KEY']
        ENDPOINT = credentials['ENDPOINT']
        cv_client = ComputerVisionClient(ENDPOINT, CognitiveServicesCredentials(API_KEY))
        results = None

        with open(output_csv, 'w', newline='') as csvfile:
            fieldnames = ['num ID', 'unique ID', 'CODE CHAUFFERIE', 'NOM COMPTEUR', 'Date & Heure', 'index m', 'index m-1', 'index m-2', 
                        'Date & Heure 1/4 H', 'index I+', 'index extrapole', 'test I+', 'test passed']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()

            existing_ids = {row['unique ID']: row for row in data}  # A dictionary to store rows by their ID for easy lookup

            rowHeure = None
            if f'{code} Heure' in existing_ids:
                rowHeure = existing_ids[f'{code} Heure']
            elif f'{code} Heure-1' in existing_ids:
                rowHeure = existing_ids[f'{code} Heure-1']
            elif f'{code} Heure-2' in existing_ids:
                rowHeure = existing_ids[f'{code} Heure-2']
            elif f'{code} Heure-3' in existing_ids:
                rowHeure = existing_ids[f'{code} Heure-3']

            if rowHeure is not None and is_earlier_or_empty(rowHeure['Date & Heure'], dateHeure):
                earlier = True

            # if code+nom not in valuesDict:
            #         valuesDict[code+nom] = []
            #         fullPathDict[code + nom] = []

            # fullPathDict[code + nom].append(full_path)

            if earlier:
                if 'Gaz' in nom:
                    results = mainGaz(local_image_path)
                elif 'Elec' in nom:
                    results = mainElec(local_image_path, cv_client)
                elif 'Chaleur' in nom:
                    results = mainChaleur(local_image_path, cv_client)
                elif 'Heure' in nom:
                    results = mainHeures(local_image_path, cv_client)
                else:
                    continue

                if code+nom not in valuesDict:
                    valuesDict[code+nom] = []
                    fullPathDict[code + nom] = []

                fullPathDict[code + nom].append(full_path)

                for result in results:
                    #if 'Gaz' in nom:
                    #    newV = str(result)

                    try:
                        newV = float(result)
                        newV = str(newV)
                        newV = newV[:-2] # on retire le .0
                    except:
                        newV = '0'
                    valuesDict[code+nom].append(newV)
    if firstTimeRunning:
        combine_images(fullPathDict)
    suffixDict = {}
    # TOPASS : values, image_file, output_csv, yearMonth
    for iteration in range(3):
        if iteration == 0:
            operatingHours = {}
            iterType = 'Heure'
        elif iteration == 1:
            iterType = 'plausible'

        for image_file in image_files:
            try :
                identite, code, nom, dateHeure = get_info_from_name(image_file)
                identite = checkID(identite, data)

                if iteration == 0 and 'Heure' not in nom:
                    continue

                if (iteration == 1 or iteration == 2) and 'Heure' in nom:
                    continue

                if identite[-2] == '=':
                    if code + nom not in suffixDict:
                        suffixDict[code + nom] = [" Prod", " Conso"]
                    suffix = suffixDict[code + nom].pop(0)
                    identite = identite.replace(identite[-2:], suffix)

                # Download image from Dropbox to local folder
                dropbox_image_path = os.path.join(dropbox_folder, image_file).replace("\\","/")
                local_image_path = os.path.join(local_temp_folder, image_file).replace("\\","/")
                full_path = os.path.abspath(local_image_path)
            except:
                continue


            with open(output_csv, 'w', newline='') as csvfile:
                fieldnames = ['num ID', 'unique ID', 'CODE CHAUFFERIE', 'NOM COMPTEUR', 'Date & Heure', 'index m', 'index m-1', 'index m-2', 
                            'Date & Heure 1/4 H', 'index I+', 'index extrapole', 'test I+', 'test passed']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()

                existing_ids = {row['unique ID']: row for row in data}  # A dictionary to store rows by their ID for easy lookup

                IsIn, identite = isInIds(identite, existing_ids)
                if IsIn == False:

                    print('Not In')

                    new_row = {
                        'num ID': '',
                        'unique ID': identite,
                        'CODE CHAUFFERIE': code,
                        'NOM COMPTEUR': nom,
                        'Date & Heure': '',
                        'index m': '',
                        'index m-1': '',
                        'index m-2': '',
                        'Date & Heure 1/4 H': '',
                        'index I+': '',
                        'index extrapole': '',
                        'test I+': '',
                        'test passed': ''
                    }
                    data.append(new_row)
                    existing_ids[identite] = new_row  # Add this new row to the dictionary

                row = existing_ids[identite]

                if is_earlier_or_empty(row['Date & Heure'], dateHeure) or (iteration == 2 and 'Suspect' in row['test passed']): # problème ici : ça écrase les valeurs si on relance le programme

                    if iteration != 2:
                        row = recursiveMoveValue(row, 'index m')

                    if code+nom not in valuesDict:
                        print(identite, "Non lue : Déjà lue précédemment?")
                        continue
                    
                    prevIndex = row['index m-1']
                    prevprevIndex = row['index m-2']

                    dotValues = []
                    extrapolated_value = extrapolate_index(row, operatingHours, code, max_n=2)

                    if extrapolated_value is not None:
                        row['index extrapole'] = extrapolated_value
                        for value in valuesDict[code+nom]:
                            dotValues.append(setDotPosition(value, row, 'index extrapole'))
                        value = closestValue(dotValues, 'index extrapole', row['index m-1'], row)
                        if float(extrapolated_value)*0.9 <= float(value) < float(extrapolated_value)*1.1 and float(value) >= float(prevIndex):
                            row['test passed'] = f'=LIEN_HYPERTEXTE("{full_path}"; "Plausible")'
                        else:
                            row['test passed'] = f'=LIEN_HYPERTEXTE("{full_path}"; "Suspect")'

                    elif prevIndex != '0' and prevIndex != '' and prevIndex != '0.0':
                        floatPrev = float(prevIndex) # to test if float -> otherwize exit try
                    
                        for value in valuesDict[code+nom]:
                            dotValues.append(setDotPosition(value, row, 'index m-1'))
                        value = closestValue(dotValues, 'index m-1', row['index m-1'], row)
                        if float(floatPrev)*1 <= float(value) < float(floatPrev)*1.3:
                            row['test passed'] = f'=LIEN_HYPERTEXTE("{full_path}"; "Plausible")'
                        else:
                            row['test passed'] = f'=LIEN_HYPERTEXTE("{full_path}"; "Suspect")'

                    elif prevprevIndex != '0' and prevprevIndex != '' and prevprevIndex != '0.0':
                        floatPrevPrev = float(prevprevIndex)
                        for value in valuesDict[code+nom]:
                            dotValues.append(setDotPosition(value, row, 'index m-2'))
                            value = closestValue(dotValues, 'index m-2', row['index m-2'], row)
                        if float(floatPrevPrev)*1 <= float(value) < float(floatPrevPrev)*1.6:
                            row['test passed'] = f'=LIEN_HYPERTEXTE("{full_path}"; "Plausible")'
                        else:
                            row['test passed'] = f'=LIEN_HYPERTEXTE("{full_path}"; "Suspect")'
                    else:
                        if len(valuesDict[code+nom]) != 0:
                            value = valuesDict[code+nom][0] #erreur ici, parfois liste vide
                            row['test passed'] = f'=LIEN_HYPERTEXTE("{full_path}"; "Suspect")'
                        else : 
                            value = '0.0' #erreur ici, parfois liste vide
                            row['test passed'] = f'=LIEN_HYPERTEXTE("{full_path}"; "Suspect")'

                
                    
                    value = str(value)
                    if value != '0' and value != '0.0':
                        value = value.lstrip('0')

                    if value == '0' or value == '0.0':
                        row['test passed'] = f'=LIEN_HYPERTEXTE("{full_path}"; "Suspect")'


                    # For Prod/Cons decision
                    retrieveDictVal = None
                    if value[-2:] == '.0':
                        retrieveDictVal = value.replace('.0', '')
                    else:
                        retrieveDictVal = value.replace('.', '')

                    if retrieveDictVal in valuesDict[code+nom] and len(valuesDict[code+nom])>=2:
                        if 'Plausible' in row['test passed']:
                            index = valuesDict[code+nom].index(retrieveDictVal)
                            if index == 0 or index == 1:
                                valuesDict[code+nom] = valuesDict[code+nom][2:]
                                new_full_path = fullPathDict[code + nom][0]
                                fullPathDict[code + nom].pop(0)
                            elif index == 2 or index == 3:
                                valuesDict[code+nom] = valuesDict[code+nom][:2]
                                new_full_path = fullPathDict[code + nom][1]
                                fullPathDict[code + nom].pop(1)
                            row['test passed'] = f'=LIEN_HYPERTEXTE("{new_full_path}"; "Plausible")'
                        
                        else:
                            new_full_path = fullPathDict[code + nom][0]
                            row['test passed'] = f'=LIEN_HYPERTEXTE("{new_full_path}"; "Suspect")'

                    # For heure dict
                    if iterType == 'Heure':
                        if 'Plausible' in row['test passed']:
                            operatingHours[code] = [value, row['index m-1'], row['index m-2']]

                    #value = value.replace('.', ',')
                    row['index m'] = value

                    print(f"Value at index: {row['unique ID']} = {value}")
                    row['Date & Heure'] = translate_datetime(dateHeure)
                    row['Date & Heure 1/4 H'] = mean_datetime(heureList)

                for row in data:
                    filtered_row = {key: row[key] for key in fieldnames if key in row}
                    writer.writerow(filtered_row)

    return
