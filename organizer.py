import shutil
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from utils.config_loader import load_config
from utils.file_mover import organize_files, detect_conflicts, filter_files, get_all_files
from utils.logger import write_log, read_last_log, clear_last_log
import argparse

console = Console()

def get_file_info(path):
    path = Path(path)
    if not path.exists():
        return "N/A", "N/A"
    stat = path.stat()
    size = stat.st_size
    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
    if size < 1024:
        size_str = f"{size} B"
    elif size < 1024 * 1024:
        size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = f"{size / 1024 / 1024:.1f} MB"
    return size_str, modified

def prompt_key(valid_keys, prompt_text):
    while True:
        console.print(prompt_text, end="")
        key = input().strip()
        if not any(k.isupper() for k in valid_keys):
            key = key.lower()
        if key in valid_keys:
            return key
        console.print(f"[red]Invalid key. Choose one of: {', '.join(valid_keys)}[/red]")

def prompt_conflict_resolution(conflicts, folder_path):
    resolutions = {}

    table = Table(title=f"Found {len(conflicts)} conflict(s)")
    table.add_column("File", style="yellow")
    table.add_column("Location", style="cyan")
    table.add_column("Size", style="white")
    table.add_column("Modified", style="white")
    table.add_column("Conflict", style="red")

    for c in conflicts:
        file = c["file"]
        size, modified = get_file_info(file)
        location = str(file.relative_to(folder_path).parent)
        if c["type"] == "disk":
            conflict_desc = f"exists in {c['destination'].parent.name}/"
        else:
            other = c["conflicts_with"]
            conflict_desc = f"clashes with {other.parent.name}/{other.name}"
        table.add_row(file.name, location, size, modified, conflict_desc)

    console.print(table)

    bulk_key = prompt_key(
        ["r", "s", "o", "a"],
        "\n[bold](r)[/bold] Rename all  "
        "[bold](s)[/bold] Skip all  "
        "[bold](o)[/bold] Overwrite all  "
        "[bold](a)[/bold] Ask each one : "
    )

    if bulk_key != "a":
        resolution_map = {"r": "rename", "s": "skip", "o": "overwrite"}
        for c in conflicts:
            resolutions[str(c["file"])] = resolution_map[bulk_key]
        return resolutions

    apply_rest = None
    for c in conflicts:
        if apply_rest:
            resolutions[str(c["file"])] = apply_rest
            continue

        file = c["file"]
        dest = c["destination"]

        console.print(
            f"\n[bold yellow]Conflict:[/bold yellow] "
            f"[cyan]{file.name}[/cyan] -> [green]{dest.parent.name}/[/green]"
        )

        incoming_size, incoming_modified = get_file_info(file)
        console.print(
            f"   [cyan]Incoming :[/cyan] "
            f"{file.parent.name}/{file.name:<25} "
            f"{incoming_size:<10} {incoming_modified}"
        )

        if c["type"] == "disk":
            existing_size, existing_modified = get_file_info(dest)
            console.print(
                f"   [green]Existing :[/green] "
                f"{dest.parent.name}/{dest.name:<25} "
                f"{existing_size:<10} {existing_modified}"
            )
        else:
            other = c["conflicts_with"]
            other_size, other_modified = get_file_info(other)
            console.print(
                f"   [green]Batch    :[/green] "
                f"{other.parent.name}/{other.name:<25} "
                f"{other_size:<10} {other_modified}"
            )

        key = prompt_key(
            ["r", "s", "o", "R", "S"],
            "\n[bold](r)[/bold] Rename  "
            "[bold](s)[/bold] Skip  "
            "[bold](o)[/bold] Overwrite  "
            "[bold](R)[/bold] Rename rest  "
            "[bold](S)[/bold] Skip rest : "
        )

        resolution_map = {"r": "rename", "s": "skip", "o": "overwrite"}
        if key == "R":
            resolutions[str(file)] = "rename"
            apply_rest = "rename"
        elif key == "S":
            resolutions[str(file)] = "skip"
            apply_rest = "skip"
        else:
            resolutions[str(file)] = resolution_map[key]

    return resolutions

def print_moves(moves, dry_run=False):
    table = Table(title="File Operations" if not dry_run else "Dry Run Preview")
    table.add_column("File", style="cyan")
    table.add_column("Destination", style="green")
    table.add_column("Action", style="yellow")

    for move in moves:
        source_name = Path(move["source"]).name
        destination = move["destination"]
        action = move.get("action", "moved")
        table.add_row(source_name, destination, action)

    console.print(table)

def print_summary(moves, dry_run=False):
    moved   = sum(1 for m in moves if m.get("action") == "moved")
    renamed = sum(1 for m in moves if m.get("action") == "renamed")
    skipped = sum(1 for m in moves if m.get("action") == "skipped")

    label = "Would" if dry_run else ""
    if moved:
        console.print(f"[green]{label} Moved    {moved} file(s)[/green]")
    if renamed:
        console.print(f"[cyan]{label} Renamed  {renamed} file(s)[/cyan]")
    if skipped:
        console.print(f"[yellow]{label} Skipped  {skipped} file(s)[/yellow]")

def run_undo():
    last_log = read_last_log()
    if not last_log:
        console.print("[yellow]No previous session found to undo.[/yellow]")
        return

    console.print(f"[bold]Undoing session from:[/bold] {last_log['timestamp']}")
    moves = last_log["moves"]
    failed = []

    for move in reversed(moves):
        if move.get("action") == "skipped":
            continue
        source = Path(move["destination"])
        destination = Path(move["source"])
        if not source.exists():
            failed.append(str(source))
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))

    clear_last_log()

    if failed:
        console.print(f"[red]Could not undo {len(failed)} file(s) - already moved or deleted.[/red]")
    console.print(f"[green]Successfully undid {len(moves) - len(failed)} move(s).[/green]")

def main():
    parser = argparse.ArgumentParser(
        description="Organize files in a folder into categorized subfolders."
    )
    parser.add_argument("folder", help="Path to the folder to organize")
    parser.add_argument("--dry-run",   action="store_true", help="Preview changes without moving files")
    parser.add_argument("--verbose",   action="store_true", help="Show each file operation")
    parser.add_argument("--undo",      action="store_true", help="Undo the last organize session")
    parser.add_argument("--config",    help="Path to a custom config JSON file")
    parser.add_argument("--recursive", action="store_true", help="Also organize files in subfolders")
    parser.add_argument("--flat",      action="store_true", help="With --recursive, pull all files into root category folders")
    parser.add_argument("--ignore",    help="Comma-separated folder names to skip (e.g. --ignore work,old)")

    args = parser.parse_args()

    if args.undo:
        run_undo()
        return

    folder = Path(args.folder)
    if not folder.exists() or not folder.is_dir():
        console.print(f"[red]Error:[/red] '{folder}' is not a valid directory.")
        return

    categories = load_config(args.config)
    ignore_list = [i.strip() for i in args.ignore.split(",")] if args.ignore else []

    console.print(f"\n[bold cyan]File Organizer[/bold cyan]")
    console.print(f"Target folder: [yellow]{folder.resolve()}[/yellow]")
    if args.dry_run:
        console.print("[yellow]DRY RUN MODE - no files will be moved[/yellow]\n")

    all_files = get_all_files(folder, recursive=args.recursive)
    filtered  = filter_files(all_files, folder, ignore_list)
    conflicts = detect_conflicts(filtered, folder, categories, args.recursive, args.flat)

    resolutions = {}
    if conflicts and not args.dry_run:
        resolutions = prompt_conflict_resolution(conflicts, folder)
        console.print()

    moves = organize_files(
        folder_path=folder,
        categories=categories,
        dry_run=args.dry_run,
        recursive=args.recursive,
        ignore=ignore_list,
        flat=args.flat,
        resolutions=resolutions
    )

    if not moves:
        console.print("[yellow]No files found to organize.[/yellow]")
        return

    if args.verbose or args.dry_run:
        print_moves(moves, dry_run=args.dry_run)

    print_summary(moves, dry_run=args.dry_run)

    if not args.dry_run:
        write_log(moves)
        console.print("[dim]Session logged. Use --undo to reverse.[/dim]")

if __name__ == "__main__":
    main()