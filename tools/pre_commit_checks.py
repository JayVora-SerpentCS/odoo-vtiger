#!/usr/bin/env python3
# See LICENSE file for full copyright and licensing details.

import ast
import pathlib
import sys
import xml.etree.ElementTree as ET

SKIP_SUFFIXES = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".ico", ".svg"}


def _is_binary(path):
    try:
        with path.open("rb") as stream:
            return b"\0" in stream.read(1024)
    except OSError:
        return True


def _check_text_file(path, errors):
    if path.suffix.lower() in SKIP_SUFFIXES or _is_binary(path):
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines(True)
    except UnicodeDecodeError:
        return
    for index, line in enumerate(lines, start=1):
        content = line[:-1] if line.endswith("\n") else line
        if content.endswith((" ", "\t")):
            errors.append(f"{path}:{index}: trailing whitespace")
    if lines and not lines[-1].endswith("\n"):
        errors.append(f"{path}: missing final newline")


def _check_python_file(path, errors):
    try:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))
    except SyntaxError as error:
        errors.append(f"{path}: invalid Python: {error}")
        return
    if path.name == "__manifest__.py":
        try:
            ast.literal_eval(source)
        except (SyntaxError, ValueError) as error:
            errors.append(f"{path}: invalid manifest: {error}")


def _check_xml_file(path, errors):
    try:
        ET.parse(path)
    except ET.ParseError as error:
        errors.append(f"{path}: invalid XML: {error}")


def main(argv):
    errors = []
    for filename in argv:
        path = pathlib.Path(filename)
        if not path.exists() or path.is_dir():
            continue
        _check_text_file(path, errors)
        if path.suffix == ".py":
            _check_python_file(path, errors)
        elif path.suffix == ".xml":
            _check_xml_file(path, errors)
    if errors:
        sys.stderr.write("%s\n" % "\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
