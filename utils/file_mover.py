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

def organize_files(folder_path, categories, dry_run=False, recursive=False, ignore=None, flat=False):
    files = get_all_files(folder_path, recursive)
    moves = []
    ignore = [i.lower() for i in ignore] if ignore else []

    for file in files:
        if file.name.startswith("."):
            continue

        relative_parts = [p.lower() for p in file.relative_to(folder_path).parts]
        if any(part in ignore for part in relative_parts):
            continue

        extension = file.suffix
        category = get_category(extension, categories)

        if recursive and not flat and file.parent != Path(folder_path):
            destination_folder = file.parent / category
        else:
            destination_folder = Path(folder_path) / category

        move = move_file(file, destination_folder, dry_run)
        moves.append(move)

    return moves