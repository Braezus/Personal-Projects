from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import List


def main(argv: List[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Apply Terraform remediation for a given environment."
  )
  parser.add_argument(
    "--env-path",
    required=True,
    help="Path to the Terraform environment directory.",
  )
  args = parser.parse_args(argv)

  env_dir = Path(args.env_path).resolve()

  cmd = ["terraform", "apply", "-auto-approve"]
  proc = subprocess.Popen(
    cmd,
    cwd=str(env_dir),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
  )
  stdout, stderr = proc.communicate()

  print(stdout)
  if proc.returncode != 0:
    print(stderr)
  return proc.returncode


if __name__ == "__main__":
  raise SystemExit(main())

