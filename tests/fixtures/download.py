#!/usr/bin/env python3
"""Deterministic curl/wget replacement for installer subprocess tests."""

import os
import shutil
import sys
from pathlib import Path

args = sys.argv[1:]
url = next(arg for arg in args if arg.startswith("https://"))
output_flag = "-o" if "-o" in args else "-O"
output = Path(args[args.index(output_flag) + 1])
with Path(os.environ["REQUEST_LOG"]).open("a", encoding="utf-8") as log:
    log.write(url + "\n")
if "/commits/main" in url:
    if os.environ.get("FAIL_RESOLVE") == "1":
        sys.exit(22)
    output.write_text("a" * 40, encoding="utf-8")
else:
    relative = url.split("/AutoEvolve/", 1)[1].split("/", 1)[1]
    if relative == os.environ.get("FAIL_FILE"):
        output.write_text("partial download", encoding="utf-8")
        sys.exit(0 if os.environ.get("CORRUPT_FILE") == "1" else 22)
    shutil.copyfile(Path(os.environ["FIXTURE_SOURCE"]) / relative, output)
