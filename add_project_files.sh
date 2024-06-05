#!/bin/bash

# Navigate to the project directory
cd /Users/ulysses/IELTS/writing

# Create a list of files to add
files_to_add=(
  "forms.py"
  "app.py"
  "auth.py"
  "add_files.py"
  "add_commands.txt"
  "config.py"
  "requirements.txt"
)

# Function to add files from a directory while excluding .pyc and other unwanted files
add_files_from_directory() {
  local dir=$1
  if [ -d "$dir" ]; then
    while IFS= read -r -d $'\0' file; do
      files_to_add+=("$file")
    done < <(find "$dir" -type f ! -name "*.pyc" ! -name "*.ico" ! -name "*.png" ! -name "*.jpg" -print0)
  else
    echo "Directory $dir does not exist. Please create it."
  fi
}

# Add files from the specified directories
add_files_from_directory "models/"
add_files_from_directory "routes/"
add_files_from_directory "utils/"
add_files_from_directory "static/"
add_files_from_directory "csv/"
add_files_from_directory "logs/"

# Uncomment the following lines if you need to add specific JS and JSON files

# Add specific JS files
# while IFS= read -r -d $'\0' file; do
#   files_to_add+=("$file")
# done < <(find . -name "*.js" -print0)

# Add specific JSON files
# while IFS= read -r -d $'\0' file; do
#   files_to_add+=("$file")
# done < <(find . -name "*.json" -print0)

# Run aider with all the collected files
aider "${files_to_add[@]}"
