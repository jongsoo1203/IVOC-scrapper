from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, PatternFill, Side


@dataclass(frozen=True)
class ReportWriter:
    data_dir: Path

    def write_csv(self, rows: list[list[str]], filename: str) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        out = self.data_dir / filename

        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n", quoting=csv.QUOTE_ALL)
            w.writerows(rows)

        return out

    def csv_to_styled_xlsx(self, csv_path: Path) -> Path:
        df = pd.read_csv(csv_path, header=None, parse_dates=[0])
        out_xlsx = csv_path.with_suffix(".xlsx")

        # Save initial XLSX
        df.to_excel(out_xlsx, index=False, header=False)

        color_map = {
            "green": PatternFill(start_color="92D050", end_color="92D050", fill_type="solid"),
            "darkblue": PatternFill(start_color="9DC3E6", end_color="9DC3E6", fill_type="solid"),
            "orange": PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid"),
            "lightblue": PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid"),
            "grey": PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid"),
            "peach": PatternFill(start_color="FBE5D6", end_color="FBE5D6", fill_type="solid"),
            "yellow": PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid"),
        }

        color_keywords = [
            ("green", ["tab", "bud", "watch", "xr"]),
            ("darkblue", ["s21"]),
            ("orange", ["s22"]),
            ("lightblue", ["s23"]),
            ("grey", ["s24"]),
            ("peach", ["s25"]),
            ("yellow", ["flip", "fold"]),
        ]

        priority = {"green": 7, "darkblue": 6, "orange": 5, "lightblue": 4, "grey": 3, "peach": 2, "yellow": 1}

        def row_color(row) -> str | None:
            last = None
            for color, keys in color_keywords:
                if any(any(k in str(row[col]).lower() for k in keys) for col in [4, 3, 2]):
                    last = color
            return last

        df["__color__"] = df.apply(row_color, axis=1)
        df["__priority__"] = df["__color__"].map(priority).fillna(999)
        df = df.sort_values("__priority__").reset_index(drop=True)
        df.drop(columns="__priority__").to_excel(out_xlsx, index=False, header=False)

        wb = load_workbook(out_xlsx)
        ws = wb.active

        thin = Side(border_style="thin", color="000000")
        border = Border(top=thin, left=thin, right=thin, bottom=thin)
        wrap = Alignment(wrap_text=True)

        for i, row in df.iterrows():
            ws.row_dimensions[i + 1].height = 13.8
            c = row["__color__"]
            for col in range(1, ws.max_column):
                cell = ws.cell(row=i + 1, column=col)
                if c and col == 3:
                    cell.fill = color_map[c]
                cell.border = border
                cell.alignment = wrap

        # remove __color__ col
        ws.delete_cols(ws.max_column)
        wb.save(out_xlsx)
        return out_xlsx
