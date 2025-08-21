import os
from groundingdino.util.inference import load_model, load_image, predict, annotate
import cv2
import numpy as np
import torch
import io
import imutils

import warnings
warnings.filterwarnings("ignore")

def preProcessing(image_path, height = False, alpha = 1, beta = 0):

    # Specify that you want to use the CPU
    #model = load_model("C:/Users/brieu/AppData/Local/Programs/Python/Python39/Lib/site-packages/groundingdino/config/GroundingDINO_SwinT_OGC.py", "groundingdino_swint_ogc.pth", device='cpu')
    model = load_model("dino_config.py", "groundingdino_swint_ogc.pth", device='cpu')
    IMAGE_PATH = image_path
    #TEXT_PROMPT = "digital screen display . electronic device"
    #TEXT_PROMPT = "white counter value on black background . electronic device"

    TEXT_PROMPT = "digital screen display . electronic device"
    BOX_TRESHOLD = 0.2 #0.35
    TEXT_TRESHOLD = 0.15 #0.25

    image_source, image = load_image(IMAGE_PATH)
    image_height, image_width = image_source.shape[:2]

    boxes, logits, phrases = predict(
        model=model,
        image=image,
        caption=TEXT_PROMPT,
        box_threshold=BOX_TRESHOLD,
        text_threshold=TEXT_TRESHOLD
    )
    roi = {}

    # Check if the boxes are normalized [center_x, center_y, width, height]
    if boxes.shape[1] == 4:
        # Convert from [center_x, center_y, width, height] to [x1, y1, x2, y2]
        cx, cy, w, h = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        x1 = cx - 0.5 * w
        y1 = cy - 0.5 * h
        x2 = cx + 0.5 * w
        y2 = cy + 0.5 * h
        boxesBIS = torch.stack([x1, y1, x2, y2], dim=1)

    # Identify the box corresponding to 'numerical display'
    best_idx = None
    smallestArea = float(np.inf)
    for idx, phrase in enumerate(phrases):
        area = boxes[idx][2]*boxes[idx][3]
        if "digital screen display" in phrase.lower() and area < smallestArea:
            smallestArea = area
            best_idx = idx

    # Check if 'numerical display' was found
    if best_idx is not None:
        # Get the best box
        best_box = boxesBIS[best_idx]

        # Convert the best box to pixel coordinates
        x1, y1, x2, y2 = best_box
        x1 = int(x1 * image_width)
        y1 = int(y1 * image_height)
        x2 = int(x2 * image_width)
        y2 = int(y2 * image_height)

        # Ensure the coordinates are correct
        X1 = min(x1, x2)
        X2 = max(x1, x2)
        Y1 = min(y1, y2)
        Y2 = max(y1, y2)

        roi = {"x_min": X1, "y_min": Y1, "x_max": X2, "y_max": Y2}

        # Crop the image based on the best bounding box
        cropped_image = image_source[Y1:Y2, X1:X2]
        heightCropped, widthCropped = cropped_image.shape[:2]
        if heightCropped < 100:
            cropped_image = imutils.resize(cropped_image, height=100, inter=cv2.INTER_CUBIC) #100 ? random value
        if height != False:
            cropped_image = imutils.resize(cropped_image, height=height, inter=cv2.INTER_CUBIC)
            cropped_image = cv2.addWeighted(cropped_image, alpha, cropped_image, 0, beta)
        
        



        # define the alpha and beta
        #alpha = 1.5 # Contrast control
        #beta = -20 # Brightness control

        # call convertScaleAbs function
        #cropped_image = cv2.convertScaleAbs(cropped_image, alpha=alpha, beta=beta)

        
        #cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        #cropped_image = cv2.GaussianBlur(cropped_image, (3, 3), 0)
        #cropped_image = cv2.adaptiveThreshold(cropped_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        cropped_images_dir = "cropped_images"
        os.makedirs(cropped_images_dir, exist_ok=True)

        # Save the cropped image
        name = 'crop.jpg'
        cropped_image_path = os.path.join(cropped_images_dir, name)
        cropped_image_path = f'{cropped_images_dir}/{name}'
        cv2.imwrite(cropped_image_path, cropped_image)

        print(f"Saved cropped image for 'numerical display': {cropped_image_path}")
    else:
        pass
        #print("No 'numerical display' found in the detected phrases.")

    # Optionally, save the annotated image
    annotated_frame = annotate(image_source=image_source, boxes=boxes, logits=logits, phrases=phrases)
    annotated_name = "annotated_image.jpg"
    cv2.imwrite(annotated_name, annotated_frame)
    print("Saved annotated image: annotated_image.jpg")
    # Step 1: Encode the matrix to an image format using OpenCV
    _, encoded_image = cv2.imencode('.jpg', cropped_image)  # .png, .jpg, etc.

    # Step 2: Convert the encoded image to a byte stream
    byte_stream = io.BytesIO(encoded_image.tobytes())
    return cropped_image_path, roi


#preProcessing('img\gaz\IMG-20240817-WA0004.jpg', 'gaz.jpg')