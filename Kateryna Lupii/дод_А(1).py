import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
import matplotlib.pyplot as plt
import csv
import os

# =========================
# 1. Підготовка даних
# =========================
torch.manual_seed(42)

transform_train = transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.RandomCrop(32, padding=4),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465),
                         (0.2470, 0.2435, 0.2616))
])

transform_test = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465),
                         (0.2470, 0.2435, 0.2616))
])

train_dataset = torchvision.datasets.CIFAR10(
    root='./data', train=True, download=True, transform=transform_train)
test_dataset = torchvision.datasets.CIFAR10(
    root='./data', train=False, download=True, transform=transform_test)

train_loader = torch.utils.data.DataLoader(
    train_dataset, batch_size=64, shuffle=True)
test_loader = torch.utils.data.DataLoader(
    test_dataset, batch_size=64, shuffle=False)

classes = ['airplane', 'car', 'bird', 'cat', 'deer',
           'dog', 'frog', 'horse', 'ship', 'truck']


# =========================
# 2. Власна модифікована CNN
# =========================
class ImprovedCNN(nn.Module):
    """
    Модифікована архітектура CNN із:
    - Batch Normalization після кожного Conv2d
    - Двостадійним Dropout (p=0.3 та p=0.5)
    - Розширеним FC-шаром (512 нейронів)
    """
    def __init__(self):
        super(ImprovedCNN, self).__init__()
        # Блок 1: Conv -> BN -> ReLU -> Pool
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.bn1   = nn.BatchNorm2d(32)
        # Блок 2: Conv -> BN -> ReLU -> Pool
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2   = nn.BatchNorm2d(64)

        self.pool  = nn.MaxPool2d(2, 2)

        # Класифікатор з двостадійним Dropout
        self.fc1   = nn.Linear(64 * 8 * 8, 512)
        self.drop1 = nn.Dropout(0.3)
        self.fc2   = nn.Linear(512, 10)
        self.drop2 = nn.Dropout(0.5)

    def forward(self, x):
        x = self.pool(torch.relu(self.bn1(self.conv1(x))))
        x = self.pool(torch.relu(self.bn2(self.conv2(x))))
        x = x.view(-1, 64 * 8 * 8)
        x = self.drop1(torch.relu(self.fc1(x)))
        x = self.drop2(self.fc2(x))
        return x


# =========================
# 3. Ініціалізація
# =========================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Пристрій: {device}")

model = ImprovedCNN().to(device)

# Підрахунок параметрів
total_params = sum(p.numel() for p in model.parameters())
print(f"Загальна кількість параметрів: {total_params:,}")

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)


# =========================
# 4. Навчання з CSV-логуванням
# =========================
epochs = 10
log_path = "training_log.csv"
best_val_acc = 0.0

train_losses = []
val_losses   = []
train_accs   = []
val_accs     = []

with open(log_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['epoch', 'train_loss', 'val_loss', 'train_acc', 'val_acc'])

for epoch in range(epochs):
    # --- Навчання ---
    model.train()
    running_loss, correct_train, total_train = 0.0, 0, 0

    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total_train += labels.size(0)
        correct_train += (predicted == labels).sum().item()

    train_loss = running_loss / len(train_loader)
    train_acc  = correct_train / total_train

    # --- Валідація ---
    model.eval()
    val_loss_sum, correct_val, total_val = 0.0, 0, 0

    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            val_loss_sum += loss.item()
            _, predicted = torch.max(outputs, 1)
            total_val += labels.size(0)
            correct_val += (predicted == labels).sum().item()

    val_loss = val_loss_sum / len(test_loader)
    val_acc  = correct_val / total_val

    # Зберігаємо метрики для графіків
    train_losses.append(train_loss)
    val_losses.append(val_loss)
    train_accs.append(train_acc)
    val_accs.append(val_acc)

    # Зберігаємо найкращу модель
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), 'best_model.pth')

    print(f"Епоха {epoch+1}/{epochs} | "
          f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | "
          f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")

    with open(log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([epoch+1,
                         round(train_loss, 4),
                         round(val_loss, 4),
                         round(train_acc, 4),
                         round(val_acc, 4)])

print(f"\nНайкраща Val Accuracy: {best_val_acc*100:.2f}%")
print(f"Лог навчання збережено: {log_path}")


# =========================
# 5. Графіки навчання (Loss та Accuracy)
# =========================
epochs_range = range(1, epochs + 1)

# Графік Loss
plt.figure(figsize=(10, 5))
plt.plot(epochs_range, train_losses, label='Train Loss')
plt.plot(epochs_range, val_losses,   label='Val Loss', linestyle='--')
plt.xlabel('Епоха')
plt.ylabel('Loss')
plt.title('Криві втрат (Loss) — ImprovedCNN')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('training_loss.png', dpi=200)
plt.close()
print("Графік loss збережено: training_loss.png")

# Графік Accuracy
plt.figure(figsize=(10, 5))
plt.plot(epochs_range, train_accs, label='Train Accuracy')
plt.plot(epochs_range, val_accs,   label='Val Accuracy', linestyle='--')
plt.xlabel('Епоха')
plt.ylabel('Accuracy')
plt.title('Криві точності (Accuracy) — ImprovedCNN')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('training_accuracy.png', dpi=200)
plt.close()
print("Графік accuracy збережено: training_accuracy.png")


# =========================
# 6. Оцінка моделі (Confusion Matrix + Report)
# =========================
model.load_state_dict(torch.load('best_model.pth'))
model.eval()

all_preds, all_labels = [], []

with torch.no_grad():
    for images, labels in test_loader:
        outputs = model(images.to(device))
        _, preds = torch.max(outputs, 1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.numpy())

cm     = confusion_matrix(all_labels, all_preds)
report = classification_report(all_labels, all_preds, target_names=classes)

print("\nClassification Report:\n", report)

# Теплова карта матриці помилок
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=classes, yticklabels=classes)
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix — ImprovedCNN')
plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=200)
plt.close()
print("Матрицю помилок збережено: confusion_matrix.png")


# =========================
# 7. Приклади роботи моделі
# =========================
# Зворотна нормалізація для відображення зображень
mean = (0.4914, 0.4822, 0.4465)
std  = (0.2470, 0.2435, 0.2616)

images, labels = next(iter(test_loader))
images_device = images.to(device)

with torch.no_grad():
    outputs = model(images_device)
    _, preds = torch.max(outputs, 1)

for i in range(5):
    img = images[i].clone()

    # Зворотна нормалізація
    for c in range(3):
        img[c] = img[c] * std[c] + mean[c]

    img = img.permute(1, 2, 0).cpu().numpy()
    img = img.clip(0, 1)

    true_class = classes[labels[i].item()]
    predicted_class = classes[preds[i].item()]

    plt.figure(figsize=(3, 3))
    plt.imshow(img)
    plt.title(f"True: {true_class}\nPred: {predicted_class}",
              color='green' if true_class == predicted_class else 'red')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(f"example_{i}.png", dpi=200, bbox_inches='tight')
    plt.close()

    print(f"example_{i}.png: Реальний = {true_class}, "
          f"Прогноз = {predicted_class} "
          f"{'✓' if true_class == predicted_class else '✗'}")

print("\nГотово! Збережені файли:")
print("  training_log.csv      — лог навчання")
print("  training_loss.png     — графік loss")
print("  training_accuracy.png — графік accuracy")
print("  confusion_matrix.png  — матриця помилок")
print("  example_0..4.png      — приклади класифікацій")