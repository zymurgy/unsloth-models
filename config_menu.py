import curses

# --- Configuration Data ---
MODELS = [
    {
        "name": "NVIDIA Nemotron 3 Super 120B",
        "repo": "unsloth/NVIDIA-Nemotron-3-Super-120B-A12B-GGUF",
        "include": "UD-Q4_K_XL/*",
        "file": "/models/unsloth/NVIDIA-Nemotron-3-Super-120B-A12B-GGUF/UD-Q4_K_XL/NVIDIA-Nemotron-3-Super-120B-A12B-UD-Q4_K_XL-00001-of-00003.gguf"
    },
    {
        "name": "Qwen 3.5 122B",
        "repo": "unsloth/Qwen3.5-122B-A10B-GGUF",
        "include": "Q4_K_M/*",
        "file": "/models/unsloth/Qwen3.5-122B-A10B-GGUF/Q4_K_M/Qwen3.5-122B-A10B-Q4_K_M-00001-of-00003.gguf"
    }
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
    selected_model_idx = select_from_list(stdscr, "Select a Model (UP/DOWN arrows, ENTER to select):", model_names)
    selected_model = MODELS[selected_model_idx]

    # 2. Select Mode
    selected_mode_idx = select_from_list(stdscr, "Select a Parameter Mode:", MODES)
    selected_mode = MODES[selected_mode_idx]

    # 3. Write to Makefile Config
    with open("config.mk", "w") as f:
        f.write(f"REPO = {selected_model['repo']}\n")
        f.write(f"INCLUDE = {selected_model['include']}\n")
        f.write(f"MODEL_FILE = {selected_model['file']}\n")
        f.write(f"LOCAL_DIR = /models/{selected_model['repo']}\n")
        f.write(f"MODE = {selected_mode}\n")

    stdscr.clear()
    stdscr.addstr(0, 0, f"Saved Configuration to config.mk!", curses.A_BOLD)
    stdscr.addstr(2, 0, f"Model: {selected_model['name']}")
    stdscr.addstr(3, 0, f"Mode : {selected_mode}")
    stdscr.addstr(5, 0, "Press any key to exit...")
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)
