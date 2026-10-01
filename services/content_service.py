import re


def clean_travelweekly_page(page_text: str, hotel_name: str) -> str:
    """Keep the hotel section and remove bulky Markdown media URLs."""
    lines = page_text.splitlines()
    start_marker = f"# {hotel_name}".casefold()

    start = next(
        (
            index
            for index, line in enumerate(lines)
            if line.strip().casefold() == start_marker
        ),
        None,
    )

    if start is None:
        raise ValueError("Hotel heading was not found in the page.")

    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].strip() == "## Other Doha Area Hotels"
        ),
        None,
    )

    if end is None:
        raise ValueError("End of the hotel section was not found.")

    text = "\n".join(lines[start:end])

    # Remove image markup, including long image URLs.
    text = re.sub(r"!\[[^\]]*\]\([^\n]*?\)", "", text)

    # Preserve link labels while removing their URLs.
    text = re.sub(r"\[([^\]]*)\]\([^\n]*?\)", r"\1", text)

    # Reduce repeated blank lines.
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)

    return text.strip()