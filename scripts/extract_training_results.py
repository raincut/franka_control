"""Extract embedded notebook figures and HTML tables into Markdown."""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "training_results"
ASSETS = OUT / "assets"
NOTEBOOKS = {
    "A — Distance-Layered": ROOT / "notebooks/Franka_A_Formal500k_DistanceLayered_AutoDL_MuJoCo3_output.ipynb",
    "B — Dense-to-Sparse": ROOT / "notebooks/Franka_B_Formal500k_Dense2Sparse_AutoDL_MuJoCo3_output.ipynb",
    "C — Force Feedback": ROOT / "notebooks/Franka_Advanced_ForceFeedback_SAC_HER_AutoDL_MuJoCo3_outpu.ipynb",
}


def text(value) -> str:
    return "".join(value) if isinstance(value, list) else str(value)


def table_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        return ""
    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if cells:
            rows.append([re.sub(r"\s+", " ", c.get_text(" ", strip=True)).replace("|", "\\|") for c in cells])
    if not rows:
        return ""
    width = max(map(len, rows))
    rows = [r + [""] * (width - len(r)) for r in rows]
    result = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
    result.extend("| " + " | ".join(r) + " |" for r in rows[1:])
    return "\n".join(result)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = ["# Franka RL Training Results", "", "Extracted from the executed outputs of the three formal 500k-step notebooks.", ""]
    for label, notebook_path in NOTEBOOKS.items():
        data = json.loads(notebook_path.read_text(encoding="utf-8"))
        safe = re.sub(r"[^A-Za-z0-9]+", "_", label).strip("_")
        asset_dir = ASSETS / safe
        asset_dir.mkdir(parents=True, exist_ok=True)
        lines += [f"## {label}", "", f"Source: `{notebook_path.name}`", ""]
        image_index = table_index = 0
        for cell in data.get("cells", []):
            for output in cell.get("outputs", []):
                od = output.get("data", {})
                for mime, ext in (("image/png", "png"), ("image/jpeg", "jpg")):
                    if mime in od:
                        image_index += 1
                        filename = f"figure_{image_index:02d}.{ext}"
                        (asset_dir / filename).write_bytes(base64.b64decode(text(od[mime])))
                        lines += [f"### Figure {image_index}", "", f"![{label} figure {image_index}](training_results/assets/{safe}/{filename})", ""]
                if "text/html" in od:
                    table = table_markdown(text(od["text/html"]))
                    if table:
                        table_index += 1
                        lines += [f"### Table {table_index}", "", table, ""]
        if not image_index:
            lines += ["No embedded figures found.", ""]
        if not table_index:
            lines += ["No HTML tables found.", ""]
    (ROOT / "docs" / "TRAINING_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
