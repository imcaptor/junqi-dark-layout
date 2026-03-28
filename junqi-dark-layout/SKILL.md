---
name: junqi-dark-layout
description: Generate a legal Chinese Army Chess (军棋) dark-layout setup on the standard 25-cell 2-player board and render it as a clear image card. Use when the user wants a 军棋暗棋摆阵, asks for a ready-to-use hidden setup, gives style/focus preferences, or wants the final answer as an image instead of only text.
---

# Junqi Dark Layout

Generate one valid 2-player 军棋暗棋 layout from the user's requested style/focus and output it as a clean practical card image.

## Workflow

1. Assume the standard 2-player 25-cell dark-chess board unless the user specifies a different platform.
2. Respect these constraints unless the user gives different platform rules:
   - The board has 25 legal cells and 5 fixed forbidden cells.
   - 军旗 must be in a 大本营.
   - 军旗 only in row 6 column 2 or row 6 column 4.
   - 地雷 only in the last two rows and never in a 大本营.
   - 炸弹 cannot be in the first row.
3. Generate dynamically from the user's requested style and focus instead of reusing a fixed template.
4. Prefer a balanced, practical layout over a flashy one:
   - Hide the flag naturally.
   - Do not cluster all big pieces together.
   - Keep at least one useful 工兵 path for late-game mine clearing.
   - Spread pressure so one side is not obviously weak.
5. Produce the result as an image first when the user asked for a picture. Include a short text explanation only if helpful.

## Standard 25-cell board model

Use a 5-column by 6-row own-side layout with these legal cells:

- Row 1: columns 1 2 3 4 5
- Row 2: columns 1 3 5
- Row 3: columns 1 2 4 5
- Row 4: columns 1 3 5
- Row 5: columns 1 2 3 4 5
- Row 6: columns 1 2 3 4 5

Fixed forbidden cells:
- Row 2 column 2
- Row 2 column 4
- Row 3 column 3
- Row 4 column 2
- Row 4 column 4

大本营 positions:
- Row 6 column 2
- Row 6 column 4

地雷 legal cells:
- Row 5 columns 1 2 3 4 5
- Row 6 columns 1 3 5

## Piece set

Use this exact 25-piece set unless the user specifies a different variant:

- 司令 ×1
- 军长 ×1
- 师长 ×2
- 旅长 ×2
- 团长 ×2
- 营长 ×2
- 连长 ×3
- 排长 ×3
- 工兵 ×3
- 炸弹 ×2
- 地雷 ×3
- 军旗 ×1

## Output rules

- If the user wants a layout only, return one fresh generated setup.
- If the user wants options, offer 2-3 styles at most: 稳健 / 激进 / 阴阵.
- If an image is requested, generate the layout first with `scripts/generate_layout.py`, then render it with `scripts/render_layout.py`.
- Keep explanations concise and practical.
- Avoid pretending platform-specific certainty when the exact app rules are unknown.

## Dynamic generation

Generate a fresh layout first, then render it.

Example:

```bash
python3 scripts/generate_layout.py --style 激进 --focus 迷惑 > /tmp/junqi.json
python3 scripts/render_layout.py \
  --title "军棋暗棋摆阵" \
  --subtitle "激进型｜偏迷惑" \
  --layout '...30-cell JSON array including 禁 for forbidden cells...' \
  --notes '["...", "...", "..."]' \
  --output /tmp/junqi-layout.png
```

Supported style values:
- `稳健`
- `激进`
- `阴阵`
- `均衡`

Supported focus values:
- `均衡`
- `保旗`
- `中攻`
- `侧攻`
- `迷惑`

The renderer produces a clean practical card image:
- readable 6×5 board with the 25 legal cells
- forbidden cells shown as 禁摆位
- 大本营 / 雷区 / 首排限制 visually distinguished
- short notes at the bottom

## Default behavior

If the user gives no preference:
- style = `稳健`
- focus = `均衡`

Then generate one fresh legal layout instead of reusing a static preset.

## Validation checklist

Before returning the answer, verify:

- Count of each piece is correct.
- Forbidden cells remain forbidden.
- 军旗 is in row 6 column 2 or row 6 column 4.
- All 地雷 are only in row 5 or row 6 columns 1/3/5.
- No 地雷 is placed in a 大本营.
- No 炸弹 is in row 1.
- The exported layout contains 30 entries only because the 5 forbidden cells are marked as `禁` for rendering.

## Files

- `scripts/generate_layout.py`: generate one fresh legal layout from style/focus hints on the standard 25-cell board.
- `scripts/render_layout.py`: render one layout card image from JSON layout input.
