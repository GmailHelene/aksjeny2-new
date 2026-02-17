"""
Emergency fix for access control issues in portfolio.py
This script will create a new portfolio.py file with unified access control
"""

import os
import shutil
from datetime import datetime

# Source file
portfolio_file = 'app/routes/portfolio.py'

# Backup path
backup_path = f"{portfolio_file}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Make backup
shutil.copy2(portfolio_file, backup_path)
print(f"Backup created at {backup_path}")

# Read the file
with open(portfolio_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace decorators
updated_content = content.replace('@access_required', '@unified_access_required')
updated_content = updated_content.replace('@demo_access', '@unified_access_required')

# Write back to the file
with open(portfolio_file, 'w', encoding='utf-8') as f:
    f.write(updated_content)

print(f"Updated {portfolio_file} with unified access control")
print(f"- Replaced {content.count('@access_required')} instances of @access_required")
print(f"- Replaced {content.count('@demo_access')} instances of @demo_access")
