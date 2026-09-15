import os
import re
from pathlib import Path

# С какой цифры начинать
START_NUMBER = 1

# Папка с файлами: "." = текущая папка
FOLDER = Path(".")

# Ищем файлы вида:
# photo_1_2026-03-29_14-47-55.jpg
# photo_98_2026-03-29_14-48-54.jpg
pattern = re.compile(r"^(photo)_(\d+)(_.+)$", re.IGNORECASE)

files = []

for f in FOLDER.iterdir():
    if not f.is_file():
        continue

    m = pattern.match(f.name)
    if not m:
        continue

    prefix = m.group(1)      # photo
    old_num = int(m.group(2))
    rest = m.group(3)        # _2026-03-29_14-47-55.jpg

    # Пытаемся вытащить дату/время из остатка имени
    # например: _2026-03-29_14-47-55.jpg
    dt_match = re.search(r"_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})", rest)

    if dt_match:
        dt_key = dt_match.group(1) + "_" + dt_match.group(2)
    else:
        # если вдруг даты в имени нет — ставим пустое значение
        dt_key = ""

    files.append({
        "path": f,
        "prefix": prefix,
        "old_num": old_num,
        "rest": rest,
        "dt_key": dt_key
    })

# Сортировка:
# 1. по дате/времени из имени
# 2. по старому номеру внутри серии
# 3. по полному имени — на всякий случай
files.sort(key=lambda x: (x["dt_key"], x["old_num"], x["path"].name.lower()))

if not files:
    print("Файлы вида photo_<число>_... не найдены.")
    exit()

print("Будут переименованы файлы в таком порядке:")
for i, item in enumerate(files, start=START_NUMBER):
    new_name = f'{item["prefix"]}_{i}{item["rest"]}'
    print(f'{item["path"].name}  ->  {new_name}')

confirm = input("\nПродолжить? (y/n): ").strip().lower()
if confirm != "y":
    print("Отменено.")
    exit()

# Шаг 1: временные имена, чтобы избежать конфликтов
temp_records = []
for idx, item in enumerate(files):
    temp_name = f"__tmp_rename__{idx}__{item['path'].name}"
    temp_path = item["path"].with_name(temp_name)
    os.rename(item["path"], temp_path)
    temp_records.append((temp_path, item))

# Шаг 2: финальные имена
for new_num, (temp_path, item) in enumerate(temp_records, start=START_NUMBER):
    new_name = f'{item["prefix"]}_{new_num}{item["rest"]}'
    final_path = temp_path.with_name(new_name)
    os.rename(temp_path, final_path)

print("\nГотово.")
print(f"Переименовано файлов: {len(files)}")
print(f"Нумерация: с {START_NUMBER} по {START_NUMBER + len(files) - 1}")