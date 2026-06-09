import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as T
from timeit import default_timer
import os

device = 'cpu'
classes = ['Heart', 'Oblong', 'Oval', 'Round', 'Square']

def load_face_model(weight_path="weights/shape_face.pth"):
    # 1. Lấy thư mục chứa file face_shape_detector.py hiện tại
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Ghép với tên thư mục weights để ra đường dẫn tuyệt đối (C:\Users\...)
    absolute_weight_path = os.path.join(current_dir, weight_path)
    
    # 3. Load model bằng đường dẫn tuyệt đối vừa tạo
    weights = torch.load(absolute_weight_path, map_location=torch.device('cpu'))

def get_face_shape(
    model: torch.nn.Module,
    class_names,
    image_path: str,
    image_size = (224, 224),
    transform: torchvision.transforms = None,
    device: torch.device = device):

    img = Image.open(image_path)
    img = img.convert("RGB")
    if transform is not None:
        image_transform = transform
    else:
        image_transform = T.Compose([T.Resize(image_size),
                                    T.ToTensor(),
                                    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                                    ])

    model.eval()
    with torch.inference_mode():
        transformed_image = image_transform(img).unsqueeze(dim=0)
        target_image_pred = model(transformed_image.to(device))

    target_image_pred_probs = torch.softmax(target_image_pred, dim=1)
    target_image_pred_label = torch.argmax(target_image_pred_probs, dim=1).item()  # .item() → Python int

    best_class = class_names[target_image_pred_label]
    best_prob   = target_image_pred_probs.max().item()
    all_probs   = dict(zip(class_names, target_image_pred_probs[0].tolist()))

    print(f'[DEBUG] Best: {best_class} | Probability: {best_prob:.4f}')
    print(f'[DEBUG] All probs: {all_probs}')

    # Luôn trả về class có xác suất cao nhất, không dùng ngưỡng cứng
    return best_class
    
def main():
    img_path = 'D:\modelkhnt\skincolor.jpg'
    # start = default_timer()
    model = load_face_model()
    print('Load success')
    type = get_face_shape(model, class_names=classes, image_path=img_path)
    # end = default_timer()
    # print(f"Predict time: {end - start:.2f} seconds")
    
# if __name__ == '__main__':
    # main()