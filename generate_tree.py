import os
import sys
from pathlib import Path


def generate_tree_simple(root_dir, output_file="tree.txt"):
    """
    Versión más simple que genera el árbol correctamente
    """
    root = Path(root_dir)

    # Lista de exclusiones
    exclude = {'.git', '__pycache__', '.venv', 'venv', 'node_modules',
               '.idea', '.vscode', '.env', '.gitignore', '.DS_Store'}

    def walk(dir_path, prefix=""):
        """Recorre el directorio y genera líneas del árbol"""
        try:
            contents = list(dir_path.iterdir())
        except (PermissionError, OSError):
            return []

        # Filtrar y ordenar
        dirs = []
        files = []
        for item in contents:
            if item.name in exclude or item.name.startswith('.'):
                continue
            if item.is_dir():
                dirs.append(item)
            else:
                files.append(item)

        dirs.sort(key=lambda x: x.name.lower())
        files.sort(key=lambda x: x.name.lower())
        items = dirs + files

        lines = []
        for i, item in enumerate(items):
            is_last = (i == len(items) - 1)

            if item.is_dir():
                # Línea del directorio
                lines.append(f"{prefix}{'└── ' if is_last else '├── '}{item.name}/")
                # Líneas de los contenidos del directorio
                extension = "    " if is_last else "│   "
                lines.extend(walk(item, prefix + extension))
            else:
                # Línea del archivo
                lines.append(f"{prefix}{'└── ' if is_last else '├── '}{item.name}")

        return lines

    # Generar el árbol
    tree_lines = walk(root)

    # Escribir al archivo
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Directorio: {root.absolute()}\n")
        f.write("=" * 50 + "\n\n")
        # Escribir la raíz
        f.write(f"{root.name}/\n" if root.name else ".\n")
        # Escribir las líneas del árbol
        for line in tree_lines:
            f.write(line + "\n")

    print(f"Árbol generado en: {output_file}")


if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "."

    if not os.path.exists(directory):
        print(f"Error: Directorio '{directory}' no existe.")
        sys.exit(1)

    generate_tree_simple(directory, "tree_simple.txt")