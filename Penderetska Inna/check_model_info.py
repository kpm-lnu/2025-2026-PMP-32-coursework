from ultralytics import YOLO

# Шлях до твоїх збережених ваг
model = YOLO('runs/detect/drone_final_results-2/weights/best.pt')

# Отримуємо словник класів
class_dict = model.names

print("\n" + "="*40)
print(f" Назва завдання: {model.task}")
print(f" Кількість класів: {len(class_dict)}")
print(f" Імена класів: {list(class_dict.values())}")
print(f" Кількість параметрів: {sum(p.numel() for p in model.model.parameters()):,}")
print("="*40 + "\n")