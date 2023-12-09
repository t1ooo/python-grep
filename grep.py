from typing import Generator, List

import os
import re
import argparse
import sys


def scan_files_recursive(base) -> Generator[str, None, None]:
    strip_root = False
    if base == "":
        strip_root = True
        base = "./"
    for root, _, files in os.walk(base):
        if strip_root:
            root = root[len(base) :]
        for f in files:
            yield f if root == "" else f"{root}/{f}"


def color_match(s: str) -> str:
    return "\x1b[01;31m\x1b[K" + s + "\x1b[m\x1b[K"


def color_file(s: str) -> str:
    return "\x1b[35m\x1b[K" + s + "\x1b[m\x1b[K"


def color_separator(s: str) -> str:
    return "\x1b[36m\x1b[K" + s + "\x1b[m\x1b[K"


def grep(
    pattern: str,
    files: List[str],
    ignore_case=False,
    invert_match=False,
    extended_regexp=False,
    recursive=False,
    color=False,
) -> bool:
    selected = False
    error = False

    p = pattern if extended_regexp else re.escape(pattern)
    r = re.compile(p, flags=re.IGNORECASE if ignore_case else 0)

    if recursive and len(files) == 0:
        files = list(scan_files_recursive(""))

    def print_out(s):
        nonlocal selected
        selected = True
        print(s)

    def print_err(s):
        nonlocal error
        error = True
        print(s, file=sys.stderr)

    def match(line):
        m = r.search(line) is not None
        if invert_match:
            m = not m
        return m

    def fmt(line, file):
        sep = ":"
        if color:
            if not invert_match:
                line = r.sub(lambda m: color_match(m[0]), line)
            file = color_file(file)
            sep = color_separator(sep)
        if len(files) > 1:
            return file + sep + line
        return line

    def grep_file(file):
        with open(file, "r", encoding="utf-8") as f:
            try:
                for line in f:
                    line = line.rstrip("\r\n")
                    if match(line):
                        print_out(fmt(line, file))
            except UnicodeDecodeError:
                print_out(f"Binary file {file} matches")

    for file in files:
        if not os.path.exists(file):
            print_err(f"grep: {file}: No such file or directory")
            continue

        if os.path.isdir(file):
            if recursive:
                files.extend(scan_files_recursive(file))
            else:
                print_err(f"grep: {file}: Is a directory")
            continue

        grep_file(file)

    return selected and not error


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern")
    ap.add_argument("files", nargs="*")
    ap.add_argument("-i", "--ignore-case", default=False, action="store_true")
    ap.add_argument("-v", "--invert-match", default=False, action="store_true")
    ap.add_argument("-E", "--extended-regexp", default=False, action="store_true")
    ap.add_argument("-r", "--recursive", default=False, action="store_true")
    ap.add_argument("--color", default="never", choices=["always", "never"])
    args = ap.parse_args()

    ok = grep(
        args.pattern,
        args.files,
        ignore_case=args.ignore_case,
        invert_match=args.invert_match,
        extended_regexp=args.extended_regexp,
        recursive=args.recursive,
        color=args.color == "always",
    )

    sys.exit(0 if ok else 2)
