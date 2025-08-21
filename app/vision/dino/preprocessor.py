import os
import io
import cv2
import numpy as np
import torch
import imutils
import warnings
from groundingdino.util.inference import load_model, load_image, predict, annotate
from app import config

warnings.filterwarnings("ignore")

def preProcessing(image_path, height = False, alpha = 1, beta = 0):
    model = load_model(config.DINO_CONFIG_PATH, config.DINO_MODEL_PATH, device='cpu')
    image_source, image = load_image(image_path)
    image_height, image_width = image_source.shape[:2]
    boxes, logits, phrases = predict(
        model=model,
        image=image,
        caption=config.TEXT_PROMPT,
        box_threshold=config.BOX_THRESHOLD,
        text_threshold=config.TEXT_THRESHOLD
    )
    roi = {}
    if boxes.shape[1] == 4:
        cx, cy, w, h = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        x1 = cx - 0.5 * w
        y1 = cy - 0.5 * h
        x2 = cx + 0.5 * w
        y2 = cy + 0.5 * h
        boxesBIS = torch.stack([x1, y1, x2, y2], dim=1)
    best_idx = None
    smallestArea = float(np.inf)
    for idx, phrase in enumerate(phrases):
        area = boxes[idx][2]*boxes[idx][3]
        if "digital screen display" in phrase.lower() and area < smallestArea:
            smallestArea = area
            best_idx = idx
    if best_idx is not None:
        best_box = boxesBIS[best_idx]
        x1, y1, x2, y2 = best_box
        x1 = int(x1 * image_width)
        y1 = int(y1 * image_height)
        x2 = int(x2 * image_width)
        y2 = int(y2 * image_height)
        X1 = min(x1, x2)
        X2 = max(x1, x2)
        Y1 = min(y1, y2)
        Y2 = max(y1, y2)
        roi = {"x_min": X1, "y_min": Y1, "x_max": X2, "y_max": Y2}
        cropped_image = image_source[Y1:Y2, X1:X2]
        heightCropped, widthCropped = cropped_image.shape[:2]
        if heightCropped < 100:
            cropped_image = imutils.resize(cropped_image, height=100, inter=cv2.INTER_CUBIC)
        if height != False:
            cropped_image = imutils.resize(cropped_image, height=height, inter=cv2.INTER_CUBIC)
            cropped_image = cv2.addWeighted(cropped_image, alpha, cropped_image, 0, beta)
        os.makedirs(config.CROPPED_IMAGES_DIR, exist_ok=True)
        cropped_image_path = os.path.join(config.CROPPED_IMAGES_DIR, 'crop.jpg')
        cv2.imwrite(cropped_image_path, cropped_image)
        print(f"Saved cropped image for 'numerical display': {cropped_image_path}")
    else:
        pass
    annotated_frame = annotate(image_source=image_source, boxes=boxes, logits=logits, phrases=phrases)
    annotated_name = "annotated_image.jpg"
    annotated_path = os.path.join(config.ANNOTATED_TESTS_DIR, annotated_name)
    cv2.imwrite(annotated_path, annotated_frame)
    print(f"Saved annotated image: {annotated_path}")
    _, encoded_image = cv2.imencode('.jpg', cropped_image)
    byte_stream = io.BytesIO(encoded_image.tobytes())
    return cropped_image_path, roi