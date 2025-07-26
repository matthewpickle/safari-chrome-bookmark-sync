#!/usr/bin/env python3
import os
import json
import plistlib
import shutil
from datetime import datetime

# Paths
SAFARI_BOOKMARKS = os.path.expanduser('~/Library/Safari/Bookmarks.plist')
CHROME_BOOKMARKS = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Bookmarks')

BACKUP_DIR = os.path.expanduser('~/Desktop/bookmark_sync_backups')
SYNCED_FOLDER_NAME = 'Synced'

def backup_file(path):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    base = os.path.basename(path)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'{base}.{timestamp}.bak')
    shutil.copy2(path, backup_path)
    print(f'Backup created: {backup_path}')

def extract_safari_bookmarks(node, bookmarks=None):
    if bookmarks is None:
        bookmarks = []
    if isinstance(node, dict):
        if node.get('WebBookmarkType') == 'WebBookmarkTypeLeaf':
            url = node.get('URLString')
            title = node.get('URIDictionary', {}).get('title', url)
            if url:
                bookmarks.append({'url': url, 'title': title})
        elif node.get('Children'):
            for child in node['Children']:
                extract_safari_bookmarks(child, bookmarks)
    elif isinstance(node, list):
        for item in node:
            extract_safari_bookmarks(item, bookmarks)
    return bookmarks

def extract_chrome_bookmarks(node, bookmarks=None):
    if bookmarks is None:
        bookmarks = []
    if isinstance(node, dict):
        if node.get('type') == 'url':
            url = node.get('url')
            title = node.get('name', url)
            if url:
                bookmarks.append({'url': url, 'title': title})
        elif 'children' in node:
            for child in node['children']:
                extract_chrome_bookmarks(child, bookmarks)
    elif isinstance(node, list):
        for item in node:
            extract_chrome_bookmarks(item, bookmarks)
    return bookmarks

def add_safari_synced_folder(bookmarks_data, merged_bookmarks):
    synced_folder = {
        'Title': SYNCED_FOLDER_NAME,
        'WebBookmarkType': 'WebBookmarkTypeList',
        'Children': [
            {
                'URIDictionary': {'title': b['title']},
                'URLString': b['url'],
                'WebBookmarkType': 'WebBookmarkTypeLeaf',
            } for b in merged_bookmarks
        ]
    }
    # Add to the root level
    bookmarks_data['Children'].append(synced_folder)
    return bookmarks_data

def add_chrome_synced_folder(bookmarks_data, merged_bookmarks):
    synced_folder = {
        'type': 'folder',
        'name': SYNCED_FOLDER_NAME,
        'children': [
            {
                'type': 'url',
                'name': b['title'],
                'url': b['url'],
            } for b in merged_bookmarks
        ]
    }
    # Add to the "bookmark_bar"
    bookmarks_data['roots']['bookmark_bar']['children'].append(synced_folder)
    return bookmarks_data

def main():
    print('*** Please close Safari and Chrome before running this script! ***')
    input('Press Enter to continue if both browsers are closed...')

    # Backup
    backup_file(SAFARI_BOOKMARKS)
    backup_file(CHROME_BOOKMARKS)

    # Read Safari
    with open(SAFARI_BOOKMARKS, 'rb') as f:
        safari_data = plistlib.load(f)
    safari_bookmarks = extract_safari_bookmarks(safari_data.get('Children', []))

    # Read Chrome
    with open(CHROME_BOOKMARKS, 'r') as f:
        chrome_data = json.load(f)
    chrome_bookmarks = extract_chrome_bookmarks(chrome_data['roots'])

    # Merge by URL
    url_to_bookmark = {}
    for b in safari_bookmarks + chrome_bookmarks:
        url_to_bookmark[b['url']] = b  # Last one wins (title from Chrome if duplicate)
    merged_bookmarks = list(url_to_bookmark.values())

    # Remove old Synced folders if present
    safari_data['Children'] = [c for c in safari_data['Children'] if c.get('Title') != SYNCED_FOLDER_NAME]
    chrome_data['roots']['bookmark_bar']['children'] = [c for c in chrome_data['roots']['bookmark_bar']['children'] if c.get('name') != SYNCED_FOLDER_NAME]

    # Add merged bookmarks to both
    safari_data = add_safari_synced_folder(safari_data, merged_bookmarks)
    chrome_data = add_chrome_synced_folder(chrome_data, merged_bookmarks)

    # Write back
    with open(SAFARI_BOOKMARKS, 'wb') as f:
        plistlib.dump(safari_data, f)
    with open(CHROME_BOOKMARKS, 'w') as f:
        json.dump(chrome_data, f, indent=2)

    print('Bookmarks synced! Check the "Synced" folder in both browsers.')

if __name__ == '__main__':
    main() 