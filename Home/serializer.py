from rest_framework import serializers
from .models import CityMonitoring, Department
from PIL import Image
import os
import uuid
from ultralytics import YOLO
import time
from django.conf import settings
from django.core.files.base import ContentFile

# Lazy-load YOLO model
model = None

def get_yolo_model():
    global model
    if model is None:
        model_path = os.path.join(os.path.dirname(__file__), 'epoch80.pt')
        try:
            model = YOLO(model_path)
            print("🔍 Model class names:", model.names)
        except Exception as e:
            print(f"Failed to load YOLO model: {str(e)}")
            raise
    return model

LABELS_MAP = {
    'Traffic': ['encroachment', 'manholes','pothholes','crack'],
    'Animal': ['cattles'],  # Fixed from 'cattles' to match model.names
    'Sanitation': ['garbage', 'trashcan']
}

def detect_and_crop(image_path):
    print(f"🔍 Detecting objects in image: {image_path}")
    try:
        model = get_yolo_model()
        results = model(image_path, conf=0.2)
        img = Image.open(image_path)
        all_labels = [label for labels in LABELS_MAP.values() for label in labels]
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls)
                cls_name = model.names[cls_id].lower()
                conf = box.conf.item()
                print(f"Detected class: {cls_name} (id {cls_id}), confidence: {conf}")
                if cls_name in all_labels:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    print(f"Cropping box coordinates: {(x1, y1, x2, y2)}")
                    cropped = img.crop((x1, y1, x2, y2))
                    filename = f"{os.path.basename(image_path).split('.')[0]}_{uuid.uuid4().hex[:8]}.jpg"
                    save_dir = os.path.join(settings.MEDIA_ROOT, 'cropped_objects')
                    os.makedirs(save_dir, exist_ok=True)
                    save_path = os.path.join(save_dir, filename)
                    cropped.save(save_path)
                    print(f"Cropped image saved at: {save_path}")
                    with open(save_path, 'rb') as f:
                        cropped_file = ContentFile(f.read(), name=filename)
                    return cropped_file, cls_name
        print("No matching detection found.")
        return None, None
    except Exception as e:
        print(f"Error during object detection: {str(e)}")
        return None, None

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class CityMonitoringSerializer(serializers.ModelSerializer):
    department = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Department.objects.all(),
        required=False  # Allow automatic assignment
    )
    photo_url = serializers.SerializerMethodField()
    identify_object_url = serializers.SerializerMethodField()
    location_link = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()
    identify_object = serializers.ImageField(read_only=True)  # Mark as read-only

    class Meta:
        model = CityMonitoring
        fields = '__all__'
        read_only_fields = ('reported_on', 'identify_object')  # Ensure identify_object is read-only

    def validate_photo(self, value):
        if not value:
            raise serializers.ValidationError("A valid image file is required.")
        if not value.content_type.startswith('image/'):
            raise serializers.ValidationError("The uploaded file must be an image (e.g., .jpg, .png).")
        return value

    def get_photo_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.photo.url) if obj.photo else None

    def get_identify_object_url(self, obj):
        request = self.context.get('request')
        if obj.identify_object:
            url = request.build_absolute_uri(obj.identify_object.url)
            url = url.replace("127.0.0.1", "localhost")
            url += f"?v={int(obj.updated_at.timestamp()) if hasattr(obj, 'updated_at') else int(time.time())}"
            return url
        return None

    def get_location_link(self, obj):
        return f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"

    def get_actions(self, obj):
        return {
            'edit': f"/api/city-monitoring/{obj.id}/",
            'delete': f"/api/city-monitoring/{obj.id}/"
        }

    def create(self, validated_data):
        instance = super().create(validated_data)
        self.process_identify_object(instance)
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self.process_identify_object(instance)
        return instance

    def process_identify_object(self, instance):
        if not instance.photo or not hasattr(instance.photo, 'path'):
            print("No valid photo provided for object detection.")
            return
        image_path = instance.photo.path
        cropped_file, detected_class = detect_and_crop(image_path)
        if cropped_file and detected_class:
            instance.identify_object = cropped_file
            for dept_name, labels in LABELS_MAP.items():
                if detected_class in labels:
                    try:
                        department = Department.objects.get(name=dept_name)
                        instance.department = department
                        print(f"Automatically assigned department: {dept_name} for detected class: {detected_class}")
                        break
                    except Department.DoesNotExist:
                        print(f"Department {dept_name} not found in database.")
            instance.save()
        else:
            print("No valid detection found; department not updated.")