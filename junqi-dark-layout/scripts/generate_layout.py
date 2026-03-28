#!/usr/bin/env python3
import argparse
import json
import random
from collections import Counter
from typing import Dict, List, Tuple

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
HQ_CELLS = {26, 28}  # row6 col2/4
MINE_CELLS = {20,21,22,23,24,25,27,29}  # rows 5 and 6 except HQ cells
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

STYLE_PROFILES = {
    "稳健": {"big_rows": [3, 4, 2], "bomb_rows": [1, 3, 2], "miner_rows": [3, 4, 1]},
    "激进": {"big_rows": [1, 2, 3], "bomb_rows": [2, 3, 1], "miner_rows": [2, 3, 4]},
    "阴阵": {"big_rows": [4, 3, 2], "bomb_rows": [2, 3, 1], "miner_rows": [3, 4, 2]},
    "均衡": {"big_rows": [2, 3, 4], "bomb_rows": [1, 2, 3], "miner_rows": [2, 3, 4]},
}

BIG_PIECES = ["司令", "军长", "师长", "师长", "旅长", "旅长"]
MID_PIECES = ["团长", "团长", "营长", "营长", "连长", "连长", "连长", "排长", "排长", "排长"]
MINERS = ["工兵", "工兵", "工兵"]


def row_of(idx: int) -> int:
    return idx // COLS


def col_of(idx: int) -> int:
    return idx % COLS


def valid_row_cells(row_zero_based: int) -> List[int]:
    return [idx for idx in sorted(VALID_CELLS) if row_of(idx) == row_zero_based]


def choose_empty(board: List[str], candidates: List[int], rnd: random.Random) -> int:
    opts = [idx for idx in candidates if board[idx] == "空"]
    if not opts:
        opts = [idx for idx in sorted(VALID_CELLS) if board[idx] == "空"]
    if not opts:
        raise ValueError("no empty candidate cell available")
    return rnd.choice(opts)


def place_flag_and_mines(board: List[str], rnd: random.Random):
    flag_idx = rnd.choice(sorted(HQ_CELLS))
    board[flag_idx] = "军旗"

    preferred = []
    if flag_idx == 26:
        preferred = [20, 21, 22, 25, 27]
    else:
        preferred = [22, 23, 24, 27, 29]
    pool = preferred + [idx for idx in sorted(MINE_CELLS) if idx not in preferred]

    chosen = []
    for idx in pool:
        if idx != flag_idx and board[idx] == "空":
            chosen.append(idx)
        if len(chosen) == 3:
            break
    for idx in chosen:
        board[idx] = "地雷"


def place_bombs(board: List[str], rows_pref: List[int], rnd: random.Random):
    candidates = []
    for r in rows_pref:
        rr = max(0, min(ROWS - 1, r))
        candidates.extend(valid_row_cells(rr))
    candidates = [c for c in candidates if c not in FRONT_ROW_CELLS]
    for _ in range(2):
        idx = choose_empty(board, candidates, rnd)
        board[idx] = "炸弹"


def place_pieces(board: List[str], pieces: List[str], rows_pref: List[int], rnd: random.Random, lane: str = "center"):
    candidates = []
    for r in rows_pref:
        rr = max(0, min(ROWS - 1, r))
        candidates.extend(valid_row_cells(rr))

    unique_candidates = []
    seen = set()
    for idx in candidates:
        if idx in seen:
            continue
        seen.add(idx)
        unique_candidates.append(idx)

    if lane == "left":
        unique_candidates.sort(key=lambda i: (abs(col_of(i)-1), row_of(i)))
    elif lane == "right":
        unique_candidates.sort(key=lambda i: (abs(col_of(i)-3), row_of(i)))
    else:
        unique_candidates.sort(key=lambda i: (abs(col_of(i)-2), row_of(i)))

    for piece in pieces:
        idx = choose_empty(board, unique_candidates, rnd)
        board[idx] = piece


def validate(board: List[str]):
    if len(board) != ROWS * COLS:
        raise ValueError("board size mismatch")
    for idx in range(ROWS * COLS):
        if idx not in VALID_CELLS and board[idx] != "禁":
            raise ValueError(f"invalid hole cell {idx} must be 禁")

    counts = Counter(board)
    for piece, expected in PIECE_COUNTS.items():
        if counts[piece] != expected:
            raise ValueError(f"{piece} count mismatch: {counts[piece]} != {expected}")

    flag_positions = [i for i, p in enumerate(board) if p == "军旗"]
    if len(flag_positions) != 1 or flag_positions[0] not in HQ_CELLS:
        raise ValueError("军旗 must be in row6 col2 or col4")

    for idx, piece in enumerate(board):
        if piece == "地雷" and idx not in MINE_CELLS:
            raise ValueError("地雷只能在后两排且不能在大本营")
        if piece == "炸弹" and idx in FRONT_ROW_CELLS:
            raise ValueError("炸弹不能在第一排")


def score(board: List[str], style: str, focus: str) -> Dict[str, int]:
    flag_idx = board.index("军旗")
    big_positions = [i for i, p in enumerate(board) if p in {"司令", "军长", "师长", "旅长"}]
    bomb_positions = [i for i, p in enumerate(board) if p == "炸弹"]
    miner_positions = [i for i, p in enumerate(board) if p == "工兵"]
    mine_positions = [i for i, p in enumerate(board) if p == "地雷"]

    conceal = 55
    if flag_idx == 26:
        if 25 in mine_positions or 27 in mine_positions or 21 in mine_positions:
            conceal += 14
    else:
        if 27 in mine_positions or 29 in mine_positions or 23 in mine_positions:
            conceal += 14
    conceal += sum(3 for i in bomb_positions if row_of(i) in {2, 3})

    defense = 55 + sum(5 for i in big_positions if row_of(i) >= 2) + sum(5 for i in mine_positions)
    offense = 50 + sum(7 for i in big_positions if row_of(i) <= 3) + sum(7 for i in bomb_positions if row_of(i) <= 3)
    miner_mobility = 45 + sum(10 for i in miner_positions if row_of(i) <= 3)

    if style == "激进":
        offense += 10
    if style == "阴阵":
        conceal += 10
    if focus == "保旗":
        defense += 8
    elif focus == "中攻":
        offense += 8
    elif focus == "迷惑":
        conceal += 12

    return {
        "隐蔽": max(1, min(100, conceal)),
        "防守": max(1, min(100, defense)),
        "进攻": max(1, min(100, offense)),
        "工兵机动": max(1, min(100, miner_mobility)),
    }


def explain(board: List[str], style: str, focus: str, scores: Dict[str, int]) -> List[str]:
    flag_idx = board.index("军旗")
    side = "第6排第2列" if flag_idx == 26 else "第6排第4列"
    return [
        f"风格：{style}｜侧重：{focus}｜军旗在{side}。",
        f"地雷只放后两排且避开大本营；隐蔽/防守/进攻约为 {scores['隐蔽']}/{scores['防守']}/{scores['进攻']}。",
        "前中场保留试探与突击子，整体更像真实军棋 25 格布阵。",
    ]


def generate(style: str, focus: str, seed: int = None) -> Tuple[List[str], Dict[str, int], List[str]]:
    style = style if style in STYLE_PROFILES else "稳健"
    profile = STYLE_PROFILES[style]
    rnd = random.Random(seed)

    best = None
    best_total = -1

    for _ in range(200):
        board = ["禁"] * (ROWS * COLS)
        for idx in VALID_CELLS:
            board[idx] = "空"

        place_flag_and_mines(board, rnd)
        place_bombs(board, profile["bomb_rows"], rnd)

        lane = "center"
        if focus == "侧攻":
            lane = rnd.choice(["left", "right"])

        big_rows = profile["big_rows"]
        if focus == "保旗":
            big_rows = [4, 3, 2]
        elif focus == "中攻":
            big_rows = [1, 2, 3]
        elif focus == "迷惑":
            big_rows = [2, 3, 4]

        place_pieces(board, BIG_PIECES, big_rows, rnd, lane)
        place_pieces(board, MID_PIECES, [0, 1, 2, 3, 4], rnd, lane)
        place_pieces(board, MINERS, profile["miner_rows"], rnd, lane)

        try:
            validate(board)
        except Exception:
            continue

        scores = score(board, style, focus)
        total = scores["隐蔽"] + scores["防守"] + scores["进攻"] + scores["工兵机动"]
        if focus == "迷惑":
            total += scores["隐蔽"]
        elif focus == "保旗":
            total += scores["防守"]
        elif focus == "中攻":
            total += scores["进攻"]

        if total > best_total:
            best_total = total
            best = board[:]

    if best is None:
        raise RuntimeError("failed to generate a legal layout under the 25-cell board model")

    scores = score(best, style, focus)
    notes = explain(best, style, focus, scores)
    return best, scores, notes


def main():
    parser = argparse.ArgumentParser(description="Generate a Junqi dark-chess layout on the standard 25-cell board")
    parser.add_argument("--style", default="稳健")
    parser.add_argument("--focus", default="均衡")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    board, scores, notes = generate(args.style, args.focus, args.seed)
    print(json.dumps({
        "style": args.style,
        "focus": args.focus,
        "layout": board,
        "scores": scores,
        "notes": notes,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
