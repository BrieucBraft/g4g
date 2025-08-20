from ultralytics import YOLO
import cv2
import os

script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the current script (yoloGaz.py)

# Load the trained model
model = YOLO(os.path.join(script_dir, "ObjectDetection/last.pt"))



def mainGaz(image_path):
    # Prepare a list to collect results
    results = []
        
    # Call yoloROI function
    detected_number = yoloROI(image_path, "annotated")

    # Append result to the list
    results.append(str(detected_number))
    
    return results


def compute_iou(box1, box2):
    x1, y1, x2, y2 = box1
    x1_p, y1_p, x2_p, y2_p = box2
    
    # Compute the intersection
    xi1 = max(x1, x1_p)
    yi1 = max(y1, y1_p)
    xi2 = min(x2, x2_p)
    yi2 = min(y2, y2_p)
    
    # Compute area of intersection
    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    
    # Compute area of each box
    box1_area = (x2 - x1) * (y2 - y1)
    box2_area = (x2_p - x1_p) * (y2_p - y1_p)
    
    # Compute IoU
    iou = inter_area / (box1_area + box2_area - inter_area)
    return iou

def yoloROI(img_path, save_name, iou_threshold=0.5):
    img = cv2.imread(img_path)

    # Perform inference
    results = model(img)

    # Access the bounding boxes
    boxes = results[0].boxes  # Get boxes from the first image in batch
    detected_digits = []  # List to store detected digits with their bounding boxes and confidences

    # Loop through the detected boxes
    for i, box in enumerate(boxes):
        class_id = int(box.cls[0])  # Get the class ID
        confidence = box.conf[0]  # Get the confidence score
        x1, y1, x2, y2 = box.xyxy[0].tolist()  # Get the bounding box coordinates

        if 0 <= class_id <= 9:
            detected_digits.append((class_id, confidence, x1, y1, x2, y2))  # Store digit, confidence, and bbox

    # Filter overlapping boxes
    filtered_digits = []
    while detected_digits:
        # Get the box with the highest confidence
        detected_digits.sort(key=lambda x: x[1], reverse=True)
        top_digit = detected_digits.pop(0)
        top_class_id, top_confidence, top_x1, top_y1, top_x2, top_y2 = top_digit

        # Add it to the filtered list
        filtered_digits.append(top_digit)

        # Remove boxes that overlap too much with the top box
        new_detected_digits = []
        for digit in detected_digits:
            _, _, x1, y1, x2, y2 = digit
            iou = compute_iou((top_x1, top_y1, top_x2, top_y2), (x1, y1, x2, y2))
            if iou < iou_threshold:  # Keep boxes that don't overlap too much
                new_detected_digits.append(digit)
        detected_digits = new_detected_digits

    # Sort filtered digits based on their x-coordinate (x1) to read from left to right
    filtered_digits.sort(key=lambda x: x[2])

    # Concatenate the digits into a single string
    number_string = ''.join([str(digit[0]) for digit in filtered_digits])

    #print(f"Detected number (left to right): {number_string}")

    # Draw the bounding boxes and labels on the image
    for class_id, confidence, x1, y1, x2, y2 in filtered_digits:
        # Draw the bounding box
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

        # Put the digit label on the image
        label = f"{class_id} ({confidence:.2f})"
        cv2.putText(img, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

    # Save the annotated image in the /test folder
    os.makedirs('tests', exist_ok=True)  # Ensure the test folder exists
    output_path = f'tests/{save_name}.jpg'
    cv2.imwrite(output_path, img)
    #print(f"Annotated image saved at: {output_path}")
    return number_string

