import re


def extract_code_from_response(response: str) -> str:
    """
    Extract code from LLM response, removing any markdown formatting or explanatory text
    """
    # First, try to extract code from markdown code blocks with various language identifiers
    code_block_pattern = (
        r"```(?:jsx|tsx|javascript|typescript|js|ts|react|nextjs|next\.js)?(.+?)```"
    )
    code_blocks = re.findall(code_block_pattern, response, re.DOTALL)

    if code_blocks:
        # Join all code blocks if multiple are found
        clean_code = "\n\n".join(block.strip() for block in code_blocks)
        # Remove any language identifiers that might have been included
        clean_code = re.sub(
            r"^(jsx|tsx|javascript|typescript|js|ts|react|nextjs|next\.js)\s*\n",
            "",
            clean_code,
            flags=re.MULTILINE,
        )
        return clean_code

    # If no code blocks, try to identify pure code sections
    # Remove common prefixes that might indicate explanatory text
    lines = response.split("\n")
    cleaned_lines = []
    in_explanation = False

    for line in lines:
        stripped = line.strip()

        # Skip explanatory text markers
        if any(
            marker in stripped.lower()
            for marker in [
                "here's the",
                "here is the",
                "converting",
                "i've converted",
                "this is the",
                "code implementation",
                "explanation:",
                "note:",
                "implementation of",
                "let me",
                "the react",
                "the next.js",
                "as requested",
                "here you go",
                "this code",
                "following is",
                "this component",
                "this implementation",
                "i've created",
                "now let's",
                "let me explain",
                "i'll create",
            ]
        ):
            in_explanation = True
            continue

        # Skip empty lines at the beginning
        if not cleaned_lines and not stripped:
            continue

        # If we hit imports or actual code, we're no longer in explanation
        if (
            stripped.startswith("import ")
            or stripped.startswith("export ")
            or stripped.startswith("function ")
            or stripped.startswith("const ")
            or stripped.startswith("class ")
            or stripped.startswith("interface ")
            or stripped.startswith("type ")
            or stripped.startswith("let ")
            or stripped.startswith("var ")
            or stripped.startswith("async ")
            or stripped.startswith("return ")
            or stripped.startswith("<")  # JSX/HTML opening tag
            or stripped.startswith("use ")
        ):  # React 'use client' directive
            in_explanation = False

        if not in_explanation:
            cleaned_lines.append(line)

    # If we have extracted any code this way
    if cleaned_lines:
        code = "\n".join(cleaned_lines)
        # Remove any trailing explanation text
        if "//" in code or "/*" in code:
            # Keep essential TODOs but remove explanatory comments
            comment_lines = []
            code_lines = code.split("\n")
            for i, line in enumerate(code_lines):
                line_stripped = line.strip()
                # Check if this is an explanatory comment, not a TODO
                if (
                    ("//" in line and not "TODO" in line)
                    or ("/*" in line and not "TODO" in line)
                    or ("*" == line_stripped.lstrip())
                    or ("*/" in line)
                ):
                    if not any(
                        code_keyword in line_stripped
                        for code_keyword in [
                            "const",
                            "let",
                            "var",
                            "function",
                            "class",
                            "import",
                            "export",
                            "return",
                            "<",
                            ">",
                        ]
                    ):
                        comment_lines.append(i)

            # Remove comment lines
            code_lines = [
                line for i, line in enumerate(code_lines) if i not in comment_lines
            ]
            code = "\n".join(code_lines)

        return code

    # Last resort: just return the response as is, assuming it's just code
    return response.strip()
