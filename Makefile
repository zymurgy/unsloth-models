# ==========================================
# 1. Configuration & Paths
# ==========================================
-include config.mk

LLAMA_PATH ?= ./llama.cpp

# Fallbacks in case config.mk hasn't been generated yet
REPO       ?= unsloth/Qwen3.5-122B-A10B-GGUF
QUANT      ?= Q4_K_M
INCLUDE    ?= "*$(QUANT)*"
LOCAL_DIR  ?= /models/$(REPO)
MODE       ?= non-thinking

# Dynamically find the first .gguf file matching the quant in the downloaded dir.
# llama.cpp will automatically find the rest of the shards if it's a split model.
MODEL_FILE = $(shell find $(LOCAL_DIR) -name "*$(QUANT)*.gguf" | sort | head -n 1)

# ==========================================
# 2. Inference Parameters
# ==========================================
GPU_ARGS    = --n-gpu-layers 99
CTX_ARGS    = --ctx-size 16384

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
.PHONY: help config download run-cli run-server run-bench setup build clean check-model

default: help

help:
	@echo "====================================================================="
	@echo "                        llama.cpp Makefile Helper                    "
	@echo "====================================================================="
	@echo "  make config     - Open the Curses UI to configure settings <--"
	@echo "  make download   - Download the configured model & quant"
	@echo "  make run-cli    - Run the configured model in CLI mode"
	@echo "  make run-server - Run the configured model as an API server"
	@echo "  make run-bench  - Run performance benchmarks"
	@echo "====================================================================="
	@echo "Current Config: $(REPO) | Quant: $(QUANT) | Mode: $(MODE)"

# --- Safeguard ---
check-model:
	@if [ -z "$(MODEL_FILE)" ]; then \
		echo "ERROR: Model file not found in $(LOCAL_DIR)."; \
		echo "Please run 'make download' first."; \
		exit 1; \
	fi

# --- UI Target ---
config:
	@python3 config_menu.py

# --- Execution Targets ---
download:
	@echo "Downloading $(QUANT) from $(REPO) to $(LOCAL_DIR)..."
	env HF_HUB_ENABLE_HF_TRANSFER=1 hf download $(REPO) --include $(INCLUDE) --local-dir $(LOCAL_DIR)

run-cli: check-model
	@echo "Starting CLI using $(MODEL_FILE) in $(MODE) mode..."
	$(LLAMA_PATH)/llama-cli -m $(MODEL_FILE) $(GPU_ARGS) $(CTX_ARGS) $(CLI_ARGS) $(ACTIVE_PARAMS)

run-server: check-model
	@echo "Starting Server using $(MODEL_FILE) in $(MODE) mode..."
	$(LLAMA_PATH)/llama-server -m $(MODEL_FILE) --host 0.0.0.0 $(GPU_ARGS) $(CTX_ARGS) $(ACTIVE_PARAMS)

run-bench: check-model
	@echo "Running Benchmarks on $(MODEL_FILE)..."
	$(LLAMA_PATH)/llama-bench -m $(MODEL_FILE) $(GPU_ARGS) $(BENCH_ARGS)

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
