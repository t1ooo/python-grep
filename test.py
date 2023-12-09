import hashlib
import os
import random
import string
import subprocess
import tempfile
from typing import Generator, List, Tuple
import unittest


def run(cmd: List[str]) -> Tuple[List[str], List[str], int]:
    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    return (
        p.stdout.decode("utf-8").split("\n"),
        p.stderr.decode("utf-8").split("\n"),
        p.returncode,
    )


def file_hash(file: str) -> str:
    with open(file, "rb") as f:
        data = f.read()
        h = hashlib.md5(data)
        return h.hexdigest()


GREP_BASE_CMD = ["grep"]
BASE_CMD = ["poetry", "run", "python", "grep.py"]


TEST_DATA_BASE = tempfile.gettempdir() + "/python-grep/" + file_hash(__file__)


def scan_recursive(base: str) -> Generator[str, None, None]:
    for root, dirs, files in os.walk(base):
        for f in files:
            yield f"{root}/{f}"
        for f in dirs:
            yield f"{root}/{f}"


def rand_str(n: int) -> str:
    ascii_letters = string.ascii_letters
    while len(ascii_letters) < n:
        ascii_letters += string.ascii_letters
    return "".join(random.sample(ascii_letters, n))


def gen_rand_file(path: str, n_lines=10):
    with open(path, "w") as f:
        for _ in range(n_lines):
            n = random.randint(5, 10)
            line = rand_str(n)
            f.write(line + "\n")


def gen_test_data(base_dir: str):
    if os.path.exists(base_dir):
        return
    os.makedirs(base_dir)

    print("gen test data:", base_dir)

    n_dirs = 10
    for dirname in [""] + [rand_str(5).lower() for _ in range(n_dirs)]:
        path = f"{base_dir}/{dirname}"
        os.makedirs(path, exist_ok=True)

        n_files = random.randint(0, 5)
        for _ in range(n_files):
            filename = rand_str(7).lower() + ".txt"
            n_lines = random.randint(0, 20)
            gen_rand_file(f"{path}/{filename}", n_lines)


class GrepTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        gen_test_data(TEST_DATA_BASE)

    def _run_test(self, cmd: List[str], sort=False):
        self.maxDiff = None
        out1, err1, code1 = run(GREP_BASE_CMD + cmd)
        out2, err2, code2 = run(BASE_CMD + cmd)
        if sort:
            out1.sort()
            out2.sort()
            err1.sort()
            err2.sort()

        self.assertEqual(out1, out2, f"wrong out for {' '.join(cmd)}")
        self.assertEqual(err1, err2, f"wrong err for {' '.join(cmd)}")
        self.assertEqual(code1, code2, f"wrong code for {' '.join(cmd)}")

    def test_match(self):
        cmd = ["pipe", "test.py"]
        self._run_test(cmd)

    def test_not_match(self):
        cmd = ["34534523452345", "test.py"]
        self._run_test(cmd)

    def test_ignore_case_short(self):
        cmd = ["-i", "pipe", "test.py"]
        self._run_test(cmd)

    def test_ignore_case_long(self):
        cmd = ["--ignore-case", "pipe", "test.py"]
        self._run_test(cmd)

    def test_invert_match_short(self):
        cmd = ["-v", "pipe", "test.py"]
        self._run_test(cmd)

    def test_invert_match_long(self):
        cmd = ["--invert-match", "pipe", "test.py"]
        self._run_test(cmd)

    def test_non_existent_file(self):
        cmd = ["pipe", "test.py___"]
        self._run_test(cmd)

    def test_multiple_files(self):
        cmd = ["a", "test.py", "grep.py"]
        self._run_test(cmd)

    def test_multiple_files__invert_match(self):
        cmd = ["-v", "a", "test.py", "grep.py"]
        self._run_test(cmd)

    def test_multiple_regexp_short(self):
        cmd = ["-E", "a+", "test.py"]
        self._run_test(cmd)

    def test_multiple_regexp_long(self):
        cmd = ["--extended-regexp", "a+", "test.py"]
        self._run_test(cmd)

    def test_binary_file(self):
        cmd = ["a", "/usr/bin/grep"]
        self._run_test(cmd)

    def test_recursive_short(self):
        cmd = ["-r", "a", TEST_DATA_BASE]
        self._run_test(cmd, sort=True)

    def test_recursive_long(self):
        cmd = ["--recursive", "a", TEST_DATA_BASE]
        self._run_test(cmd, sort=True)

    def test_recursive_without_file(self):
        cmd = ["-r", "a"]
        self._run_test(cmd, sort=True)

    def test_color(self):
        cmd = ["--color=always", "pipe", "test.py"]
        self._run_test(cmd)

    def test_nocolor(self):
        cmd = ["--color=never", "pipe", "test.py"]
        self._run_test(cmd)

    def test_random(self):
        flags = [
            "-i",
            "--ignore-case",
            "-v",
            "--invert-match",
            "-E",
            "--extended-regexp",
            "-r",
            "--recursive",
            "--color=always",
            "--color=never",
        ]
        patterns = ["a", "A", "a+"]
        files = [TEST_DATA_BASE] + list(TEST_DATA_BASE)

        for _ in range(5):
            flag = random.sample(flags, k=random.randint(1, 3))
            pattern = random.sample(patterns, k=random.randint(1, 3))
            file = random.sample(files, k=random.randint(1, 3))

            cmd = flag + pattern + file
            self._run_test(cmd, sort=True)


if __name__ == "__main__":
    unittest.main()
