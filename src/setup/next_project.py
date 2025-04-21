from dotenv import load_dotenv
import os
from pathlib import Path
from setup.base_config_files import (
    PACKAGE_JSON,
    TSCONFIG_JSON,
    NEXT_CONFIG_JS,
    LAYOUT_TSX,
    GLOBALS_CSS,
    PAGE_TSX,
)

load_dotenv()

DESTINATION_PATH = os.getenv("DESTINATION_PATH", "")
destination_path = Path(DESTINATION_PATH)


def setup_next_project() -> None:
    """
    Set up the basic Next.js project structure and configuration files
    """
    print("Setting up Next.js project structure...")

    # Create src directory
    src_dir = destination_path / "src"
    src_dir.mkdir(exist_ok=True, parents=True)

    # Create app directory
    app_dir = src_dir / "app"
    app_dir.mkdir(exist_ok=True, parents=True)

    # Create components directory
    components_dir = src_dir / "components"
    components_dir.mkdir(exist_ok=True, parents=True)

    # Create lib directory for utilities
    lib_dir = src_dir / "lib"
    lib_dir.mkdir(exist_ok=True, parents=True)

    # Create package.json
    (destination_path / "package.json").write_text(PACKAGE_JSON)

    # Create tsconfig.json
    (destination_path / "tsconfig.json").write_text(TSCONFIG_JSON)

    # Create next.config.js
    (destination_path / "next.config.js").write_text(NEXT_CONFIG_JS)

    # Create base app files
    (app_dir / "layout.tsx").write_text(LAYOUT_TSX)

    # Create globals.css
    (app_dir / "globals.css").write_text(GLOBALS_CSS)

    # Create root page.tsx
    (app_dir / "page.tsx").write_text(PAGE_TSX)

    print("Next.js project structure set up successfully.")
