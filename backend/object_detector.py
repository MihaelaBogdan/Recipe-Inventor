import io
import os
from PIL import Image

COCO_FOOD_MAPPING = {
    "banana": "banane",
    "apple": "mere",
    "sandwich": "paine",
    "orange": "portocale",
    "broccoli": "broccoli",
    "carrot": "morcovi",
    "hot dog": "carnati",
    "pizza": "pizza",
    "donut": "zahar",
    "cake": "faina",
    "bottle": "lapte",
    "wine glass": "vin",
    "cup": "apa",
    "bowl": "orez",
}

class IngredientDetector:
    def __init__(self):
        self.model = None

    def _load_model(self):
        if self.model is None:
            # Prevent excessive YOLO output logs
            os.environ["YOLO_VERBOSE"] = "False"
            from ultralytics import YOLO
            self.model = YOLO("yolov8n.pt")

    def detect_ingredients(self, image_bytes: bytes) -> list[str]:
        self._load_model()
        try:
            image = Image.open(io.BytesIO(image_bytes))
            results = self.model(image, verbose=False)
            
            detected = []
            if results and len(results) > 0:
                for box in results[0].boxes:
                    cls_id = int(box.cls[0].item())
                    name = self.model.names[cls_id].lower()
                    
                    # Map COCO labels to ingredients in our recipe dataset
                    mapped = COCO_FOOD_MAPPING.get(name)
                    if mapped and mapped not in detected:
                        detected.append(mapped)
            return detected
        except Exception as e:
            print(f"Error in object detection: {e}")
            return []

# Singleton instance
DETECTOR = IngredientDetector()
