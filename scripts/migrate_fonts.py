import os
import re


def migrate_fonts():
    root_dir = r"src\casare_rpa\presentation\canvas"

    replacements = {
        r"FONTS\.ui": "TOKENS.typography.family",
        r"FONTS\.code": "TOKENS.typography.code",
        r"FONTS\.mono": "TOKENS.typography.code",
    }

    files_to_check = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                files_to_check.append(os.path.join(root, file))

    count = 0
    for file_path in files_to_check:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Apply replacements
            for pattern, replacement in replacements.items():
                content = re.sub(pattern, replacement, content)

            # Use TOKENS if we added usages of TOKENS.typography (if not already there)
            # But usually TOKENS is already imported or we added it in legacy migration.
            # If strictly missing, we might need to add it, but simpler to check imports.

            # Cleanup imports
            # Remove "FONTS," lines or inline
            content = re.sub(r"^\s*FONTS,\s*$", "", content, flags=re.MULTILINE)
            content = re.sub(r"FONTS,", "", content)
            content = re.sub(r",\s*FONTS", "", content)

            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Migrated: {file_path}")
                count += 1

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print(f"Total files migrated: {count}")


if __name__ == "__main__":
    migrate_fonts()
