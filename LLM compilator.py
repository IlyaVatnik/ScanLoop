# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 13:04:59 2026

@author: Александр
"""

import os

# Какие расширения берем
EXTENSIONS = ('.py', '.md', '.json', '.yaml', '.toml')
# Какие папки игнорируем
IGNORE_DIRS = set(['venv', '.git', '__pycache__', '.idea', '.vscode', 'migrations'])

with open("project_context.txt", "w", encoding="utf-8") as outfile:
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if file.endswith(EXTENSIONS):
                filepath = os.path.join(root, file)
                outfile.write(f"\n\n{'='*50}\n")
                outfile.write(f"FILE: {filepath}\n")
                outfile.write(f"{'='*50}\n")
                try:
                    with open(filepath, "r", encoding="utf-8") as infile:
                        outfile.write(infile.read())
                except Exception as e:
                    outfile.write(f"Error reading file: {e}\n")