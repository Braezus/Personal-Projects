from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Tuple


class TerraformError(RuntimeError):
  pass


def run_terraform_plan(terraform_dir: Path, plan_path: Path) -> Tuple[int, str, str]:
  """Run `terraform plan -refresh-only -detailed-exitcode`.

  Returns (exit_code, stdout, stderr).
  """
  cmd = [
    "terraform",
    "plan",
    "-refresh-only",
    "-detailed-exitcode",
    "-out",
    str(plan_path),
  ]

  proc = subprocess.Popen(
    cmd,
    cwd=str(terraform_dir),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
  )
  stdout, stderr = proc.communicate()
  return proc.returncode, stdout, stderr


def export_plan_json(terraform_dir: Path, plan_path: Path, json_path: Path) -> None:
  """Run `terraform show -json` and write to json_path."""
  cmd = [
    "terraform",
    "show",
    "-json",
    str(plan_path),
  ]
  proc = subprocess.Popen(
    cmd,
    cwd=str(terraform_dir),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
  )
  stdout, stderr = proc.communicate()
  if proc.returncode != 0:
    raise TerraformError(
      f"terraform show failed with code {proc.returncode}: {stderr}"
    )

  # Validate JSON before writing for clearer errors
  try:
    parsed = json.loads(stdout)
  except json.JSONDecodeError as exc:
    raise TerraformError(f"Invalid JSON from terraform show: {exc}") from exc

  json_path.write_text(json.dumps(parsed, indent=2))

