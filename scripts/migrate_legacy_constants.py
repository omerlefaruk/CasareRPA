
import os
import re

def migrate_legacy_constants():
    root_dir = r"src\casare_rpa\presentation\canvas"
    
    # Mappings
    replacements = {
        r"FONT_SIZES\.xs": "TOKENS.typography.tiny",
        r"FONT_SIZES\.sm": "TOKENS.typography.caption",
        r"FONT_SIZES\.md": "TOKENS.typography.body",
        r"FONT_SIZES\.lg": "TOKENS.typography.body", # Fallback
        r"FONT_SIZES\.xl": "TOKENS.typography.h3",
        r"FONT_SIZES\.xxl": "TOKENS.typography.h2",
        
        r"SPACING\.xs": "TOKENS.spacing.xs",
        r"SPACING\.sm": "TOKENS.spacing.sm",
        r"SPACING\.md": "TOKENS.spacing.md",
        r"SPACING\.lg": "TOKENS.spacing.lg",
        r"SPACING\.xl": "TOKENS.spacing.xl",
        
        r"RADIUS\.sm": "TOKENS.radius.sm",
        r"RADIUS\.md": "TOKENS.radius.md",
        r"RADIUS\.lg": "TOKENS.radius.lg",
        r"RADIUS\.xl": "TOKENS.radius.xl",
        r"RADIUS\.circle": "999",

        r"SIZES\.icon_sm": "TOKENS.sizes.icon_sm",
        r"SIZES\.icon_md": "TOKENS.sizes.icon_md",
        r"SIZES\.icon_lg": "TOKENS.sizes.icon_lg",
    }
    
    # Regex for cleanup imports
    # Pattern to match "from ...theme import (..., FONT_SIZES, ...)" multiline is hard.
    # We will just remove the specific words from the import block if they exist.
    
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
            
            original_content = content
            
            # Apply replacements
            for pattern, replacement in replacements.items():
                content = re.sub(pattern, replacement, content)
            
            # Use TOKENS if we added usages
            if "TOKENS." in content and "import TOKENS" not in content and "TOKENS," not in content:
                # Naive import injection - finding where theme is imported
                if "from casare_rpa.presentation.canvas.theme import" in content:
                    content = content.replace("from casare_rpa.presentation.canvas.theme import", "from casare_rpa.presentation.canvas.theme import TOKENS, ")
                elif "from .theme import" in content:
                     content = content.replace("from .theme import", "from .theme import TOKENS, ")

            # Cleanup imports (simple string removal for comma separated list)
            # This is risky but "FONT_SIZES," "SPACING," etc usually appear in lists.
            keywords = ["FONT_SIZES", "SPACING", "RADIUS", "SIZES", "BORDER_RADIUS"]
            for kw in keywords:
                # Remove "    KW," lines
                content = re.sub(r"^\s*" + kw + r",\s*$", "", content, flags=re.MULTILINE)
                # Remove "KW," inline
                content = re.sub(kw + r",", "", content)
                # Remove ", KW" inline
                content = re.sub(r",\s*" + kw, "", content)
                # Remove "KW" at end of import (tricky)

            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Migrated: {file_path}")
                count += 1
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
    print(f"Total files migrated: {count}")

if __name__ == "__main__":
    migrate_legacy_constants()
