# ==========================================
# 1. Configuration & Paths
# ==========================================
-include config.mk

# Check if running as root
IS_ROOT := $(shell [ $$(id -u) -eq 0 ] && echo true || echo false)
SUDO    =
ifeq ($(filter true,$(IS_ROOT)),true)
else
	SUDO := sudo
endif

# Detect OS
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	# macOS (Apple Silicon/Metal) settings
	SETUP_CMD   = brew update && brew install cmake curl python3
	CMAKE_FLAGS = -DBUILD_SHARED_LIBS=OFF -DGGML_METAL=ON
else
	# Linux (Debian/CUDA) settings
	SETUP_CMD   = $(SUDO) apt-get update && $(SUDO) apt-get install pciutils build-essential git cmake curl libcurl4-openssl-dev python3 python3-venv -y
	CMAKE_FLAGS = -DBUILD_SHARED_LIBS=OFF -DGGML_CUDA=ON
endif

LLAMA_PATH ?= ./llama.cpp
VENV_DIR   ?= .venv

# --- Path Discovery for HF CLI ---
# Look for the official 'hf' binary in the virtual environment
ifneq ($(wildcard $(VENV_DIR)/bin/hf),)
    HF_CLI ?= $(VENV_DIR)/bin/hf
# Fallback to global system PATH if it's installed globally
else
    HF_CLI ?= hf
endif

# Fallbacks in case config.mk hasn't been generated yet
REPO        ?= unsloth/Qwen3.5-122B-A10B-GGUF
QUANT       ?= Q4_K_M
INCLUDE     ?= "*$(QUANT)*"
HOST_MODELS_DIR ?= ./models
MODE        ?= non-thinking
CTX_SIZE    ?= 16384

# --- Path Routing Logic ---
ifeq ($(IN_DOCKER),true)
	BASE_MODELS_DIR = /app/models
else
	BASE_MODELS_DIR = $(HOST_MODELS_DIR)
endif

LOCAL_DIR = $(BASE_MODELS_DIR)/$(REPO)

# Hardware Profile Fallbacks
EXEC_MODE      ?= native
DOCKERFILE_EXT ?= Dockerfile.cuda
GPU_LAYERS   ?= 99
SPLIT_MODE   ?= layer
TENSOR_SPLIT ?= 0

# Parameter Fallbacks
TEMP        ?= 0.8
TOP_P       ?= 0.95
TOP_K       ?= 50
MIN_P       ?= 0.10
REP_PENALTY ?= 1.15
PRES_PEN    ?= 0.0
EXTRA_ARGS  ?=
IS_VISION_MODEL ?= false

# Dynamically find the first .gguf file matching the quant in the downloaded dir.
MODEL_FILE = $(shell find $(LOCAL_DIR) -name "*$(QUANT)*.gguf" 2>/dev/null | sort | head -n 1)

# For vision models, find the mmproj-F16.gguf file
MMPROJ_FILE = $(shell find $(LOCAL_DIR) -name "mmproj-F16.gguf" 2>/dev/null | sort | head -n 1)

# Docker Configuration
DOCKER_IMAGE_NAME ?= unsloth-llm-$(EXEC_MODE)
DOCKER_PORT       ?= 8080

# ==========================================
# 2. Inference Parameters
# ==========================================
GPU_ARGS    = --n-gpu-layers $(GPU_LAYERS) --split-mode $(SPLIT_MODE)
ifneq ($(TENSOR_SPLIT),0)
GPU_ARGS   += --tensor-split $(TENSOR_SPLIT)
endif

CTX_ARGS    = --ctx-size $(CTX_SIZE)

CLI_ARGS    = --prio 2
BENCH_ARGS  ?= -p 512,1024 -n 128,256 -r 1

# Dynamically generated parameters from config.mk
ACTIVE_PARAMS = --temp $(TEMP) --top-p $(TOP_P) --top-k $(TOP_K) --min-p $(MIN_P) --repeat-penalty $(REP_PENALTY) --presence-penalty $(PRES_PEN) $(EXTRA_ARGS)

# ==========================================
# 3. Main Targets & Routers
# ==========================================
.PHONY: help config download run-cli run-server run-bench setup build clean check-model native-cli native-server native-bench docker-build docker-cli docker-server docker-bench docker-download native-download

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
	@echo "Hardware Profile: $(EXEC_MODE) Execution | Layers $(GPU_LAYERS) | Split $(SPLIT_MODE) | TensorSplit $(TENSOR_SPLIT)"
	@echo "Params: Temp $(TEMP), Top-P $(TOP_P), Top-K $(TOP_K), Min-P $(MIN_P), RepPen $(REP_PENALTY), PresPen $(PRES_PEN)"
	@if [ "$(IS_VISION_MODEL)" = "true" ]; then \
		echo "Vision Model: Yes (mmproj: $(MMPROJ_FILE))" ; \
	else \
		echo "Vision Model: No" ; \
	fi

config:
	@python3 config_menu.py

download:
ifeq ($(EXEC_MODE),docker)
	@echo "Routing download to Docker execution..."
	@$(MAKE) docker-download
else
	@echo "Routing download to Native execution..."
	@$(MAKE) native-download
endif

run-cli: check-model
ifeq ($(EXEC_MODE),docker)
	@echo "Routing to Docker execution..."
	@$(MAKE) docker-cli
else
	@echo "Routing to Native Metal/CUDA execution..."
	@$(MAKE) native-cli
endif

run-server: check-model
ifeq ($(EXEC_MODE),docker)
	@echo "Routing to Docker execution..."
	@$(MAKE) docker-server
else
	@echo "Routing to Native Metal/CUDA execution..."
	@$(MAKE) native-server
endif

run-bench: check-model
ifeq ($(EXEC_MODE),docker)
	@echo "Routing to Docker execution..."
	@$(MAKE) docker-bench
else
	@echo "Routing to Native Metal/CUDA execution..."
	@$(MAKE) native-bench
endif

# ==========================================
# 4. Native Execution Targets
# ==========================================
native-download:
	@if [ "$(IN_DOCKER)" != "true" ] && [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Running setup first..."; \
		$(MAKE) setup; \
	fi
	@echo "Downloading $(QUANT) weights from $(REPO) to $(LOCAL_DIR) using $(HF_CLI)..."
	env HF_HUB_ENABLE_HF_TRANSFER=1 $(HF_CLI) download $(REPO) --include "$(INCLUDE)" --local-dir $(LOCAL_DIR)
	@if [ "$(IS_VISION_MODEL)" = "true" ]; then \
		echo "Downloading mmproj-F16.gguf for vision model..." ; \
		env HF_HUB_ENABLE_HF_TRANSFER=1 $(HF_CLI) download $(REPO) --include "mmproj-F16.gguf" --local-dir $(LOCAL_DIR) ; \
	fi

native-cli: check-model
	@echo "Starting Native CLI using $(MODEL_FILE) in $(MODE) mode..."
	@if [ "$(IS_VISION_MODEL)" = "true" ]; then \
		echo "Command: $(LLAMA_PATH)/llama-cli -m $(MODEL_FILE) --mmproj $(MMPROJ_FILE) $(GPU_ARGS) $(CTX_ARGS) $(CLI_ARGS) $(ACTIVE_PARAMS)" ; \
		$(LLAMA_PATH)/llama-cli -m $(MODEL_FILE) --mmproj $(MMPROJ_FILE) $(GPU_ARGS) $(CTX_ARGS) $(CLI_ARGS) $(ACTIVE_PARAMS) ; \
	else \
		echo "Command: $(LLAMA_PATH)/llama-cli -m $(MODEL_FILE) $(GPU_ARGS) $(CTX_ARGS) $(CLI_ARGS) $(ACTIVE_PARAMS)" ; \
		$(LLAMA_PATH)/llama-cli -m $(MODEL_FILE) $(GPU_ARGS) $(CTX_ARGS) $(CLI_ARGS) $(ACTIVE_PARAMS) ; \
	fi

native-server: check-model
	@echo "Starting Native Server using $(MODEL_FILE) in $(MODE) mode..."
	@if [ "$(IS_VISION_MODEL)" = "true" ]; then \
		echo "Command: $(LLAMA_PATH)/llama-server -m $(MODEL_FILE) --mmproj $(MMPROJ_FILE) --alias \"$(REPO)\" --host 0.0.0.0 $(GPU_ARGS) $(CTX_ARGS) $(ACTIVE_PARAMS)" ; \
		$(LLAMA_PATH)/llama-server -m $(MODEL_FILE) --mmproj $(MMPROJ_FILE) --alias "$(REPO)" --host 0.0.0.0 $(GPU_ARGS) $(CTX_ARGS) $(ACTIVE_PARAMS) ; \
	else \
		echo "Command: $(LLAMA_PATH)/llama-server -m $(MODEL_FILE) --alias \"$(REPO)\" --host 0.0.0.0 $(GPU_ARGS) $(CTX_ARGS) $(ACTIVE_PARAMS)" ; \
		$(LLAMA_PATH)/llama-server -m $(MODEL_FILE) --alias "$(REPO)" --host 0.0.0.0 $(GPU_ARGS) $(CTX_ARGS) $(ACTIVE_PARAMS) ; \
	fi

native-bench: check-model
	@echo "Running Native Benchmarks on $(MODEL_FILE)..."
	$(LLAMA_PATH)/llama-bench -m $(MODEL_FILE) $(GPU_ARGS) $(BENCH_ARGS)

# ==========================================
# 5. Docker Wrapper Targets
# ==========================================
docker-download: docker-build
	@echo "Running Download in Docker..."
	docker run -it --rm \
		-e IN_DOCKER=true \
		-v $(HOST_MODELS_DIR):/app/models \
		-v $(PWD)/config.mk:/app/config.mk \
		-v $(PWD)/Makefile:/app/Makefile \
		$(DOCKER_IMAGE_NAME) make native-download

docker-build:
	@if [ "$(DOCKERFILE_EXT)" = "none" ]; then \
		echo "ERROR: Current profile is set to native execution only." ; exit 1 ; \
	fi
	@echo "Building Docker image using $(DOCKERFILE_EXT)..."
	docker build -f $(DOCKERFILE_EXT) -t $(DOCKER_IMAGE_NAME) .

docker-cli: docker-build
	@echo "Running CLI in Docker..."
	docker run --gpus all -it --rm \
		-e IN_DOCKER=true \
		-v $(HOST_MODELS_DIR):/app/models \
		-v $(PWD)/config.mk:/app/config.mk \
		-v $(PWD)/Makefile:/app/Makefile \
		$(DOCKER_IMAGE_NAME) make native-cli

docker-server: docker-build
	@echo "Running Server in Docker on port $(DOCKER_PORT)..."
	docker run --gpus all -it --rm \
		-p $(DOCKER_PORT):8080 \
		-e IN_DOCKER=true \
		-v $(HOST_MODELS_DIR):/app/models \
		-v $(PWD)/config.mk:/app/config.mk \
		-v $(PWD)/Makefile:/app/Makefile \
		$(DOCKER_IMAGE_NAME) make native-server

docker-bench: docker-build
	@echo "Running Benchmarks in Docker..."
	docker run --gpus all -it --rm \
		-e IN_DOCKER=true \
		-v $(HOST_MODELS_DIR):/app/models \
		-v $(PWD)/config.mk:/app/config.mk \
		-v $(PWD)/Makefile:/app/Makefile \
		$(DOCKER_IMAGE_NAME) make native-bench

# ==========================================
# 6. Utilities
# ==========================================
check-model:
	@if [ -z "$(MODEL_FILE)" ]; then \
		echo "ERROR: Model file not found in $(LOCAL_DIR)."; \
		echo "Please run 'make download' first."; \
		exit 1; \
	fi

setup:
	@echo "Installing system dependencies..."
	$(SETUP_CMD)
	@echo "Setting up Python virtual environment in $(VENV_DIR)..."
	python3 -m venv $(VENV_DIR)
	@echo "Installing huggingface_hub and hf_transfer for faster downloads..."
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install huggingface_hub hf_transfer
	@echo "Setup complete!"

build:
	@if [ ! -d "llama.cpp" ]; then git clone https://github.com/ggml-org/llama.cpp; fi
	cmake llama.cpp -B llama.cpp/build $(CMAKE_FLAGS)
	cmake --build llama.cpp/build --config Release -j --clean-first \
		--target llama-cli llama-mtmd-cli llama-server llama-gguf-split llama-bench
	cp llama.cpp/build/bin/llama-* llama.cpp/

clean:
	rm -rf llama.cpp/build config.mk $(VENV_DIR)
