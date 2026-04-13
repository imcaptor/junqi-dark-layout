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
HQ_CELLS = {26, 28}
MINE_CELLS = {20,21,22,23,24,25,27,29}
FRONT_ROW_CELLS = {0,1,2,3,4}
ACTIVE_MINER_ZONE = {5,7,9,10,11,13,14,15,17,19,20,21,22,23,24}
BACKLINE_MINER_ZONE = {25,27,29}

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

ATTACKERS = ["司令", "军长", "师长", "师长", "旅长", "旅长", "团长", "团长", "营长", "营长"]
SMALLS = ["连长", "连长", "连长", "排长", "排长", "排长"]

STYLE_PROFILES = {
    "稳健": {
        "attacker_rows": [1, 2, 3, 4],
        "small_rows": [0, 1, 2, 3, 4],
        "bomb_rows": [1, 2, 3],
        "miner_rows": [2, 3, 4],
        "front_attackers_min": 1,
        "active_miners_min": 1,
    },
    "激进": {
        "attacker_rows": [0, 1, 2, 3],
        "small_rows": [0, 1, 2, 3, 4],
        "bomb_rows": [1, 2, 3],
        "miner_rows": [1, 2, 3],
        "front_attackers_min": 3,
        "active_miners_min": 1,
    },
    "阴阵": {
        "attacker_rows": [1, 2, 3, 4],
        "small_rows": [0, 1, 2, 3, 4],
        "bomb_rows": [1, 2, 3],
        "miner_rows": [1, 2, 3, 4],
        "front_attackers_min": 1,
        "active_miners_min": 1,
    },
    "均衡": {
        "attacker_rows": [1, 2, 3, 4],
        "small_rows": [0, 1, 2, 3, 4],
        "bomb_rows": [1, 2, 3],
        "miner_rows": [1, 2, 3, 4],
        "front_attackers_min": 2,
        "active_miners_min": 1,
    },
}


def row_of(idx: int) -> int:
    return idx // COLS


def col_of(idx: int) -> int:
    return idx % COLS


def valid_row_cells(row_zero_based: int) -> List[int]:
    return [idx for idx in sorted(VALID_CELLS) if row_of(idx) == row_zero_based]


def unique_candidates(rows_pref: List[int], lane: str = "center") -> List[int]:
    cells = []
    seen = set()
    for r in rows_pref:
        rr = max(0, min(ROWS - 1, r))
        for idx in valid_row_cells(rr):
            if idx not in seen:
                seen.add(idx)
                cells.append(idx)
    if lane == "left":
        cells.sort(key=lambda i: (abs(col_of(i)-1), row_of(i), col_of(i)))
    elif lane == "right":
        cells.sort(key=lambda i: (abs(col_of(i)-3), row_of(i), col_of(i)))
    else:
        cells.sort(key=lambda i: (abs(col_of(i)-2), row_of(i), col_of(i)))
    return cells


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

    preferred = [20, 21, 22, 25, 27] if flag_idx == 26 else [22, 23, 24, 27, 29]
    pool = preferred + [idx for idx in sorted(MINE_CELLS) if idx not in preferred]
    for idx in pool:
        if board[idx] == "空":
            board[idx] = "地雷"
            if sum(1 for p in board if p == "地雷") == 3:
                break


def place_bombs(board: List[str], rows_pref: List[int], rnd: random.Random):
    candidates = [idx for idx in unique_candidates(rows_pref) if idx not in FRONT_ROW_CELLS]
    for _ in range(2):
        board[choose_empty(board, candidates, rnd)] = "炸弹"


def place_attackers(board: List[str], rows_pref: List[int], rnd: random.Random, lane: str, front_attackers_min: int):
    front_cells = [idx for idx in FRONT_ROW_CELLS if board[idx] == "空"]
    front_need = min(front_attackers_min, len(front_cells), len(ATTACKERS))
    front_choices = ATTACKERS[:]
    rnd.shuffle(front_choices)

    chosen_front = set()
    for piece in front_choices[:front_need]:
        opts = [idx for idx in front_cells if idx not in chosen_front and board[idx] == "空"]
        if not opts:
            break
        idx = rnd.choice(opts)
        chosen_front.add(idx)
        board[idx] = piece

    remaining = [p for p in ATTACKERS]
    placed_counter = Counter(v for v in board if v in ATTACKERS)
    for piece, count in placed_counter.items():
        for _ in range(count):
            remaining.remove(piece)

    candidates = unique_candidates(rows_pref, lane)
    rnd.shuffle(remaining)
    for piece in remaining:
        idx = choose_empty(board, candidates, rnd)
        board[idx] = piece


def place_smalls(board: List[str], rows_pref: List[int], rnd: random.Random, lane: str, max_front_smalls: int):
    front_small_now = sum(1 for idx in FRONT_ROW_CELLS if board[idx] in {"连长", "排长"})
    front_available = [idx for idx in FRONT_ROW_CELLS if board[idx] == "空"]
    allowed_front_more = max(0, max_front_smalls - front_small_now)

    front_fill = min(allowed_front_more, len(front_available), len(SMALLS))
    pieces = SMALLS[:]
    rnd.shuffle(pieces)

    chosen_front = set()
    for piece in pieces[:front_fill]:
        opts = [idx for idx in front_available if idx not in chosen_front and board[idx] == "空"]
        if not opts:
            break
        idx = rnd.choice(opts)
        chosen_front.add(idx)
        board[idx] = piece

    remaining = pieces[len(chosen_front):]
    candidates = unique_candidates(rows_pref, lane)
    for piece in remaining:
        idx = choose_empty(board, candidates, rnd)
        board[idx] = piece


def place_miners(board: List[str], rows_pref: List[int], rnd: random.Random, lane: str, active_miners_min: int):
    active_candidates = [idx for idx in unique_candidates(rows_pref + [4], lane) if idx in ACTIVE_MINER_ZONE]
    all_candidates = unique_candidates(rows_pref + [4, 5], lane)

    for _ in range(active_miners_min):
        board[choose_empty(board, active_candidates, rnd)] = "工兵"
    while sum(1 for p in board if p == "工兵") < 3:
        board[choose_empty(board, all_candidates, rnd)] = "工兵"


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


def front_attackers_count(board: List[str]) -> int:
    return sum(1 for idx in FRONT_ROW_CELLS if board[idx] in set(ATTACKERS))


def front_smalls_count(board: List[str]) -> int:
    return sum(1 for idx in FRONT_ROW_CELLS if board[idx] in {"连长", "排长"})


def active_miners_count(board: List[str]) -> int:
    return sum(1 for idx in ACTIVE_MINER_ZONE if board[idx] == "工兵")


def back_miners_count(board: List[str]) -> int:
    return sum(1 for idx in BACKLINE_MINER_ZONE if board[idx] == "工兵")


def score(board: List[str], style: str, focus: str) -> Dict[str, int]:
    flag_idx = board.index("军旗")
    big_positions = [i for i, p in enumerate(board) if p in {"司令", "军长", "师长", "旅长"}]
    bomb_positions = [i for i, p in enumerate(board) if p == "炸弹"]
    mine_positions = [i for i, p in enumerate(board) if p == "地雷"]

    conceal = 55
    if flag_idx == 26 and any(i in mine_positions for i in [21, 25, 27]):
        conceal += 14
    if flag_idx == 28 and any(i in mine_positions for i in [23, 27, 29]):
        conceal += 14

    defense = 55 + sum(5 for i in big_positions if row_of(i) >= 2) + sum(5 for _ in mine_positions)
    offense = 48 + sum(8 for i in big_positions if row_of(i) <= 3) + sum(6 for i in bomb_positions if row_of(i) <= 3)
    miner_mobility = 45 + active_miners_count(board) * 15 - back_miners_count(board) * 12

    offense += front_attackers_count(board) * 8
    offense -= front_smalls_count(board) * 7

    if style == "激进":
        offense += 10
    if style == "阴阵":
        conceal += 10
    if focus == "保旗":
        defense += 8
    elif focus == "中攻":
        offense += 12
        miner_mobility += 8
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
        f"前排进攻子 {front_attackers_count(board)} 个，前中场可动工兵 {active_miners_count(board)} 个；隐蔽/防守/进攻约为 {scores['隐蔽']}/{scores['防守']}/{scores['进攻']}。",
        "已限制前排小子过多，并强制保留至少一个前中场工兵。",
    ]


def generate(style: str, focus: str, seed: int = None) -> Tuple[List[str], Dict[str, int], List[str]]:
    style = style if style in STYLE_PROFILES else "稳健"
    profile = STYLE_PROFILES[style]
    rnd = random.Random(seed)

    best = None
    best_total = -1

    front_attackers_min = profile["front_attackers_min"]
    active_miners_min = profile["active_miners_min"]
    max_front_smalls = 2

    attacker_rows = profile["attacker_rows"]
    small_rows = profile["small_rows"]
    miner_rows = profile["miner_rows"]

    if focus == "保旗":
        attacker_rows = [1, 2, 3, 4]
        miner_rows = [2, 3, 4]
        front_attackers_min = max(1, front_attackers_min - 1)
    elif focus == "中攻":
        attacker_rows = [0, 1, 2, 3]
        miner_rows = [1, 2, 3]
        front_attackers_min = max(front_attackers_min, 3)
        active_miners_min = max(active_miners_min, 1)
        max_front_smalls = 1
    elif focus == "迷惑":
        attacker_rows = [1, 2, 3, 4]
        miner_rows = [1, 2, 3]

    for _ in range(500):
        board = ["禁"] * (ROWS * COLS)
        for idx in VALID_CELLS:
            board[idx] = "空"

        place_flag_and_mines(board, rnd)
        place_bombs(board, profile["bomb_rows"], rnd)

        lane = "center"
        if focus == "侧攻":
            lane = rnd.choice(["left", "right"])

        place_attackers(board, attacker_rows, rnd, lane, front_attackers_min)
        place_smalls(board, small_rows, rnd, lane, max_front_smalls)
        place_miners(board, miner_rows, rnd, lane, active_miners_min)

        try:
            validate(board)
        except Exception:
            continue

        if front_attackers_count(board) < front_attackers_min:
            continue
        if active_miners_count(board) < active_miners_min:
            # Treat miner activity as a soft preference rather than a hard legality gate.
            pass
        if front_smalls_count(board) > max_front_smalls:
            continue

        scores = score(board, style, focus)
        total = scores["隐蔽"] + scores["防守"] + scores["进攻"] + scores["工兵机动"]
        total += front_attackers_count(board) * 10
        total += active_miners_count(board) * 16
        total -= front_smalls_count(board) * 12
        total -= back_miners_count(board) * 16

        if focus == "中攻":
            total += scores["进攻"]
        elif focus == "迷惑":
            total += scores["隐蔽"]
        elif focus == "保旗":
            total += scores["防守"]

        if best is None or total > best_total:
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
