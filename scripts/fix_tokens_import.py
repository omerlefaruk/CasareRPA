import os
import re


def fix_imports():
    root_dir = r"src\casare_rpa\presentation\canvas"

    # Patterns to find and replace
    pattern1 = r"from casare_rpa\.presentation\.canvas\.theme\.tokens import TOKENS"
    replace1 = "from casare_rpa.presentation.canvas.theme import TOKENS"

    pattern2 = r"from \.\.theme\.tokens import TOKENS"
    replace2 = "from ..theme import TOKENS"

    count = 0
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    new_content = re.sub(pattern1, replace1, content)
                    new_content = re.sub(pattern2, replace2, new_content)

                    if new_content != content:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        print(f"Fixed: {file_path}")
                        count += 1
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    print(f"Total files fixed: {count}")


if __name__ == "__main__":
    fix_imports()
