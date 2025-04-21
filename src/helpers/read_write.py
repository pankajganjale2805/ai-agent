#!/usr/bin/env python3
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SOURCE_PATH = os.getenv("SOURCE_PATH", "")
source_path = Path(SOURCE_PATH)


def read_file(file_path: str) -> str:
    """
    Read the contents of a file

    Args:
        file_path: Path to the file (relative to angular_root or absolute)

    Returns:
        File contents as string or empty string if file not found
    """
    if not file_path:
        return ""

    try:
        # Handle both absolute and relative paths
        if os.path.isabs(file_path):
            path = Path(file_path)
        else:
            path = source_path / file_path

        # Check if file exists
        if not path.exists():
            print(f"Warning: File not found: {path}")
            return ""

        # Read and return file contents
        return path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""
