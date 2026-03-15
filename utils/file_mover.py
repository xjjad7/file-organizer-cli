import os
import shutil
from pathlib import Path

def get_category(file_extension, categories):
    file_extension = file_extension.lower()
    for category, extensions in categories.items():
        if file_extension in extensions:
            return category
    return "Others"

def get_all_files(folder_path, recursive=False):
    folder = Path(folder_path)
    if recursive:
        return [f for f in folder.rglob("*") if f.is_file()]
    return [f for f in folder.iterdir() if f.is_file()]

def move_file(source, destination_folder, dry_run=False):
    destination_folder = Path(destination_folder)
    destination = destination_folder / Path(source).name

    if not dry_run:
        destination_folder.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))

    return {
        "source": str(source),
        "destination": str(destination)
    }

def organize_files(folder_path, categories, dry_run=False, recursive=False):
    files = get_all_files(folder_path, recursive)
    moves = []

    for file in files:
        if file.name.startswith("."):
            continue

        extension = file.suffix
        category = get_category(extension, categories)
        destination_folder = Path(folder_path) / category

        move = move_file(file, destination_folder, dry_run)
        moves.append(move)

    return moves