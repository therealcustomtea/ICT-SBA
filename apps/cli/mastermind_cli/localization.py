"""Traditional Chinese copy for the original offline terminal workflow."""
# ruff: noqa: RUF001 -- Full-width punctuation is intentional in translated copy.

from __future__ import annotations

import re

MESSAGES = {
    "Mastermind Logic Lab": "Mastermind 邏輯實驗室",
    "1. Start game": "1. 開始遊戲",
    "2. View local high scores": "2. 查看本機最高分",
    "3. View rules": "3. 查看規則",
    "4. Export scores": "4. 匯出分數",
    "5. Exit": "5. 離開",
    "6. Online features (same account as the GUI)": "6. 線上功能（與圖形介面使用相同帳戶）",
    "Choose an option: ": "請選擇：",
    "Player name: ": "玩家名稱：",
    "1. Easy  2. Normal  3. Hard  4. Expert  5. Custom": (
        "1. 容易  2. 普通  3. 困難  4. 專家  5. 自訂"
    ),
    "Choose difficulty: ": "選擇難度：",
    "Enter a number from 1 to 5.": "請輸入 1 至 5。",
    "Enter a number from 1 to 6.": "請輸入 1 至 6。",
    "Number of colours (5-10): ": "顏色數目 (5-10)：",
    "Code length (3-6): ": "密碼長度 (3-6)：",
    "Maximum attempts (1-20): ": "最多嘗試次數 (1-20)：",
    "Allow duplicate colours? (y/n): ": "允許重複顏色？(y/n)：",
    "Human Code Maker? (y/n): ": "由玩家設定秘密密碼？(y/n)：",
    "Code Maker, enter the secret (input hidden): ": "請設定秘密密碼（隱藏輸入）：",
    "Pass the device to the Code Breaker.": "請將裝置交給猜密碼的玩家。",
    "Enter y or n.": "請輸入 y 或 n。",
    "Attempt  Guess               Black  White": "次數     猜測                黑釘   白釘",
    "Game abandoned. No score was awarded.": "已放棄遊戲，沒有獲得分數。",
    "No local scores yet.": "尚未有本機分數。",
    "Rank  Player                    Difficulty  Score  Attempts": (
        "排名  玩家                      難度        分數   次數"
    ),
    "Export path [mastermind_scores.csv]: ": "匯出路徑 [mastermind_scores.csv]：",
    "Thanks for playing.": "感謝遊玩。",
    "Mastermind rules": "Mastermind 規則",
    "The Code Maker chooses a hidden sequence of coloured pegs.": "設定者選擇一組秘密顏色密碼。",
    "Enter colour identifiers separated by spaces, commas, or hyphens.": (
        "輸入顏色字母，可用空格、逗號或連字號分隔。"
    ),
    "A black peg means the right colour is in the right position.": ("黑釘代表顏色及位置正確。"),
    "A white peg means the right colour is in a different position.": (
        "白釘代表顏色正確但位置錯誤。"
    ),
    "Each secret peg can contribute at most one feedback peg.": (
        "每個秘密密碼位置最多只會產生一個回饋釘。"
    ),
    "Type quit during a game to abandon it.": "遊戲途中輸入 quit 可放棄。",
}

PATTERNS = (
    (r"Guess \((\d+) remaining\): ", "猜測（剩餘 {0} 次）："),
    (r"(\d+) attempts? remaining\.", "剩餘 {0} 次。"),
    (r"Code broken in (\d+) attempt\(s\)!", "成功破解密碼，共使用 {0} 次！"),
    (r"Score: (\d+)", "分數：{0}"),
    (r"Scores exported to (.+)\.", "分數已匯出至 {0}。"),
    (r"No attempts remain\. The code was (.+)\.", "已用盡嘗試次數，密碼為 {0}。"),
    (
        r"Available colours: (.+) \| Code length: (\d+) \| Attempts: (\d+)",
        "可用顏色：{0} | 密碼長度：{1} | 嘗試次數：{2}",
    ),
)


def translate_local(value: str, locale: str) -> str:
    if locale != "zh-Hant":
        return value
    prefix = value[: len(value) - len(value.lstrip("\n"))]
    message = value[len(prefix) :]
    if message in MESSAGES:
        return prefix + MESSAGES[message]
    for pattern, translated in PATTERNS:
        match = re.fullmatch(pattern, message)
        if match:
            return prefix + translated.format(*match.groups())
    if "\n" in message:
        return prefix + "\n".join(translate_local(line, locale) for line in message.split("\n"))
    return value
