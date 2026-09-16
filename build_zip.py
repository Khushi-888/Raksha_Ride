import os
import zipfile

def create_project_zip(zip_name):
    # Exclude these directories and files from the zip
    exclude_dirs = {'.git', '.vscode', '__pycache__', 'venv', 'env', 'node_modules', 'raksharide'}
    exclude_files = {zip_name, 'build_zip.py'}
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files or file.endswith('.zip'):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start='.')
                zipf.write(file_path, arcname)
                print(f"Added {arcname}")

if __name__ == "__main__":
    zip_filename = "Antigravity_Full_Project.zip"
    create_project_zip(zip_filename)
    print(f"\nSuccessfully created {zip_filename}")
