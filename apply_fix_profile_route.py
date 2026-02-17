import re

# Read the file
with open('app/routes/main.py', 'r') as f:
    content = f.read()

# Define the pattern to match the profile route and its indented content
pattern = r'@main\.route\(\'/profile\'\)\s*@login_required\s*def profile\(\):\s*"""Redirect to the new profile page under /user"""\s*return redirect\(url_for\(\'profile\.profile_page\'\)\)\s*\n\s*# Initialize'

# Replace with the fixed version
replacement = '@main.route(\'/profile\')\n@login_required\ndef profile():\n    """Redirect to the new profile page under /user"""\n    return redirect(url_for(\'profile.profile_page\'))\n\n# Initialize'

# Apply the replacement
new_content = re.sub(pattern, replacement, content)

# Write the file back
with open('app/routes/main.py', 'w') as f:
    f.write(new_content)

print("Fix applied successfully!")
