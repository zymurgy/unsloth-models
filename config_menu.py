import curses
import os

# --- Configuration Data ---
MODELS = [
    {"name": "Qwen3.5 0.8B", "repo": "unsloth/Qwen3.5-0.8B-GGUF"},
    {"name": "Qwen3.5 2B", "repo": "unsloth/Qwen3.5-2B-GGUF"},
    {"name": "Qwen3.5 4B", "repo": "unsloth/Qwen3.5-4B-GGUF"},
    {"name": "Qwen3.5 9B", "repo": "unsloth/Qwen3.5-9B-GGUF"},
    {"name": "Qwen3.5 27B", "repo": "unsloth/Qwen3.5-27B-GGUF"},
    {"name": "Qwen3.5 35B-A3B", "repo": "unsloth/Qwen3.5-35B-A3B-GGUF"},
    {"name": "Qwen3.5 122B-A10B", "repo": "unsloth/Qwen3.5-122B-A10B-GGUF"},
    {"name": "Qwen3.5 397B-A17B", "repo": "unsloth/Qwen3.5-397B-A17B-GGUF"},
    {"name": "NVIDIA Nemotron 3 Super 120B", "repo": "unsloth/NVIDIA-Nemotron-3-Super-120B-A12B-GGUF"}
]

QUANTS = [
    {"name": "Q3_K_M", "tag": "Q3_K_M"},
    {"name": "Q4_K_M", "tag": "Q4_K_M"},
    {"name": "UD-Q4_K_XL", "tag": "UD-Q4_K_XL"},
    {"name": "Q6_K", "tag": "Q6_K"},
    {"name": "Q8_0", "tag": "Q8_0"},
    {"name": "BF16", "tag": "QF16"}
]

MODES = ["thinking", "coding", "non-thinking"]

def draw_menu(stdscr, title, options, current_row):
    stdscr.clear()
    stdscr.addstr(0, 0, title, curses.A_BOLD | curses.A_UNDERLINE)
    for idx, option in enumerate(options):
        x = 2
        y = 2 + idx
        if idx == current_row:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, f"> {option}")
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, x, f"  {option}")
    stdscr.refresh()

def select_from_list(stdscr, title, options):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    current_row = 0

    while True:
        draw_menu(stdscr, title, options, current_row)
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            return current_row

def main(stdscr):
    # 1. Select Model
    model_names = [m["name"] for m in MODELS]
    selected_model_idx = select_from_list(stdscr, "Select a Model:", model_names)
    selected_model = MODELS[selected_model_idx]

    # 2. Select Quantization
    quant_names = [q["name"] for q in QUANTS]
    selected_quant_idx = select_from_list(stdscr, f"Select Quantization for {selected_model['name']}:", quant_names)
    selected_quant = QUANTS[selected_quant_idx]

    # 3. Select Mode
    selected_mode_idx = select_from_list(stdscr, "Select a Parameter Mode:", MODES)
    selected_mode = MODES[selected_mode_idx]

    # 4. Write to Makefile Config
    with open("config.mk", "w") as f:
        f.write(f"REPO = {selected_model['repo']}\n")
        f.write(f"QUANT = {selected_quant['tag']}\n")
        f.write(f"INCLUDE = \"*{selected_quant['tag']}*\"\n")
        f.write(f"LOCAL_DIR = /models/{selected_model['repo']}\n")
        f.write(f"MODE = {selected_mode}\n")

    stdscr.clear()
    stdscr.addstr(0, 0, "Saved Configuration to config.mk!", curses.A_BOLD)
    stdscr.addstr(2, 0, f"Model : {selected_model['name']}")
    stdscr.addstr(3, 0, f"Quant : {selected_quant['name']} ({selected_quant['tag']})")
    stdscr.addstr(4, 0, f"Mode  : {selected_mode}")
    stdscr.addstr(6, 0, "Press any key to exit...")
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)
