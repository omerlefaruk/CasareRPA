import ast
from pathlib import Path


def check_files():
    nodes_dir = Path("src/casare_rpa/nodes")
    for filepath in nodes_dir.rglob("*.py"):
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError as e:
            print(f"Error in {filepath}: {e}")
        except IndentationError as e:
            print(f"Error in {filepath}: {e}")
        except Exception as e:
            print(f"Unexpected error in {filepath}: {e}")


if __name__ == "__main__":
    check_files()
