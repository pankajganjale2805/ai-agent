#!/usr/bin/env python3
import os
import re
import json
from typing import Dict, List
from dotenv import load_dotenv
from pathlib import Path
import shutil

from prompt.code_conversion import PROMPT_FOR_CODE_CONVERSION
from helpers.read_write import read_file
from communication.code_convert import convert_with_llm

load_dotenv()

SOURCE_PATH = os.getenv("SOURCE_PATH", "")
DESTINATION_PATH = os.getenv("DESTINATION_PATH", "")
source_path = Path(SOURCE_PATH)
destination_path = Path(DESTINATION_PATH)


def copy_assets_and_styles() -> None:
    """
    Copy assets (images, fonts) and styles from Angular to Next.js project
    preserving the directory structure where appropriate
    """
    print("Copying assets and styles...")

    # Create public directory for static assets
    public_dir = destination_path / "public"
    public_dir.mkdir(exist_ok=True, parents=True)

    # Create images directory in public
    images_dir = public_dir / "images"
    images_dir.mkdir(exist_ok=True, parents=True)

    # Copy images
    if (source_path / "app" / "images").exists():
        print("Copying images...")
        copy_directory(source_path / "app" / "images", images_dir)

    # Copy from assets directory if it exists
    if (source_path / "app" / "assets").exists():
        print("Copying assets...")
        assets_dir = public_dir / "assets"
        assets_dir.mkdir(exist_ok=True, parents=True)
        copy_directory(source_path / "app" / "assets", assets_dir)

    # Copy fonts to public directory
    if (source_path / "app" / "fonts").exists():
        print("Copying fonts...")
        fonts_dir = public_dir / "fonts"
        fonts_dir.mkdir(exist_ok=True, parents=True)
        copy_directory(source_path / "app" / "fonts", fonts_dir)

    # Create styles directory for SCSS/CSS files
    styles_src_dir = destination_path / "src" / "styles"
    styles_src_dir.mkdir(exist_ok=True, parents=True)

    # Copy SCSS files if they exist
    if (source_path / "app" / "sass").exists():
        print("Copying SCSS files...")
        copy_directory(source_path / "app" / "sass", styles_src_dir)

    # Copy CSS files if they exist
    if (source_path / "app" / "styles").exists():
        print("Copying CSS files...")
        copy_directory(source_path / "app" / "styles", styles_src_dir)

    # Create a main style import file
    # create_style_imports(styles_src_dir)

    print("Assets and styles copying complete.")


def copy_directory(source_dir: Path, target_dir: Path) -> None:
    """
    Recursively copy a directory and its contents from source to target

    Args:
        source_dir: Source directory path
        target_dir: Target directory path
    """
    # Ensure the target directory exists
    target_dir.mkdir(exist_ok=True, parents=True)

    # Copy all files from source to target
    for item in source_dir.iterdir():
        if item.is_file():
            # Copy file
            shutil.copy2(item, target_dir / item.name)
        elif item.is_dir():
            # Recursively copy subdirectory
            copy_directory(item, target_dir / item.name)


# def create_style_imports(styles_dir: Path) -> None:
#     """
#     Create a main SCSS file that imports all other SCSS files

#     Args:
#         styles_dir: Directory containing style files
#     """
#     # Check if there are any SCSS files
#     scss_files = list(styles_dir.glob("**/*.scss"))
#     css_files = list(styles_dir.glob("**/*.css"))

#     if scss_files:
#         # Create a main.scss file
#         main_scss = styles_dir / "main.scss"

#         # Generate import statements for each SCSS file
#         imports = []
#         for file in scss_files:
#             # Get relative path from styles_dir
#             rel_path = file.relative_to(styles_dir)
#             # Create import statement with path
#             # Convert to posix path for consistent forward slashes
#             path_str = str(rel_path.with_suffix("")).replace("\\", "/")
#             imports.append(f'@import "{path_str}";')

#         # Join import statements and write to file
#         main_scss.write_text("\n".join(imports))
#         print(f"Created {main_scss} with imports for {len(scss_files)} SCSS files")

#     if css_files:
#         # For CSS files, create a global.css
#         global_css = styles_dir / "globals.css"

#         # Open each CSS file and concatenate
#         css_content = []
#         for file in css_files:
#             if file != global_css:  # Avoid including the file we're creating
#                 file_content = file.read_text(encoding="utf-8")
#                 css_content.append(f"/* From {file.name} */")
#                 css_content.append(file_content)

#         # Write combined content to globals.css
#         if css_content:
#             global_css.write_text("\n\n".join(css_content))
#             print(f"Created {global_css} with content from {len(css_files)} CSS files")
