#!/usr/bin/env python3
import os
import json
import plistlib
import shutil
from datetime import datetime

def get_real_user_home():
    """
    Returns the real user's home directory, even when run with sudo.
    """
    if 'SUDO_USER' in os.environ:
        return os.path.expanduser(f"~{os.environ['SUDO_USER']}")
    return os.path.expanduser('~')

# Paths
HOME_DIR = get_real_user_home()
SAFARI_BOOKMARKS = os.path.join(HOME_DIR, 'Library/Safari/Bookmarks.plist')
CHROME_BOOKMARKS = os.path.join(HOME_DIR, 'Library/Application Support/Google/Chrome/Default/Bookmarks')
BACKUP_DIR = os.path.join(HOME_DIR, 'Desktop/bookmark_sync_backups')

def backup_file(path):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    base = os.path.basename(path)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'{base}.{timestamp}.bak')
    shutil.copy2(path, backup_path)
    print(f'Backup created: {backup_path}')

def extract_safari_bookmarks(children_list):
    """
    Recursively extracts bookmarks and folders from Safari's plist data
    into a standardized format.
    """
    items = []
    for node in children_list:
        if node.get('WebBookmarkType') == 'WebBookmarkTypeLeaf':
            url = node.get('URLString')
            title = node.get('URIDictionary', {}).get('title', url)
            if url:
                items.append({'type': 'url', 'title': title, 'url': url})
        elif node.get('WebBookmarkType') == 'WebBookmarkTypeList':
            # This is a folder
            folder_name = node.get('Title', '')
            # Reading List is a special folder we want to skip
            if folder_name == 'com.apple.ReadingList':
                continue
            folder_children = node.get('Children', [])
            items.append({
                'type': 'folder',
                'name': folder_name,
                'children': extract_safari_bookmarks(folder_children)
            })
    return items

def extract_chrome_bookmarks(children_list):
    """
    Recursively extracts bookmarks and folders from Chrome's JSON data
    into a standardized format.
    """
    items = []
    for node in children_list:
        if node.get('type') == 'url':
            url = node.get('url')
            title = node.get('name', url)
            if url:
                items.append({'type': 'url', 'title': title, 'url': url})
        elif node.get('type') == 'folder':
            folder_children = node.get('children', [])
            items.append({
                'type': 'folder',
                'name': node.get('name', ''),
                'children': extract_chrome_bookmarks(folder_children)
            })
    return items

def merge_bookmark_trees(tree1, tree2):
    """
    Recursively merges two bookmark trees.

    - Folders with the same name at the same level are merged.
    - Bookmarks are de-duplicated by URL, with the title from the second tree winning.
    """
    merged_map = {}

    # Add all items from the first tree
    for item in tree1:
        key = f"folder_{item['name']}" if item['type'] == 'folder' else item['url']
        merged_map[key] = item

    # Merge items from the second tree
    for item in tree2:
        key = f"folder_{item['name']}" if item['type'] == 'folder' else item['url']
        if key in merged_map:
            if item['type'] == 'folder':
                # Folder exists, merge children recursively
                existing_folder = merged_map[key]
                merged_children = merge_bookmark_trees(
                    existing_folder.get('children', []), item.get('children', [])
                )
                existing_folder['children'] = merged_children
            else:
                # URL exists, update title (last one wins)
                merged_map[key]['title'] = item['title']
        else:
            # New item, just add it
            merged_map[key] = item

    return list(merged_map.values())

def create_safari_tree(merged_tree):
    """
    Recursively converts the merged bookmark tree back into Safari's plist format.
    """
    safari_children = []
    for item in merged_tree:
        if item['type'] == 'url':
            safari_children.append({
                'URIDictionary': {'title': item['title']},
                'URLString': item['url'],
                'WebBookmarkType': 'WebBookmarkTypeLeaf',
            })
        elif item['type'] == 'folder':
            safari_children.append({
                'Title': item['name'],
                'WebBookmarkType': 'WebBookmarkTypeList',
                'Children': create_safari_tree(item.get('children', [])),
            })
    return safari_children

def create_chrome_tree(merged_tree):
    """
    Recursively converts the merged bookmark tree back into Chrome's JSON format.
    """
    chrome_children = []
    for item in merged_tree:
        if item['type'] == 'url':
            chrome_children.append({
                'type': 'url',
                'name': item['title'],
                'url': item['url'],
            })
        elif item['type'] == 'folder':
            chrome_children.append({
                'type': 'folder',
                'name': item['name'],
                'children': create_chrome_tree(item.get('children', [])),
            })
    return chrome_children

def main():
    print('*** Please close Safari and Chrome before running this script! ***')
    input('Press Enter to continue if both browsers are closed...')

    # Backup
    backup_file(SAFARI_BOOKMARKS)
    backup_file(CHROME_BOOKMARKS)

    # Read Safari
    print("Reading Safari bookmarks...")
    with open(SAFARI_BOOKMARKS, 'rb') as f:
        safari_data = plistlib.load(f)
    safari_tree = extract_safari_bookmarks(safari_data.get('Children', []))

    # Read Chrome
    print("Reading Chrome bookmarks...")
    with open(CHROME_BOOKMARKS, 'r') as f:
        chrome_data = json.load(f)
    chrome_bar_children = chrome_data['roots']['bookmark_bar'].get('children', [])
    chrome_other_children = chrome_data['roots']['other'].get('children', [])
    chrome_tree = extract_chrome_bookmarks(chrome_bar_children + chrome_other_children)

    # Merge the two bookmark trees
    print("Merging bookmark trees...")
    merged_tree = merge_bookmark_trees(safari_tree, chrome_tree)

    # Create the new platform-specific trees
    new_safari_children = create_safari_tree(merged_tree)
    new_chrome_children = create_chrome_tree(merged_tree)

    # Replace the old bookmarks with the new merged tree
    print("Updating bookmark files...")
    safari_data['Children'] = new_safari_children
    chrome_data['roots']['bookmark_bar']['children'] = new_chrome_children
    chrome_data['roots']['other']['children'] = []
    chrome_data['roots']['synced']['children'] = [] # Also clear synced folder

    # Write back
    with open(SAFARI_BOOKMARKS, 'wb') as f:
        plistlib.dump(safari_data, f)
    with open(CHROME_BOOKMARKS, 'w') as f:
        json.dump(chrome_data, f, indent=2)

    print('Success! Your bookmarks have been merged and synced in both browsers.')

if __name__ == '__main__':
    main() 