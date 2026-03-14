# ==========================================
# 1. Configuration & Paths
# ==========================================
# This line pulls in the variables saved by the Python curses script.
# The '-' prefix tells make not to throw an error if config.mk doesn't exist yet.
-include config.mk

LLAMA_PATH ?= ./llama.cpp

# Fallbacks in case config.mk hasn't been generated yet
REPO       ?= unsloth/NVIDIA-Nemotron-3-Super-120B-A12B-GGUF
INCLUDE    ?= "UD-Q4_K_XL/*"
LOCAL_DIR  ?= /models/$(REPO)
MODEL_FILE ?= $(LOCAL_DIR)/UD-Q4_K_XL/NVIDIA-Nemotron-3-Super-120B-A12B-UD-Q4_K_XL-00001-of-00003.gguf
MODE       ?= non-thinking

# ==========================================
# 2. Inference Parameters
# ==========================================
COMMON_ARGS = --ctx-size 16384 --n-gpu-layers 99
CLI_ARGS    = --seed 3407 --prio 2
BENCH_ARGS  ?= -p 512,1024 -n 128,256

PARAMS_THINKING     = --temp 1.0 --top-p 0.95 --top-k 20 --min-p 0.00
PARAMS_CODING       = --temp 0.2 --top-p 0.95 --top-k 40 --min-p 0.05
PARAMS_NON_THINKING = --temp 0.6 --top-p 0.95

ifeq ($(MODE), coding)
    ACTIVE_PARAMS = $(PARAMS_CODING)
else ifeq ($(MODE), thinking)
    ACTIVE_PARAMS = $(PARAMS_THINKING)
else
    ACTIVE_PARAMS = $(PARAMS_NON_THINKING)
endif

# ==========================================
# 3. Targets
# ==========================================
.PHONY: help config download run-cli run-server run-bench setup build clean

default: help

help:
	@echo "====================================================================="
	@echo "                        llama.cpp Makefile Helper                    "
	@echo "====================================================================="
	@echo "  make config   - Open the Curses UI to select Model and Mode <--"
	@echo "  make download - Download the configured model"
	@echo "  make run-cli  - Run the configured model in CLI mode"
	@echo "  make run-server- Run the configured model as an API server"
	@echo "  make run-bench- Run performance benchmarks"
	@echo "====================================================================="
	@echo "Current Config: $(REPO) | Mode: $(MODE)"

# --- UI Target ---
config:
	@python3 config_menu.py

# --- Execution Targets ---
download:
	@echo "Downloading $(REPO) to $(LOCAL_DIR)..."
	huggingface-cli download $(REPO) --include $(INCLUDE) --local-dir $(LOCAL_DIR)

run-cli:
	@echo "Starting CLI in $(MODE) mode..."
	$(LLAMA_PATH)/llama-cli -m $(MODEL_FILE) $(COMMON_ARGS) $(CLI_ARGS) $(ACTIVE_PARAMS)

run-server:
	@echo "Starting Server in $(MODE) mode..."
	$(LLAMA_PATH)/llama-server -m $(MODEL_FILE) --host 0.0.0.0 $(COMMON_ARGS) $(ACTIVE_PARAMS)

run-bench:
	@echo "Running Benchmarks on $(MODEL_FILE)..."
	$(LLAMA_PATH)/llama-bench -m $(MODEL_FILE) $(COMMON_ARGS) $(BENCH_ARGS)

# --- Build Targets ---
setup:
	sudo apt-get update
	sudo apt-get install pciutils build-essential cmake curl libcurl4-openssl-dev python3 -y

build:
	@if [ ! -d "llama.cpp" ]; then git clone https://github.com/ggml-org/llama.cpp; fi
	cmake llama.cpp -B llama.cpp/build -DBUILD_SHARED_LIBS=OFF -DGGML_CUDA=ON
	cmake --build llama.cpp/build --config Release -j --clean-first \
		--target llama-cli llama-mtmd-cli llama-server llama-gguf-split llama-bench
	cp llama.cpp/build/bin/llama-* llama.cpp/

clean:
	rm -rf llama.cpp/build config.mk
