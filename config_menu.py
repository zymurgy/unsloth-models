import curses
import os

# --- Machine Profiles ---
# System-specific settings for different hardware in your homelab.
MACHINE_PROFILES = {
    "4x RTX 3090 - Max Performance": {
        "gpu_layers": 99,
        "split_mode": "layer",
        "tensor_split": "10,11,11,11",
        "exec_mode": "docker",
        "dockerfile": "Dockerfile.cuda"
    },
    "4x RTX 3090 - Hybrid (CPU Offload)": {
        "gpu_layers": 40,
        "split_mode": "layer",
        "tensor_split": "0,0,0,0",
        "exec_mode": "docker",
        "dockerfile": "Dockerfile.cuda"
    },
    "Jetson Orin AGX": {
        "gpu_layers": 99,
        "split_mode": "none",
        "tensor_split": "0",
        "exec_mode": "docker",
        "dockerfile": "Dockerfile.jetson"
    },
    "Mac Mini M4 (24GB Unified)": {
        "gpu_layers": 99,
        "split_mode": "none",
        "tensor_split": "0",
        "exec_mode": "native",
        "dockerfile": "none"
    }
}

# --- Configuration Data ---
MODELS = [
    {"name": "Gemma 3 270M", "repo": "unsloth/gemma-3-270m-it-GGUF"},
    {"name": "Gemma 3 1B", "repo": "unsloth/gemma-3-1b-it-GGUF"},
    {"name": "Gemma 3 4B", "repo": "unsloth/gemma-3-4b-it-GGUF"},
    {"name": "Gemma 3 12B", "repo": "unsloth/gemma-3-12b-it-GGUF"},
    {"name": "Gemma 3 27B", "repo": "unsloth/gemma-3-27b-it-GGUF"},
    {"name": "GLM 4.7 Flash", "repo": "unsloth/GLM-4.7-Flash-GGUF"},
    {"name": "GPT OSS 20B", "repo": "unsloth/gpt-oss-20b-GGUF"},
    {"name": "GPT OSS 120B", "repo": "unsloth/gpt-oss-120b-GGUF"},
    {"name": "MiniMax M2.5", "repo": "unsloth/MiniMax-M2.5-GGUF"},
    {"name": "Mistral Small 4 119B", "repo": "unsloth/Mistral-Small-4-119B-2603-GGUF"},
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
    {"name": "Qwen3 VL 2B Instruct", "repo": "unsloth/Qwen3-VL-2B-Instruct-GGUF"},
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
DEFAULT_MODES = {
    "Thinking":     {"temp": 0.6, "top_p": 0.90, "top_k": 40, "min_p": 0.05, "rep_pen": 1.1,  "pres_pen": 0.0, "extra": ""},
    "Coding":       {"temp": 0.2, "top_p": 0.95, "top_k": 20, "min_p": 0.05, "rep_pen": 1.0,  "pres_pen": 0.0, "extra": ""},
    "Non-Thinking": {"temp": 0.8, "top_p": 0.95, "top_k": 50, "min_p": 0.10, "rep_pen": 1.15, "pres_pen": 0.0, "extra": ""}
}

GLM_4_7_MODES = {
    "General Tasks": {
        "temp": 1.0, "top_p": 0.95, "top_k": 40, "min_p": 0.01, "rep_pen": 1.0, "pres_pen": 0.0, "extra": ""
    },
    "Tool-calling & SWE Bench": {
        "temp": 0.7, "top_p": 1.0, "top_k": 40, "min_p": 0.01, "rep_pen": 1.0, "pres_pen": 0.0, "extra": ""
    }
}

NEMOTRON_3_MODES = {
    "General Chat/Instruction": {
        "temp": 1.0, "top_p": 1.0, "top_k": 40, "min_p": 0.05, "rep_pen": 1.1, "pres_pen": 0.0, "extra": ""
    },
    "Tool Calling": {
        "temp": 0.6, "top_p": 0.95, "top_k": 40, "min_p": 0.05, "rep_pen": 1.1, "pres_pen": 0.0, "extra": ""
    }
}

QWEN_3_5_MODES = {
    "Thinking - General Tasks": {
        "temp": 1.0, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 1.5,
        "extra": "--reasoning on", "mmproj": True
    },
    "Thinking - Precise Coding": {
        "temp": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 0.0,
        "extra": "--reasoning on", "mmproj": True
    },
    "Instruct (Non-Thinking) - General": {
        "temp": 0.7, "top_p": 0.80, "top_k": 20, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 1.5,
        "extra": "--reasoning off", "mmproj": True
    },
    "Instruct (Non-Thinking) - Reasoning": {
        "temp": 1.0, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 1.5,
        "extra": "--reasoning off", "mmproj": True
    }
}

QWEN_3_VL_MODES = {
    "Instruct": {
        "temp": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 1.5,
        "extra": "", "mmproj": True
    },
    "Thinking": {
        "temp": 1.0, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 0.0,
        "extra": "", "mmproj": True
    },
}

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

GEMMA_3_MODES = {
    "Official Recommendation": {
        "temp": 1.0, "top_p": 0.95, "top_k": 64, "min_p": 0.01, "rep_pen": 1.0, "pres_pen": 0.0, "extra": ""
    }
}

MINIMAX_M2_5_MODES = {
    "General": {
        "temp": 1.0, "top_p": 0.95, "top_k": 40, "min_p": 0.1, "rep_pen": 1.0, "pres_pen": 0.0, "extra": ""
    }
}

MODEL_MODES = {
    "GLM 4.7 Flash": GLM_4_7_MODES,
    "NVIDIA Nemotron 3 Super 120B": NEMOTRON_3_MODES,
    "NVIDIA Nemotron 3 Nano 30B": NEMOTRON_3_MODES,
    "GPT OSS 20B": GPT_OSS_MODES,
    "GPT OSS 120B": GPT_OSS_MODES,
    "Qwen3 Coder Next": {
        "Coding": {"temp": 1.0, "top_p": 0.95, "top_k": 40, "min_p": 0.01, "rep_pen": 1.0, "pres_pen": 0.0, "extra": ""},
    }
}

# Automatically assign modes based on names
for model in MODELS:
    if "Gemma 3" in model["name"]:
        MODEL_MODES[model["name"]] = GEMMA_3_MODES
    elif "Qwen3.5" in model["name"]:
        MODEL_MODES[model["name"]] = QWEN_3_5_MODES
    elif "Qwen3 VL" in model["name"]:
        MODEL_MODES[model["name"]] = QWEN_3_VL_MODES
    elif "MiniMax M2.5" in model["name"]:
        MODEL_MODES[model["name"]] = MINIMAX_M2_5_MODES

# --- UI Functions ---
def draw_menu(stdscr, title, options, current_row, show_back):
    stdscr.clear()
    
    # Get current terminal dimensions
    height, width = stdscr.getmaxyx()
    
    # Failsafe for extremely tiny terminals
    if height < 10 or width < 40:
        stdscr.addstr(0, 0, "Terminal too small!", curses.A_BOLD)
        stdscr.refresh()
        return

    # Draw Title (truncated to fit screen width)
    stdscr.addstr(0, 0, title[:width-1], curses.A_BOLD | curses.A_UNDERLINE)

    # --- Pagination / Scrolling Logic ---
    # Header takes 2 lines, Footer takes 4 lines. 
    # Calculate how many options we can actually fit.
    max_options_to_show = height - 6 
    
    # Calculate our sliding window
    start_row = max(0, current_row - (max_options_to_show // 2))
    
    # Clamp the window to the bottom of the list if we are near the end
    if start_row + max_options_to_show > len(options):
        start_row = max(0, len(options) - max_options_to_show)
        
    end_row = min(len(options), start_row + max_options_to_show)

    # Draw "Scroll Up" indicator if needed
    if start_row > 0:
        stdscr.addstr(1, 4, "↑ ...more...", curses.A_DIM)

    # Draw the visible options
    for idx in range(start_row, end_row):
        option = options[idx]
        x = 2
        y = 2 + (idx - start_row)
        
        # Truncate text so it doesn't wrap and cause another crash
        display_text = f"> {option}" if idx == current_row else f"  {option}"
        display_text = display_text[:width-1]

        if idx == current_row:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, display_text)
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, x, display_text)

    # Draw "Scroll Down" indicator if needed
    if end_row < len(options):
        stdscr.addstr(2 + (end_row - start_row), 4, "↓ ...more...", curses.A_DIM)

    # --- Draw Footer safely at the bottom ---
    footer_y = height - 3
    stdscr.addstr(footer_y, 0, "[ENTER] Select  [UP/DOWN] Navigate"[:width-1], curses.A_DIM)
    
    if show_back:
        stdscr.addstr(footer_y + 1, 0, "[B] Back        [Q / ESC] Quit without saving"[:width-1], curses.A_DIM)
    else:
        stdscr.addstr(footer_y + 1, 0, "[Q / ESC] Quit without saving"[:width-1], curses.A_DIM)

    stdscr.refresh()

def select_from_list(stdscr, title, options, show_back=True):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    current_row = 0

    while True:
        draw_menu(stdscr, title, options, current_row, show_back)
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            return current_row
        elif key in [ord('b'), ord('B'), curses.KEY_BACKSPACE, 127, 8] and show_back:
            return "BACK"
        elif key in [ord('q'), ord('Q'), 27]: # 27 is the ESC key
            return "EXIT"

def main(stdscr):
    step = 0

    # State variables to hold selections as we move forward/backward
    selected_profile_name = None
    selected_profile_data = None
    selected_model = None
    selected_bit = None
    selected_quant = None
    selected_ctx = None
    selected_mode_name = None
    gen_params = None

    # State Machine Loop
    while step < 6:
        if step == 0:
            profiles = list(MACHINE_PROFILES.keys())
            res = select_from_list(stdscr, "0/6: Select Machine Profile:", profiles, show_back=False)
            if res == "EXIT": return
            selected_profile_name = profiles[res]
            selected_profile_data = MACHINE_PROFILES[selected_profile_name]
            step += 1

        elif step == 1:
            model_names = [m["name"] for m in MODELS]
            res = select_from_list(stdscr, f"1/6: Select a Model (Profile: {selected_profile_name}):", model_names)
            if res == "EXIT": return
            if res == "BACK": step -= 1; continue
            selected_model = MODELS[res]
            step += 1

        elif step == 2:
            bit_depths = list(QUANT_GROUPS.keys())
            res = select_from_list(stdscr, f"2/6: Select Bit-Depth for {selected_model['name']}:", bit_depths)
            if res == "EXIT": return
            if res == "BACK": step -= 1; continue
            selected_bit = bit_depths[res]
            step += 1

        elif step == 3:
            specific_quants = QUANT_GROUPS[selected_bit]
            res = select_from_list(stdscr, f"3/6: Select Specific {selected_bit} Quantization:", specific_quants)
            if res == "EXIT": return
            if res == "BACK": step -= 1; continue
            selected_quant = specific_quants[res]
            step += 1

        elif step == 4:
            res = select_from_list(stdscr, "4/6: Select Context Size:", CONTEXT_SIZES)
            if res == "EXIT": return
            if res == "BACK": step -= 1; continue
            selected_ctx = CONTEXT_SIZES[res]
            step += 1

        elif step == 5:
            available_modes_dict = MODEL_MODES.get(selected_model["name"], DEFAULT_MODES)
            mode_names = list(available_modes_dict.keys())
            res = select_from_list(stdscr, f"5/6: Select Mode for {selected_model['name']}:", mode_names)
            if res == "EXIT": return
            if res == "BACK": step -= 1; continue

            selected_mode_name = mode_names[res]
            gen_params = available_modes_dict[selected_mode_name]
            step += 1 # Breaks the while loop

    # Check if vision model (for mmproj parameter)
    is_vision_model = gen_params.get("mmproj", False)

    # --- Step 6: Write to Makefile Config ---
    # (This code is only reached if the user successfully navigates all 6 steps)
    base_models_dir = "/models" if os.path.isdir("/models") else "./models"

    with open("config.mk", "w") as f:
        f.write(f"REPO = {selected_model['repo']}\n")
        f.write(f"QUANT = {selected_quant}\n")
        f.write(f"INCLUDE = \"*{selected_quant}*\"\n")
        f.write(f"LOCAL_DIR = {base_models_dir}/{selected_model['repo']}\n")
        f.write(f"CTX_SIZE = {selected_ctx}\n")
        f.write(f"MODE = {selected_mode_name}\n")

        # Write hardware profile parameters
        f.write(f"GPU_LAYERS = {selected_profile_data['gpu_layers']}\n")
        f.write(f"SPLIT_MODE = {selected_profile_data['split_mode']}\n")
        f.write(f"TENSOR_SPLIT = {selected_profile_data['tensor_split']}\n")
        f.write(f"EXEC_MODE = {selected_profile_data['exec_mode']}\n")
        f.write(f"DOCKERFILE_EXT = {selected_profile_data['dockerfile']}\n")

        # Write generation parameters
        f.write(f"TEMP = {gen_params.get('temp', 0.8)}\n")
        f.write(f"TOP_P = {gen_params.get('top_p', 0.95)}\n")
        f.write(f"TOP_K = {gen_params.get('top_k', 40)}\n")
        f.write(f"MIN_P = {gen_params.get('min_p', 0.05)}\n")
        f.write(f"REP_PENALTY = {gen_params.get('rep_pen', 1.1)}\n")
        f.write(f"PRES_PEN = {gen_params.get('pres_pen', 0.0)}\n")
        f.write(f"EXTRA_ARGS = {gen_params.get('extra', '')}\n")
        f.write(f"IS_VISION_MODEL = {'true' if is_vision_model else 'false'}\n")

    # Display confirmation screen
    stdscr.clear()
    stdscr.addstr(0, 0, "Saved Configuration to config.mk!", curses.A_BOLD)
    stdscr.addstr(2, 0, f"Profile : {selected_profile_name}")
    stdscr.addstr(3, 0, f"Model   : {selected_model['name']}")
    stdscr.addstr(4, 0, f"Class   : {selected_bit}")
    stdscr.addstr(5, 0, f"Quant   : {selected_quant}")
    stdscr.addstr(6, 0, f"Context : {selected_ctx}")
    stdscr.addstr(7, 0, f"Mode    : {selected_mode_name}")

    stdscr.addstr(9, 0, "Derived Parameters:", curses.A_UNDERLINE)
    stdscr.addstr(10, 0, f"Temp: {gen_params['temp']} | Top-P: {gen_params['top_p']} | Min-P: {gen_params['min_p']} | Rep-Pen: {gen_params['rep_pen']}")
    
    extra_line_offset = 11
    if gen_params.get("extra"):
        stdscr.addstr(extra_line_offset, 0, f"Extra: {gen_params['extra']}")
        extra_line_offset += 1
    if is_vision_model:
        stdscr.addstr(extra_line_offset, 0, "Vision Model: Yes (mmproj will be used)")

    stdscr.addstr(extra_line_offset + 2, 0, "Press any key to exit and run 'make download' or 'make run-server'...")
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)
