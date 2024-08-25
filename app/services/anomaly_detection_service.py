# import argparse
# import cv2
# import numpy as np
# import onnxruntime as ort
# import traceback
# from PIL import Image, ImageDraw
# from io import BytesIO

# # Existing functions retained from your work
# def load_detection_model():
#     try:
#         model_path = 'app/models/Anomaly.onnx'
#         session = ort.InferenceSession(model_path)
#         print("Model loaded successfully.")
#         return session
#     except Exception as e:
#         print(f"Error loading model: {str(e)}")
#         traceback.print_exc()
#         raise

# def detect_image(image_bytes):
#     try:
#         # Instantiate the Yolov8 class
#         yolov8_detector = Yolov8(
#             onnx_model='app/models/Anomaly.onnx', 
#             input_image=None,  # We won't use file paths here, just image bytes
#             confidence_thres=0.2, 
#             iou_thres=0.4
#         )
        
#         print("Loading model...")
#         model = load_detection_model()
#         if model is None:
#             raise ValueError("Model is not loaded properly.")
        
#         print("Starting image detection...")
        
#         # Use the preprocess_image method from the Yolov8 class
#         yolov8_detector.input_image = Image.open(BytesIO(image_bytes)).convert('RGB')
#         input_array = yolov8_detector.preprocess()

#         if input_array is None:
#             raise ValueError("Image preprocessing failed.")
        
#         print(f"Input array shape: {input_array.shape}")

#         input_name = model.get_inputs()[0].name
#         output_names = [output.name for output in model.get_outputs()]
#         results = model.run(output_names, {input_name: input_array})

#         output_array = results[0]
#         print(f"Output array shape: {output_array.shape}")

#         detected_image = yolov8_detector.postprocess(yolov8_detector.img, output_array)
        
#         detected_image_bytes = BytesIO()
#         Image.fromarray(cv2.cvtColor(detected_image, cv2.COLOR_BGR2RGB)).save(detected_image_bytes, format='PNG')
#         detected_image_bytes.seek(0)

#         return detected_image_bytes

#     except Exception as e:
#         print(f"Error in detect_image: {str(e)}")
#         traceback.print_exc()
#         return None

# # Yolov8 class based on the provided code
# class Yolov8:
#     def __init__(self, onnx_model, input_image, confidence_thres, iou_thres):
#         self.onnx_model = onnx_model
#         self.input_image = input_image
#         self.confidence_thres = confidence_thres
#         self.iou_thres = iou_thres

#         # Define the expected input dimensions (width and height) for the model
#         self.input_width = 800  # Update if your model expects a different size
#         self.input_height = 800  # Update if your model expects a different size

#         # Load the class names from the COCO dataset
#         self.classes = ['CSP', 'LV']  # Adjusted for your use case

#         # Generate a color palette for the classes
#         self.color_palette = np.random.uniform(0, 255, size=(len(self.classes), 3))

#     def draw_detections(self, img, box, score, class_id):
#         color = self.color_palette[class_id]
#         x1, y1, w, h = box
#         cv2.rectangle(img, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), color, 2)
#         label = f'{self.classes[class_id]}: {score:.2f}'
#         (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
#         label_x = x1
#         label_y = y1 - 10 if y1 - 10 > label_height else y1 + 10
#         cv2.rectangle(img, (label_x, label_y - label_height), (label_x + label_width, label_y + label_height), color, cv2.FILLED)
#         cv2.putText(img, label, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

#     def preprocess(self):
#         self.img = np.array(self.input_image)
#         self.img_height, self.img_width = self.img.shape[:2]
#         img = cv2.cvtColor(self.img, cv2.COLOR_RGB2BGR)
#         img = cv2.resize(img, (self.input_width, self.input_height))
#         image_data = np.array(img) / 255.0
#         image_data = np.transpose(image_data, (2, 0, 1))  # Channel first
#         image_data = np.expand_dims(image_data, axis=0).astype(np.float32)
#         return image_data

#     def postprocess(self, input_image, output):
#         outputs = np.transpose(np.squeeze(output[0]))
#         rows = outputs.shape[0]
#         boxes = []
#         scores = []
#         class_ids = []
#         x_factor = self.img_width / self.input_width
#         y_factor = self.img_height / self.input_height

#         for i in range(rows):
#             classes_scores = outputs[i][4:]
#             max_score = np.amax(classes_scores)
#             if max_score >= self.confidence_thres:
#                 class_id = np.argmax(classes_scores)
#                 x, y, w, h = outputs[i][0], outputs[i][1], outputs[i][2], outputs[i][3]
#                 left = int((x - w / 2) * x_factor)
#                 top = int((y - h / 2) * y_factor)
#                 width = int(w * x_factor)
#                 height = int(h * y_factor)
#                 class_ids.append(class_id)
#                 scores.append(max_score)
#                 boxes.append([left, top, width, height])

#         indices = cv2.dnn.NMSBoxes(boxes, scores, self.confidence_thres, self.iou_thres)
#         # Check if indices are valid and not empty
#         if len(indices) > 0:
#             for i in indices.flatten():
#                 box = boxes[i]
#                 score = scores[i]
#                 class_id = class_ids[i]
#                 self.draw_detections(input_image, box, score, class_id)

#         return input_image
