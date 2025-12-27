import os
import re

def migrate_combo_height():
    root_dir = r"src\casare_rpa\presentation\canvas"
    
    # Simple string replacement
    target = "TOKENS.sizes.combo_height"
    replacement = "TOKENS.sizes.input_md"
    
    files_to_check = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                files_to_check.append(os.path.join(root, file))

    count = 0
    for file_path in files_to_check:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if target in content:
                new_content = content.replace(target, replacement)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Fixed {file_path}")
                count += 1
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
    print(f"Total files fixed: {count}")

if __name__ == "__main__":
    migrate_combo_height()
