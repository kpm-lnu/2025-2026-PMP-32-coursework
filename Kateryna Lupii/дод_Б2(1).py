import os
import pandas as pd
import matplotlib.pyplot as plt

"""
Скрипт будує графіки навчання (loss / accuracy) на основі CSV-логів експериментів.

Очікувана структура папок:
logs/
  exp1_depth/
    model_2blocks.csv
    model_4blocks.csv
  exp2_hparams/
    lr_0.001_bs_64.csv
    ...
  exp3_regularization/
    dropout_0.5.csv
    ...
  exp4_augmentation/
    no_aug.csv
    basic_aug.csv
    ...
  exp5_transfer/
    from_scratch.csv
    transfer_learning.csv

Формат CSV:
epoch,train_loss,val_loss,train_acc,val_acc
1,1.82,1.75,0.31,0.33
2,1.45,1.39,0.47,0.49
...
"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
OUT_DIR = os.path.join(BASE_DIR, "generated_graphs")
os.makedirs(OUT_DIR, exist_ok=True)

EXPERIMENTS = {
    "exp1_depth": ("Б.1", "Б.2", "Експеримент 1 - Вплив глибини мережі"),
    "exp2_hparams": ("Б.3", "Б.4", "Експеримент 2 - Вплив гіперпараметрів навчання"),
    "exp3_regularization": ("Б.5", "Б.6", "Експеримент 3 - Вплив методів регуляризації"),
    "exp4_augmentation": ("Б.7", "Б.8", "Експеримент 4 - Вплив аугментації даних"),
    "exp5_transfer": ("Б.9", "Б.10", "Експеримент 5 - Transfer Learning та порівняння з нуля"),
}

def plot_metric(exp_folder, fig_loss_no, fig_acc_no, title):
    folder_path = os.path.join(LOGS_DIR, exp_folder)
    if not os.path.isdir(folder_path):
        print(f"Папка не знайдена: {folder_path}")
        return

    csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]
    if not csv_files:
        print(f"У папці {folder_path} немає CSV-файлів.")
        return

    # LOSS
    plt.figure(figsize=(10, 6))
    for csv_file in csv_files:
        path = os.path.join(folder_path, csv_file)
        df = pd.read_csv(path)
        label = os.path.splitext(csv_file)[0]
        plt.plot(df["epoch"], df["train_loss"], label=f"{label} - train")
        plt.plot(df["epoch"], df["val_loss"], linestyle="--", label=f"{label} - val")
    plt.xlabel("Епоха")
    plt.ylabel("Loss")
    plt.title(f"{title}: loss")
    plt.legend(fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    loss_path = os.path.join(OUT_DIR, f"fig_{fig_loss_no}_loss.png")
    plt.savefig(loss_path, dpi=200)
    plt.close()

    # ACC
    plt.figure(figsize=(10, 6))
    for csv_file in csv_files:
        path = os.path.join(folder_path, csv_file)
        df = pd.read_csv(path)
        label = os.path.splitext(csv_file)[0]
        plt.plot(df["epoch"], df["train_acc"], label=f"{label} - train")
        plt.plot(df["epoch"], df["val_acc"], linestyle="--", label=f"{label} - val")
    plt.xlabel("Епоха")
    plt.ylabel("Accuracy")
    plt.title(f"{title}: accuracy")
    plt.legend(fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    acc_path = os.path.join(OUT_DIR, f"fig_{fig_acc_no}_accuracy.png")
    plt.savefig(acc_path, dpi=200)
    plt.close()

    print(f"Створено: {loss_path}")
    print(f"Створено: {acc_path}")

if __name__ == "__main__":
    for folder, values in EXPERIMENTS.items():
        plot_metric(folder, *values)
