"""
Simple fix: Comment out PostgreSQL and use SQLite
Run this script to fix your .env file
"""

import os

print("🔧 Fixing .env file to use SQLite...")

# Read current .env
with open('.env', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Comment out DATABASE_URL
new_lines = []
for line in lines:
    if line.strip().startswith('DATABASE_URL='):
        new_lines.append('# ' + line)
        print(f"✅ Commented out: {line.strip()}")
    elif line.strip().startswith('DATABASE_TYPE='):
        new_lines.append('# ' + line)
        print(f"✅ Commented out: {line.strip()}")
    else:
        new_lines.append(line)

# Write back
with open('.env', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("\n✅ Done! Now .env will use SQLite by default")
print("\n📝 To use it, run:")
print("   python database/models.py")