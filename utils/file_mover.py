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

def filter_files(files, folder_path, ignore=None):
    ignore = [i.lower() for i in ignore] if ignore else []
    result = []
    for file in files:
        if file.name.startswith("."):
            continue
        relative_parts = [p.lower() for p in file.relative_to(folder_path).parts]
        if any(part in ignore for part in relative_parts):
            continue
        result.append(file)
    return result

def get_destination_path(file, folder_path, categories, recursive, flat):
    extension = file.suffix
    category = get_category(extension, categories)
    if recursive and not flat and file.parent != Path(folder_path):
        destination_folder = file.parent / category
    else:
        destination_folder = Path(folder_path) / category
    return destination_folder / file.name

def resolve_rename(destination, claimed=None):
    dest = Path(destination)
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    claimed = claimed or set()
    counter = 1
    new_dest = dest
    while new_dest.exists() or str(new_dest) in claimed:
        new_dest = parent / f"{stem}_{counter}{suffix}"
        counter += 1
    return new_dest

def detect_conflicts(files, folder_path, categories, recursive, flat):
    conflicts = []
    seen_destinations = {}

    for file in files:
        destination = get_destination_path(file, folder_path, categories, recursive, flat)
        dest_str = str(destination)

        if destination.exists():
            conflicts.append({
                "file": file,
                "destination": destination,
                "type": "disk"
            })
        elif dest_str in seen_destinations:
            conflicts.append({
                "file": file,
                "destination": destination,
                "type": "batch",
                "conflicts_with": seen_destinations[dest_str]
            })
        else:
            seen_destinations[dest_str] = file

    return conflicts

def move_file(source, destination, dry_run=False):
    source = Path(source)
    destination = Path(destination)

    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))

    action = "renamed" if source.name != destination.name else "moved"
    return {
        "source": str(source),
        "destination": str(destination),
        "action": action
    }

def organize_files(folder_path, categories, dry_run=False, recursive=False,
                   ignore=None, flat=False, resolutions=None):
    files = get_all_files(folder_path, recursive)
    files = filter_files(files, folder_path, ignore)
    moves = []
    resolutions = resolutions or {}
    claimed_destinations = set()

    for file in files:
        destination = get_destination_path(file, folder_path, categories, recursive, flat)
        has_conflict = destination.exists() or str(destination) in claimed_destinations

        if has_conflict:
            resolution = resolutions.get(str(file), "rename")

            if resolution == "skip":
                moves.append({
                    "source": str(file),
                    "destination": str(destination),
                    "action": "skipped"
                })
                continue
            elif resolution == "rename":
                destination = resolve_rename(destination, claimed_destinations)

        claimed_destinations.add(str(destination))
        move = move_file(file, destination, dry_run)
        moves.append(move)

    return moves