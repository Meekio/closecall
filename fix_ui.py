"""
Quick script to remove childish emojis and make UI professional.
Run: python fix_ui.py
"""

import re
from pathlib import Path

# Emoji replacements - remove or replace with text
REPLACEMENTS = [
    # Tab labels - remove emojis, keep text
    ('🏠 Home', 'Home'),
    ('👗 Wardrobe', 'Wardrobe'),
    ('✨ Outfits', 'Outfits'),
    ('👤 Profile', 'Profile'),
    
    # Button text
    ('📷\\nAdd Clothes', 'Add Clothes'),
    ('👗\\nMy Wardrobe', 'My Wardrobe'),
    
    # Titles and headers
    ('Hi! ✨', 'Hi!'),
    ('New Outfit ✨', 'New Outfit'),
    ('Here are 3 outfits for you ✨', 'Your Outfits'),
    ('Analyzing your clothes… ✨', 'Analyzing your clothes...'),
    ('✨  Tag & Add to Wardrobe', 'Tag & Add to Wardrobe'),
    
    # Large splash emoji - replace with simple icon
    ('<div style="font-size:72px;margin-bottom:20px">👗</div>',
     '<div style="font-size:48px;margin-bottom:20px;font-weight:300;letter-spacing:2px">CC</div>'),
    
    # Empty wardrobe icon
    ('<div style="font-size:48px;margin-bottom:12px">👗</div>',
     '<div style="font-size:16px;margin-bottom:12px;color:#9CA3AF;font-weight:600">WARDROBE</div>'),
    
    # Placeholder item icon
    ('font-size:28px">👕</div>',
     'font-size:14px;color:#9CA3AF;font-weight:600">•</div>'),
    
    # Weather icons
    ('"🌧️"', '"Rain"'),
    ('"🌤️"', '""'),  # Remove sunny emoji
    
    # Profile wardrobe link
    ('<span class="cc-profile-row-icon">👗</span>',
     '<span class="cc-profile-row-icon">•</span>'),
    
    # Agent thinking steps - remove emojis
    ('("Fetching weather for your location…",    "🌤️"),',
     '("Fetching weather for your location",    ""),'),
    ('("Filtering your wardrobe…",               "👗"),',
     '("Filtering your wardrobe",               ""),'),
    ('("Generating outfit combinations…",        "✨"),',
     '("Generating outfit combinations",        ""),'),
    ('("Validating for occasion and weather…",   "✅"),',
     '("Validating for occasion and weather",   ""),'),
    
    # Status messages
    ('Item added! ✅', 'Item added!'),
    ('Tagging failed ❌', 'Tagging failed'),
]

def fix_file(filepath: Path):
    """Apply replacements to a single file."""
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    for old, new in REPLACEMENTS:
        content = content.replace(old, new)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        print(f"✓ Fixed: {filepath}")
        return True
    return False

def main():
    print("Removing emojis and making UI professional...\n")
    
    # Files to process
    files_to_fix = [
        "app.py",
        "src/ui/home_tab.py",
        "src/ui/wardrobe_tab.py",
        "src/ui/outfits_tab.py",
        "src/ui/add_clothes_tab.py",
        "src/ui/profile_tab.py",
    ]
    
    fixed_count = 0
    for file_path in files_to_fix:
        filepath = Path(file_path)
        if filepath.exists():
            if fix_file(filepath):
                fixed_count += 1
        else:
            print(f"⚠ Not found: {file_path}")
    
    print(f"\n✅ Fixed {fixed_count} files")
    print("\nRestart the app to see changes:")
    print("  python app.py")

if __name__ == "__main__":
    main()
