import curses
import os

# --- Configuration Data ---
MODELS = [
    {"name": "GLM 4.7 Flash", "repo": "unsloth/GLM-4.7-Flash-GGUF"},
    {"name": "GPT OSS 20B", "repo": "unsloth/gpt-oss-20b-GGUF"},
    {"name": "GPT OSS 120B", "repo": "unsloth/gpt-oss-120b-GGUF"},
    {"name": "NVIDIA Nemotron 3 Super 120B", "repo": "unsloth/NVIDIA-Nemotron-3-Super-120B-A12B-GGUF"},
    {"name": "NVIDIA Nemotron 3 Nano 30B", "repo": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF"},
    {"name": "Qwen3.5 0.8B", "repo": "unsloth/Qwen3.5-0.8B-GGUF"},
    {"name": "Qwen3.5 2B", "repo": "unsloth/Qwen3.5-2B-GGUF"},
    {"name": "Qwen3.5 4B", "repo": "unsloth/Qwen3.5-4B-GGUF"},
    {"name": "Qwen3.5 9B", "repo": "unsloth/Qwen3.5-9B-GGUF"},
    {"name": "Qwen3.5 27B", "repo": "unsloth/Qwen3.5-27B-GGUF"},
    {"name": "Qwen3.5 35B-A3B", "repo": "unsloth/Qwen3.5-35B-A3B-GGUF"},
    {"name": "Qwen3.5 122B-A10B", "repo": "unsloth/Qwen3.5-122B-A10B-GGUF"},
    {"name": "Qwen3.5 397B-A17B", "repo": "unsloth/Qwen3.5-397B-A17B-GGUF"},
    {"name": "Qwen3 Coder Next", "repo": "unsloth/Qwen3-Coder-Next-GGUF"},
    {"name": "Tri 21B Think", "repo": "mykor/Tri-21B-Think-GGUF"},
]

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
    "16-bit": ["BF16", "F16"]
}

CONTEXT_SIZES = [
    "4096", "8192", "16384", "32768", "65536", "131072", "262144"
]

# --- Sampling Parameters & Modes ---
# Fallback modes if a model doesn't have custom ones
DEFAULT_MODES = {
    "Thinking":     {"temp": 0.6, "top_p": 0.90, "top_k": 40, "min_p": 0.05, "rep_pen": 1.1,  "pres_pen": 0.0, "extra": ""},
    "Coding":       {"temp": 0.2, "top_p": 0.95, "top_k": 20, "min_p": 0.05, "rep_pen": 1.0,  "pres_pen": 0.0, "extra": ""},
    "Non-Thinking": {"temp": 0.8, "top_p": 0.95, "top_k": 50, "min_p": 0.10, "rep_pen": 1.15, "pres_pen": 0.0, "extra": ""}
}

# GLM 4.7 Flash Specific Modes
GLM_4_7_MODES = {
    "General Tasks": {
        "temp": 1.0, "top_p": 0.95, "top_k": 40, "min_p": 0.01, "rep_pen": 1.0, "pres_pen": 0.0, "extra": ""
    },
    "Tool-calling & SWE Bench": {
        "temp": 0.7, "top_p": 1.0, "top_k": 40, "min_p": 0.01, "rep_pen": 1.0, "pres_pen": 0.0, "extra": ""
    }
}

# Nemotron 3 Specific Modes (Used by both Super and Nano)
NEMOTRON_3_MODES = {
    "General Chat/Instruction": {
        "temp": 1.0, "top_p": 1.0, "top_k": 40, "min_p": 0.05, "rep_pen": 1.1, "pres_pen": 0.0, "extra": ""
    },
    "Tool Calling": {
        "temp": 0.6, "top_p": 0.95, "top_k": 40, "min_p": 0.05, "rep_pen": 1.1, "pres_pen": 0.0, "extra": ""
    }
}

# Qwen3.5 Specific Hybrid Modes
QWEN_3_5_MODES = {
    "Thinking - General Tasks": {
        "temp": 1.0, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 1.5,
        "extra": "--chat-template-kwargs '{\"enable_thinking\":true}'"
    },
    "Thinking - Precise Coding": {
        "temp": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 0.0,
        "extra": "--chat-template-kwargs '{\"enable_thinking\":true}'"
    },
    "Instruct (Non-Thinking) - General": {
        "temp": 0.7, "top_p": 0.80, "top_k": 20, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 1.5,
        "extra": "--chat-template-kwargs '{\"enable_thinking\":false}'"
    },
    "Instruct (Non-Thinking) - Reasoning": {
        "temp": 1.0, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 1.5,
        "extra": "--chat-template-kwargs '{\"enable_thinking\":false}'"
    }
}

# GPT OSS 20B Specific Modes
GPT_OSS_MODES = {
    "Reasoning Effort: Low": {
        "temp": 1.0, "top_p": 1.0, "top_k": 0, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 0.0,
        "extra": ""
    },
    "Reasoning Effort: Medium": {
        "temp": 1.0, "top_p": 1.0, "top_k": 0, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 0.0,
        "extra": ""
    },
    "Reasoning Effort: High": {
        "temp": 1.0, "top_p": 1.0, "top_k": 0, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 0.0,
        "extra": ""
    }
}


# Model-specific dictionaries. Maps model name -> its available modes.
MODEL_MODES = {
    "GLM 4.7 Flash": GLM_4_7_MODES,
    "NVIDIA Nemotron 3 Super 120B": NEMOTRON_3_MODES,
    "NVIDIA Nemotron 3 Nano 30B": NEMOTRON_3_MODES,
    "GPT OSS 20B": GPT_OSS_MODES,
    "GPT OSS 120B": GPT_OSS_MODES,
    "Qwen3 Coder Next": {
        "Coding": {"temp": 1.0, "top_p": 0.95, "top_k": 40, "min_p": 0.01, "rep_pen": 1.0, "pres_pen": 0.0, "extra": ""},
        "Thinking": DEFAULT_MODES["Thinking"],
        "Non-Thinking": DEFAULT_MODES["Non-Thinking"],
    },
    "Tri 21B Think": {
        "Thinking": {"temp": 0.5, "top_p": 0.85, "top_k": 30, "min_p": 0.02, "rep_pen": 1.05, "pres_pen": 0.0, "extra": ""},
        "Coding": DEFAULT_MODES["Coding"],
        "Non-Thinking": DEFAULT_MODES["Non-Thinking"],
    }
}

# Automatically assign the 4 Qwen modes to all Qwen 3.5 models
for model in MODELS:
    if "Qwen3.5" in model["name"]:
        MODEL_MODES[model["name"]] = QWEN_3_5_MODES


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
    selected_model_idx = select_from_list(stdscr, "1/5: Select a Model:", model_names)
    selected_model = MODELS[selected_model_idx]

    # 2. Select Bit-Depth Category
    bit_depths = list(QUANT_GROUPS.keys())
    selected_bit_idx = select_from_list(stdscr, f"2/5: Select Bit-Depth for {selected_model['name']}:", bit_depths)
    selected_bit = bit_depths[selected_bit_idx]

    # 3. Select Specific Quantization
    specific_quants = QUANT_GROUPS[selected_bit]
    selected_quant_idx = select_from_list(stdscr, f"3/5: Select Specific {selected_bit} Quantization:", specific_quants)
    selected_quant = specific_quants[selected_quant_idx]

    # 4. Select Context Size
    selected_ctx_idx = select_from_list(stdscr, "4/5: Select Context Size:", CONTEXT_SIZES)
    selected_ctx = CONTEXT_SIZES[selected_ctx_idx]

    # 5. Select Mode (Dynamic based on selected model!)
    available_modes_dict = MODEL_MODES.get(selected_model["name"], DEFAULT_MODES)
    mode_names = list(available_modes_dict.keys())
    selected_mode_idx = select_from_list(stdscr, f"5/5: Select Mode for {selected_model['name']}:", mode_names)

    selected_mode_name = mode_names[selected_mode_idx]
    gen_params = available_modes_dict[selected_mode_name]

    # 6. Write to Makefile Config
    base_models_dir = "/models" if os.path.isdir("/models") else "./models"

    with open("config.mk", "w") as f:
        f.write(f"REPO = {selected_model['repo']}\n")
        f.write(f"QUANT = {selected_quant}\n")
        f.write(f"INCLUDE = \"*{selected_quant}*\"\n")
        f.write(f"LOCAL_DIR = {base_models_dir}/{selected_model['repo']}\n")
        f.write(f"CTX_SIZE = {selected_ctx}\n")
        f.write(f"MODE = {selected_mode_name}\n")

        # Write generation parameters
        f.write(f"TEMP = {gen_params.get('temp', 0.8)}\n")
        f.write(f"TOP_P = {gen_params.get('top_p', 0.95)}\n")
        f.write(f"TOP_K = {gen_params.get('top_k', 40)}\n")
        f.write(f"MIN_P = {gen_params.get('min_p', 0.05)}\n")
        f.write(f"REP_PENALTY = {gen_params.get('rep_pen', 1.1)}\n")
        f.write(f"PRES_PEN = {gen_params.get('pres_pen', 0.0)}\n")
        f.write(f"EXTRA_ARGS = {gen_params.get('extra', '')}\n")

    stdscr.clear()
    stdscr.addstr(0, 0, "Saved Configuration to config.mk!", curses.A_BOLD)
    stdscr.addstr(2, 0, f"Model   : {selected_model['name']}")
    stdscr.addstr(3, 0, f"Class   : {selected_bit}")
    stdscr.addstr(4, 0, f"Quant   : {selected_quant}")
    stdscr.addstr(5, 0, f"Context : {selected_ctx}")
    stdscr.addstr(6, 0, f"Mode    : {selected_mode_name}")

    stdscr.addstr(8, 0, "Derived Parameters:", curses.A_UNDERLINE)
    stdscr.addstr(9, 0, f"Temp: {gen_params['temp']} | Top-P: {gen_params['top_p']} | Min-P: {gen_params['min_p']} | Rep-Pen: {gen_params['rep_pen']}")
    if gen_params.get("extra"):
        stdscr.addstr(10, 0, f"Extra: {gen_params['extra']}")

    stdscr.addstr(12, 0, "Press any key to exit and run 'make download' or 'make run-server'...")
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)
