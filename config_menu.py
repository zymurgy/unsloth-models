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
    {"name": "Qwen3 Coder Next", "repo": "unsloth/Qwen3-Coder-Next-GGUF"},
    {"name": "NVIDIA Nemotron 3 Super 120B", "repo": "unsloth/NVIDIA-Nemotron-3-Super-120B-A12B-GGUF"}
]

# Grouped by bit-depth according to the matrix
QUANT_GROUPS = {
    "1-bit": ["UD-IQ1_S", "UD-TQ1_0", "UD-IQ1_M"],
    "2-bit": ["UD-IQ2_XXS", "Q2_K", "UD-IQ2_M", "Q2_K_L", "UD-Q2_K_XL"],
    "3-bit": ["UD-IQ3_XXS", "Q3_K_S", "UD-IQ3_S", "UD-Q3_K_S", "Q3_K_M", "UD-Q3_K_M", "UD-Q3_K_XL"],
    "4-bit": [
        "IQ4_XS", "UD-IQ4_XS", "Q4_K_S", "UD-Q4_K_S", 
        "Q4_1", "IQ4_NL", "MXFP4_MOE", "Q4_0", 
        "UD-IQ4_NL", "Q4_K_M", "UD-Q4_K_M", "UD-Q4_K_XL"
    ],
    "5-bit": ["Q5_K_S", "UD-Q5_K_S", "Q5_K_M", "UD-Q5_K_M", "UD-Q5_K_XL"],
    "6-bit": ["Q6_K", "UD-Q6_K", "UD-Q6_K_XL"],
    "8-bit": ["Q8_0", "UD-Q8_K_XL"],
    "16-bit": ["BF16"]
}

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
    selected_model_idx = select_from_list(stdscr, "1/4: Select a Model:", model_names)
    selected_model = MODELS[selected_model_idx]

    # 2. Select Bit-Depth Category
    bit_depths = list(QUANT_GROUPS.keys())
    selected_bit_idx = select_from_list(stdscr, f"2/4: Select Bit-Depth for {selected_model['name']}:", bit_depths)
    selected_bit = bit_depths[selected_bit_idx]

    # 3. Select Specific Quantization
    specific_quants = QUANT_GROUPS[selected_bit]
    selected_quant_idx = select_from_list(stdscr, f"3/4: Select Specific {selected_bit} Quantization:", specific_quants)
    selected_quant = specific_quants[selected_quant_idx]

    # 4. Select Mode
    selected_mode_idx = select_from_list(stdscr, "4/4: Select a Parameter Mode:", MODES)
    selected_mode = MODES[selected_mode_idx]

    # 5. Write to Makefile Config
    with open("config.mk", "w") as f:
        f.write(f"REPO = {selected_model['repo']}\n")
        f.write(f"QUANT = {selected_quant}\n")
        # Include flag uses wildcards so it catches both loose files and subdirectories
        f.write(f"INCLUDE = \"*{selected_quant}*\"\n") 
        f.write(f"LOCAL_DIR = /models/{selected_model['repo']}\n")
        f.write(f"MODE = {selected_mode}\n")

    stdscr.clear()
    stdscr.addstr(0, 0, "Saved Configuration to config.mk!", curses.A_BOLD)
    stdscr.addstr(2, 0, f"Model: {selected_model['name']}")
    stdscr.addstr(3, 0, f"Class: {selected_bit}")
    stdscr.addstr(4, 0, f"Quant: {selected_quant}")
    stdscr.addstr(5, 0, f"Mode : {selected_mode}")
    stdscr.addstr(7, 0, "Press any key to exit and run 'make download' or 'make run-server'...")
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)
