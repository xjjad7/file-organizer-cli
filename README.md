# File Organizer CLI

A command-line tool that automatically scans any folder and sorts its contents
into clean, categorized subfolders, so your Downloads or Desktop never becomes
a disaster zone again.

---

## Demo
```
$ python organizer.py ~/Downloads --dry-run --verbose

┌─────────────────────────────────────────────────────┐
│                   Dry Run Preview                   │
├────────────────────────┬────────────────────────────┤
│ File                   │ Destination                │
├────────────────────────┼────────────────────────────┤
│ photo.jpg              │ ~/Downloads/Images         │
│ report.pdf             │ ~/Downloads/Documents      │
│ song.mp3               │ ~/Downloads/Audio          │
│ script.py              │ ~/Downloads/Code           │
└────────────────────────┴────────────────────────────┘

Would move 4 file(s)
```
---

## Features

- Sorts files into `Images`, `Documents`, `Videos`, `Audio`, `Archives`, `Code`, `Executables`, `Others`
- `--dry-run` preview changes without moving anything
- `--verbose` print every file operation to the terminal
- `--undo` reverse the last organize session
- `--recursive` organize files inside subfolders too
- `--recursive --flat` organize files in root folder from all subfolders too
- `--ignore` skip specific folders (e.g. `--ignore work,backup`)
- `--config` use a custom category config file

---

## Installation
```
git clone https://github.com/xjjad7/file-organizer-cli.git
cd file-organizer-cli
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
---

## Usage
```
# To Organize a folder
python organizer.py ~/Downloads

# Preview without actually moving anything
python organizer.py ~/Downloads --dry-run --verbose

# To Organize including subfolders
python organizer.py ~/Downloads --recursive

# Recursive but skips certain folders
python organizer.py ~/Downloads --recursive --ignore work,backup

# Use a custom config
python organizer.py ~/Downloads --config my_config.json

# Undo last session
python organizer.py ~/Downloads --undo
```
---

## Custom Config

You can define your own categories by editing `config.json` or passing a custom file with `--config`:
```
{
  "categories": {
    "Images": [".jpg", ".png", ".gif"],
    "Work": [".pdf", ".docx", ".xlsx"],
    "MyCategory": [".exe", ".py"]
  }
}
```
---

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.13+-blue)
![Rich](https://img.shields.io/badge/Rich-terminal_UI-green)

---
