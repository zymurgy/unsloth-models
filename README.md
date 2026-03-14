s a complete, polished `README.md` ready to be dropped into your repository. I have expanded it to include prerequisites, a guide on how users can add their own custom models, and a quick troubleshooting section.

```markdown
# 🦥 Unsloth llama.cpp Helper

A streamlined, cross-platform terminal UI (TUI) and Makefile toolchain for downloading, configuring, and running [Unsloth](https://github.com/unslothai/unsloth) GGUF models using `llama.cpp`. 

This tool eliminates the headache of manually hunting down Hugging Face URLs, guessing the right sampling parameters for specific models, and typing out massive terminal commands. It features an interactive menu to select your model and injects the exact recommended inference parameters (Temperature, Top-P, Min-P, etc.) automatically.

## ✨ Features
* **Interactive Terminal UI:** A Curses-based menu to easily select models, quantizations, context sizes, and inference modes.
* **Smart Parameter Injection:** Automatically applies the exact recommended sampling parameters based on the model and task (e.g., Qwen 3.5 Hybrid Thinking modes, Nemotron Tool-Calling, GLM General tasks).
* **Blazing Fast Downloads:** Automatically creates an isolated Python virtual environment and utilizes `huggingface_hub` with `hf_transfer` to saturate your download bandwidth.
* **Cross-Platform Auto-Detection:** Automatically detects your OS. Builds with CUDA on Linux and Apple Metal on macOS.
* **Smart Pathing:** Saves models to a global `/models` directory if you have root permissions, or gracefully falls back to a local `./models` folder if you don't.

---

## 📋 Prerequisites

* **Linux (Debian/Ubuntu):** You just need `make` and `sudo` privileges. The setup script will handle `apt-get` dependencies automatically.
* **macOS:** You must have [Homebrew](https://brew.sh/) installed. The setup script will handle the rest.

---

## 🚀 Quick Start

**1. Install Dependencies & Virtual Environment**
```bash
make setup

```

*(Installs system packages, creates a `.venv`, and installs the Hugging Face CLI).*

**2. Build llama.cpp**

```bash
make build

```

*(Clones the official `llama.cpp` repository and compiles it for your system's hardware).*

**3. Configure your Model**

```bash
make config

```

*(Opens the interactive menu. Use **Arrow Keys** to navigate, **Enter** to select, **B** to go back, and **Q/ESC** to quit).*

**4. Download the Model**

```bash
make download

```

*(Downloads your selected GGUF file directly from Hugging Face).*

**5. Run It!**

```bash
make run-server  # Starts the API server on port 8080 (0.0.0.0)
# OR
make run-cli     # Starts an interactive chat directly in your terminal

```

---

## 🛠️ Available Commands

Run `make` or `make help` at any time to see your current configuration and all available commands.

| Command | Description |
| --- | --- |
| `make setup` | Installs system dependencies and creates the Python venv. |
| `make build` | Clones and compiles `llama.cpp` with appropriate GPU acceleration. |
| `make config` | Opens the TUI to select a model, quantization, context size, and mode. |
| `make download` | Downloads the selected GGUF file(s) to your models directory. |
| `make run-server` | Boots the `llama.cpp` API server with the configured parameters. |
| `make run-cli` | Boots the model directly in your terminal for quick testing. |
| `make run-bench` | Runs a standard 512/1024 prompt and 128/256 generation benchmark. |
| `make clean` | Removes the `llama.cpp/build` directory, the `.venv`, and `config.mk`. |

---

## 🧠 Supported Models & Modes

The script includes specialized parameter presets based on official model documentation. When you select a model in `make config`, the menu will dynamically adapt to show the appropriate inference modes for that specific architecture:

* **Qwen 3.5 (0.8B - 397B):** Specific toggles for *Thinking*, *Precise Coding*, and *Instruct* variants, automatically injecting `enable_thinking` chat template arguments.
* **NVIDIA Nemotron 3 (Nano & Super):** Presets for *General Chat/Instruction* and strict *Tool Calling*.
* **GLM 4.7 Flash:** Presets for *General Tasks* and *Tool-calling & SWE Bench*.
* **GPT OSS (20B & 120B):** Optimized settings with disabled Top-K filtering for dynamic reasoning efforts (*Low*, *Medium*, *High*).
* **Qwen 3 Coder Next:** Tightened parameters specific for code generation.

---

## 🔧 Adding Custom Models

You can easily add new models to the TUI by editing `config_menu.py`.

**1. Add the repository to the `MODELS` list:**

```python
MODELS = [
    # ... existing models ...
    {"name": "My Custom Model 8B", "repo": "username/my-custom-model-GGUF"},
]

```

**2. (Optional) Define custom modes in `MODEL_MODES`:**
If your model requires specific inference parameters or `llama.cpp` flags, map them in the `MODEL_MODES` dictionary. If you skip this step, it will default to the standard "Thinking", "Coding", and "Non-Thinking" generic profiles.

```python
MODEL_MODES = {
    # ... existing modes ...
    "My Custom Model 8B": {
        "Creative Writing": {"temp": 1.2, "top_p": 0.95, "top_k": 50, "min_p": 0.1, "rep_pen": 1.1, "pres_pen": 0.0, "extra": ""},
        "Strict JSON": {"temp": 0.1, "top_p": 1.0, "top_k": 40, "min_p": 0.0, "rep_pen": 1.0, "pres_pen": 0.0, "extra": ""}
    }
}

```

---

## ⚠️ Troubleshooting

* **`make: *** missing separator. Stop.`**
If you copy and paste the `Makefile` and encounter this error, your text editor converted the required `TAB` characters into spaces. Makefiles require strict Tab indentation for all commands under a target.
* **Hugging Face CLI not found:**
Ensure you ran `make setup` successfully. The `Makefile` relies on the isolated virtual environment (`.venv`) to execute downloads cleanly without conflicting with your system Python packages.

```

Would you like me to show you how to initialize a Git repository for this folder and push it up to GitHub, or are you all set?

```
