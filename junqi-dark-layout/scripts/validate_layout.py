#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path

ROWS = 6
COLS = 5
VALID_CELLS = {
    0,1,2,3,4,
    5,7,9,
    10,11,13,14,
    15,17,19,
    20,21,22,23,24,
    25,26,27,28,29,
}
HQ_CELLS = {26, 28}
MINE_CELLS = {20,21,22,23,24,25,27,29}
FRONT_ROW_CELLS = {0,1,2,3,4}

PIECE_COUNTS = {
    "司令": 1,
    "军长": 1,
    "师长": 2,
    "旅长": 2,
    "团长": 2,
    "营长": 2,
    "连长": 3,
    "排长": 3,
    "工兵": 3,
    "炸弹": 2,
    "地雷": 3,
    "军旗": 1,
}

ALL_ALLOWED_VALUES = set(PIECE_COUNTS) | {"禁"}


def load_layout(raw: str):
    text = raw.strip()
    if text.startswith("["):
        return json.loads(text)
    path = Path(text)
    return json.loads(path.read_text(encoding="utf-8"))


def validate_layout(layout):
    errors = []
    checks = {}

    checks["layout_length_ok"] = len(layout) == ROWS * COLS
    if not checks["layout_length_ok"]:
        errors.append(f"布局长度错误：应为 {ROWS * COLS}，实际为 {len(layout)}")
        return {"valid": False, "errors": errors, "checks": checks}

    checks["cell_values_known"] = all(cell in ALL_ALLOWED_VALUES for cell in layout)
    if not checks["cell_values_known"]:
        errors.append("存在未知棋子或非法单元值")

    forbidden_ok = True
    for idx in range(ROWS * COLS):
        if idx not in VALID_CELLS and layout[idx] != "禁":
            forbidden_ok = False
            break
    checks["forbidden_cells_ok"] = forbidden_ok
    if not forbidden_ok:
        errors.append("禁摆位未保持为“禁”")

    valid_cells_no_forbidden = True
    for idx in VALID_CELLS:
        if layout[idx] == "禁":
            valid_cells_no_forbidden = False
            break
    checks["valid_cells_filled"] = valid_cells_no_forbidden
    if not valid_cells_no_forbidden:
        errors.append("可摆位中出现“禁”，说明布局不完整")

    counts = Counter(layout)
    piece_counts_ok = True
    for piece, expected in PIECE_COUNTS.items():
        if counts[piece] != expected:
            piece_counts_ok = False
            errors.append(f"{piece} 数量错误：应为 {expected}，实际为 {counts[piece]}")
    checks["piece_counts_ok"] = piece_counts_ok

    flag_positions = [i for i, p in enumerate(layout) if p == "军旗"]
    flag_in_hq = len(flag_positions) == 1 and flag_positions[0] in HQ_CELLS
    checks["flag_in_hq"] = flag_in_hq
    if not flag_in_hq:
        errors.append("军旗必须且只能位于大本营（第6排第2列或第4列）")

    mines_legal = True
    for idx, piece in enumerate(layout):
        if piece == "地雷" and idx not in MINE_CELLS:
            mines_legal = False
            break
    checks["mines_legal"] = mines_legal
    if not mines_legal:
        errors.append("地雷只能放在后两排合法雷区，且不能进入大本营")

    bombs_not_in_front_row = True
    for idx in FRONT_ROW_CELLS:
        if layout[idx] == "炸弹":
            bombs_not_in_front_row = False
            break
    checks["bombs_not_in_front_row"] = bombs_not_in_front_row
    if not bombs_not_in_front_row:
        errors.append("炸弹不能放在第一排")

    # HQ pieces cannot move, so HQ should only hold 军旗 or low-value pieces
    # (typically 排长/连长), never big pieces / 工兵 / 炸弹
    hq_piece_ok = True
    forbidden_hq_pieces = {"司令", "军长", "师长", "旅长", "团长", "营长", "工兵", "炸弹"}
    for idx in HQ_CELLS:
        if layout[idx] in forbidden_hq_pieces:
            hq_piece_ok = False
            break
    checks["hq_piece_ok"] = hq_piece_ok
    if not hq_piece_ok:
        errors.append("大本营只允许放军旗或低价值子（排长/连长），不能放大子、工兵、炸弹")

    valid = all(checks.values())
    return {
        "valid": valid,
        "errors": errors,
        "checks": checks,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate a Junqi 25-cell layout")
    parser.add_argument("--layout", required=True, help="JSON array string or path to a JSON file")
    args = parser.parse_args()

    layout = load_layout(args.layout)
    result = validate_layout(layout)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
