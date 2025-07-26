# Safari-Chrome Bookmark Sync

A Python script that performs two-way synchronization of bookmarks between Safari and Chrome on macOS.

## Features

- **Two-way merge**: Combines bookmarks from both Safari and Chrome
- **Automatic backup**: Creates timestamped backups before making changes
- **Deduplication**: Removes duplicate bookmarks based on URL
- **Safe operation**: Warns user to close browsers before running

## Requirements

- macOS
- Python 3.6+
- Safari and Chrome browsers installed
- Full Disk Access permission for Terminal

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/safari-chrome-bookmark-sync.git
   cd safari-chrome-bookmark-sync
   ```

2. Make the script executable:
   ```bash
   chmod +x bookmark_sync.py
   ```

## Setup (Important!)

### Grant Full Disk Access

Before running the script, you must grant Full Disk Access to your Terminal:

1. Open **System Settings** → **Privacy & Security**
2. Scroll to **Full Disk Access**
3. Click **+** and add your Terminal app (Terminal, iTerm, or VSCode)
4. Restart your Terminal

This is required because the script needs to access Safari's bookmarks file in `~/Library/Safari/`.

## Usage

1. **Close both Safari and Chrome completely**

2. Run the script:
   ```bash
   python3 bookmark_sync.py
   ```

3. Press Enter when prompted to confirm browsers are closed

4. Check both browsers for a new "Synced" folder containing merged bookmarks

## How It Works

1. **Backup**: Creates timestamped backups in `~/Desktop/bookmark_sync_backups/`
2. **Read**: Extracts bookmarks from both Safari (`Bookmarks.plist`) and Chrome (`Bookmarks` JSON)
3. **Merge**: Combines all bookmarks, removing duplicates by URL
4. **Write**: Adds merged bookmarks to a "Synced" folder in both browsers

## File Locations

- **Safari bookmarks**: `~/Library/Safari/Bookmarks.plist`
- **Chrome bookmarks**: `~/Library/Application Support/Google/Chrome/Default/Bookmarks`
- **Backups**: `~/Desktop/bookmark_sync_backups/`

## Important Notes

⚠️ **Always close both browsers before running the script**

⚠️ **Backups are created automatically, but verify results before deleting**

⚠️ **The script creates a "Synced" folder - original folder structures are not preserved for merged bookmarks**

⚠️ **This is a simple merge - complex folder hierarchies are flattened**

## Troubleshooting

### Permission Error
If you see `PermissionError: Operation not permitted`, you need to grant Full Disk Access to your Terminal app (see Setup section above).

### File Not Found
Make sure both Safari and Chrome are installed and have been used at least once (to create bookmark files).

### Script Won't Run
Ensure you're using Python 3:
```bash
python3 --version
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the [MIT License](LICENSE).

## Disclaimer

This script modifies browser bookmark files directly. While it creates backups, use at your own risk. Always verify the results before deleting backups. 