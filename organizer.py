import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from utils.config_loader import load_config
from utils.file_mover import organize_files
from utils.logger import write_log, read_last_log, clear_last_log
import shutil

console = Console()

def print_moves(moves, dry_run=False):
    table = Table(title="File Operations" if not dry_run else "Dry Run Preview")
    table.add_column("File", style="cyan")
    table.add_column("Destination", style="green")

    for move in moves:
        source_name = Path(move["source"]).name
        destination = move["destination"]
        table.add_row(source_name, destination)

    console.print(table)
    label = "Would move" if dry_run else "Moved"
    console.print(f"\n[bold]{label} {len(moves)} file(s)[/bold]")

def run_undo():
    last_log = read_last_log()

    if not last_log:
        console.print("[yellow]No previous session found to undo.[/yellow]")
        return

    console.print(f"[bold]Undoing session from:[/bold] {last_log['timestamp']}")
    moves = last_log["moves"]
    failed = []

    for move in reversed(moves):
        source = Path(move["destination"])
        destination = Path(move["source"])

        if not source.exists():
            failed.append(str(source))
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))

    clear_last_log()

    if failed:
        console.print(f"[red]Could not undo {len(failed)} files, they may have been moved or deleted.[/red]")

    console.print(f"[green]Successfully undid {len(moves) - len(failed)} move(s).[/green]")

def main():
    parser = argparse.ArgumentParser(
        description="Organize files in a folder into categorized subfolders."
    )
    parser.add_argument("folder", help="Path to the folder to organize")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without moving files")
    parser.add_argument("--verbose", action="store_true", help="Show each file operation")
    parser.add_argument("--undo", action="store_true", help="Undo the last organize session")
    parser.add_argument("--config", help="Path to a custom config JSON file")
    parser.add_argument("--recursive", action="store_true", help="Also organize files in subfolders")
    parser.add_argument("--ignore", help="Comma-separated list of folder names to skip (e.g. --ignore work,old)")
    parser.add_argument("--flat", action="store_true", help="With --recursive, pull all files into root category folders")

    args = parser.parse_args()

    if args.undo:
        run_undo()
        return

    folder = Path(args.folder)
    if not folder.exists() or not folder.is_dir():
        console.print(f"[red]Error:[/red] '{folder}' is not a valid directory.")
        return

    categories = load_config(args.config)

    console.print(f"\n[bold cyan]File Organizer[/bold cyan]")
    console.print(f"Target folder: [yellow]{folder.resolve()}[/yellow]")
    if args.dry_run:
        console.print("[yellow]DRY RUN MODE - no files will be moved[/yellow]\n")

    ignore_list = [i.strip() for i in args.ignore.split(",")] if args.ignore else []

    moves = organize_files(
        folder_path=folder,
        categories=categories,
        dry_run=args.dry_run,
        recursive=args.recursive,
        ignore=ignore_list,
        flat=args.flat
    )

    if not moves:
        console.print("[yellow]No files found to organize.[/yellow]")
        return

    if args.verbose or args.dry_run:
        print_moves(moves, dry_run=args.dry_run)
    else:
        console.print(f"[green]Done! Organized {len(moves)} file(s).[/green]")

    if not args.dry_run:
        write_log(moves)
        console.print("[dim]Session logged. Use --undo to reverse.[/dim]")

if __name__ == "__main__":
    main()