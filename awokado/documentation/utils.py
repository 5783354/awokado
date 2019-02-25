import re
import sys


def trim(docstring):
    """trim function from PEP-257"""
    if not docstring:
        return ""
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)

    # Current code/unittests expects a line return at
    # end of multiline docstrings
    # workaround expected behavior from unittests
    if "\n" in docstring:
        trimmed.append("")

    # Return a single string:
    return "\n".join(trimmed)


def parse_doc_string(doc_string):
    PARAM_OR_RETURNS_REGEX = re.compile(":(?:param|returns)")
    docstring = trim(doc_string)
    long_description = None

    lines = docstring.split("\n", 1)
    short_description = lines[0]

    if len(lines) > 1:
        long_description = lines[1].strip()

        match = PARAM_OR_RETURNS_REGEX.search(long_description)
        if match:
            long_desc_end = match.start()
            long_description = long_description[:long_desc_end].rstrip()

    return short_description, long_description
