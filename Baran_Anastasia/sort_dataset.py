import os
import shutil

SOURCE_FOLDER = "Audio_Speech_Actors_01-24"
DEST_FOLDER = "dataset"

emotion_map = {
    "01": "neutral",
    "03": "happy",
    "04": "sad",
    "05": "angry",
    "06": "fear",
    "07": "disgust"
}

# створення папок
for emotion in emotion_map.values():
    os.makedirs(os.path.join(DEST_FOLDER, emotion), exist_ok=True)

count = 0

# прохід по actor папках
for actor_folder in os.listdir(SOURCE_FOLDER):

    actor_path = os.path.join(SOURCE_FOLDER, actor_folder)

    if os.path.isdir(actor_path):

        for file in os.listdir(actor_path):

            if file.endswith(".wav"):

                parts = file.split("-")

                emotion_code = parts[2]

                if emotion_code in emotion_map:

                    emotion_name = emotion_map[emotion_code]

                    src = os.path.join(actor_path, file)

                    dst = os.path.join(
                        DEST_FOLDER,
                        emotion_name,
                        file
                    )

                    shutil.copy2(src, dst)

                    count += 1

print(f"DONE Copied {count} files")