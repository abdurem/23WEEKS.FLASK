import torch
from torchvision import transforms
from PIL import Image
import io

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model_path = 'app/models/fetal_planes_model.pt'
model = torch.jit.load(model_path, map_location=device)
model.eval()

main_class_names = ['Fetal abdomen', 'Fetal brain', 'Fetal femur', 'Fetal thorax', 'Maternal cervix', 'Other']
brain_class_names = ['Not A Brain', 'Other', 'Trans-cerebellum', 'Trans-thalamic', 'Trans-ventricular']

def preprocess_image(image_bytes):
    transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5]),
    ])
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    return transform(image).unsqueeze(0).to(device)

def process_output(output, class_names):
    probabilities = torch.nn.functional.softmax(output[0], dim=0)
    results = [{"name": name, "probability": float(prob)} for name, prob in zip(class_names, probabilities)]
    results.sort(key=lambda x: x['probability'], reverse=True)
    return results

def classify_image(image_bytes):
    try:
        input_tensor = preprocess_image(image_bytes)
        with torch.no_grad():
            main_output, brain_output = model(input_tensor)
        main_results = process_output(main_output, main_class_names)
        brain_results = process_output(brain_output, brain_class_names)
        main_class = main_results[0]['name']
        response = {
            "mainClassification": {
                "mainClass": main_class,
                "accuracy": main_results[0]['probability'],
                "allClasses": main_results
            },
            "brainClassification": {
                "mainClass": brain_results[0]['name'],
                "accuracy": brain_results[0]['probability'],
                "allClasses": brain_results
            } if main_class == 'Fetal brain' else None
        }
        return response
    except Exception as e:
        raise e
