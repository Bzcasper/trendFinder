from pathlib import Path
import os
import time
import json
import logging
from typing import List, Dict, Optional, Any, Union

import modal

# Constants
MINUTES = 60
GPU_CONFIG = "T4:1"  # Using 1x T4 GPU for more affordable inference
MODEL_CACHE_DIR = "/root/.cache/huggingface"
TOKEN = os.environ.get("MODAL_API_TOKEN", "ak-oH4YlsxdQDVeCLqtXREK3P")  # Replace with secure token

app = modal.App("trend-analyzer-api")

# Create a volume for model storage
model_volume = modal.Volume.from_name("trend-analyzer-model", create_if_missing=True)

# Build the base image with properly sequenced installation steps
server_image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install(
        "build-essential",
        "cmake",
        "git",
        "python3-dev",
    )
    # First upgrade pip and install basic dependencies
    .run_commands(
        "python -m pip install --upgrade pip",
        "python -m pip install packaging wheel setuptools"
    )
    # Install PyTorch first as it's a major dependency
    .pip_install("torch==2.1.2")
    # Install the rest of the dependencies in chunks
    .pip_install(
        "transformers==4.38.1",
        "accelerate==0.28.0",
        "pydantic==2.6.1",
        "flask==2.3.3",
        "werkzeug==2.3.7",
        "itsdangerous==2.1.2",
        "click==8.1.7",
        "hf_transfer",
    )
    # Install complex dependencies separately
    .pip_install(
        "safetensors==0.4.2",
        "sentencepiece==0.1.99",
        "protobuf==4.25.2",
        "einops==0.7.0",
    )
    # Optional - install quantization support
    .pip_install("bitsandbytes==0.43.0")
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1", 
        "HF_HOME": MODEL_CACHE_DIR,
        "TRANSFORMERS_CACHE": f"{MODEL_CACHE_DIR}/transformers"
    })
)

# Function to download the model
@app.function(
    image=server_image,
    volumes={MODEL_CACHE_DIR: model_volume},
    timeout=30 * MINUTES,
)
def download_model():
    """Download open source model from Hugging Face."""
    from huggingface_hub import snapshot_download
    import os
    
    print("🔍 Checking if model is already downloaded...")
    
    # Using DeepSeek-7B-Instruct-v1.5 as our default model
    model_id = "DeepSeek/coder-7b-instruct-v1.5"
    model_path = os.path.join(MODEL_CACHE_DIR, "models--DeepSeek--coder-7b-instruct-v1.5")
    
    if os.path.exists(model_path):
        print(f"✅ Model already downloaded at {model_path}")
        return
    
    # Download the model
    try:
        print(f"📥 Downloading {model_id} from Hugging Face...")
        snapshot_download(
            repo_id=model_id,
            local_dir=os.path.join(MODEL_CACHE_DIR, "models"),
        )
        print("✅ Model downloaded successfully")
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        raise
    
    # Commit the volume to persist the cache
    model_volume.commit()

# Main API server
@app.function(
    image=server_image,
    volumes={MODEL_CACHE_DIR: model_volume},
    gpu=GPU_CONFIG,
    timeout=15 * MINUTES,
    scaledown_window=10 * MINUTES,  # Auto-shutdown after 10 minutes of inactivity
    max_containers=3,  # Allow up to 3 concurrent requests
)
@modal.asgi_app()
def trend_analyzer_api():
    """Flask API server for DeepSeek AI chat completions."""
    from flask import Flask, request, jsonify, Response, stream_with_context
    import torch
    from threading import Thread
    import time
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize Flask app
    app = Flask(__name__)
    
    # Download model if needed
    try:
        download_model.remote()
        model_volume.reload()
    except Exception as e:
        logger.error(f"Error during model download: {e}")
        # Continue anyway - we'll try to load from cache if available
    
    # Initialize model class
    class DeepSeekModel:
        def __init__(self):
            self.model = None
            self.tokenizer = None
            
        def load_model(self):
            """Load DeepSeek model with optimized parameters."""
            if self.model is not None:
                return
                
            logger.info("🔄 Loading DeepSeek model...")
            
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch
                
                # Load tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(
                    "DeepSeek/coder-7b-instruct-v1.5",
                    cache_dir=MODEL_CACHE_DIR,
                    trust_remote_code=True
                )
                
                # Load model with BF16 precision and quantization for efficiency
                self.model = AutoModelForCausalLM.from_pretrained(
                    "DeepSeek/coder-7b-instruct-v1.5",
                    cache_dir=MODEL_CACHE_DIR,
                    torch_dtype=torch.bfloat16,
                    trust_remote_code=True,
                    device_map="auto",  # Automatically distribute model across available GPUs
                    load_in_8bit=True   # 8-bit quantization for memory efficiency
                )
                
                logger.info("✅ DeepSeek model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load model: {str(e)}")
                raise
                
        def unload_model(self):
            """Unload model to free memory."""
            if self.model is not None:
                del self.model
                del self.tokenizer
                self.model = None
                self.tokenizer = None
                import gc
                gc.collect()
                torch.cuda.empty_cache()
                logger.info("🧹 Model unloaded to free memory")
                
        def format_prompt(self, messages):
            """Format messages for DeepSeek model."""
            formatted_prompt = ""
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                
                if role == "system":
                    formatted_prompt += f"<s>[INST] {content} [/INST]"
                elif role == "user":
                    formatted_prompt += f"<s>[INST] {content} [/INST]"
                elif role == "assistant":
                    formatted_prompt += f" {content} </s>"
            
            # Add final marker for completion
            if not formatted_prompt.endswith("</s>"):
                formatted_prompt += " "
            return formatted_prompt
                
        def generate(self, messages, **kwargs):
            """Generate completion for chat messages using transformers."""
            self.load_model()
            
            # Format prompt according to DeepSeek's format
            prompt = self.format_prompt(messages)
            
            # Extract generation parameters with defaults
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1024)
            stop = kwargs.get("stop", [])
            stream = kwargs.get("stream", False)
            
            # Tokenize the input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            # Define generation config
            generation_config = {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "do_sample": temperature > 0.0,
                "top_p": 0.95,
                "pad_token_id": self.tokenizer.eos_token_id,
            }
            
            if stream:
                # For streaming generation, we need to use a different approach
                from transformers import TextIteratorStreamer
                
                # Create a streamer that will yield tokens as they're generated
                streamer = TextIteratorStreamer(
                    self.tokenizer,
                    skip_prompt=True,
                    skip_special_tokens=True
                )
                
                generation_kwargs = {
                    **generation_config,
                    "streamer": streamer,
                    "input_ids": inputs.input_ids,
                    "attention_mask": inputs.attention_mask,
                }
                
                # Start generation in a separate thread
                thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
                thread.start()
                
                # Return a generator that yields tokens as they're generated
                def stream_generator():
                    for text in streamer:
                        yield {
                            "choices": [{
                                "text": text,
                                "index": 0,
                                "finish_reason": None
                            }]
                        }
                
                return stream_generator()
            else:
                # For non-streaming generation
                with torch.no_grad():
                    output_ids = self.model.generate(
                        **inputs,
                        **generation_config
                    )
                
                # Decode the output
                output_text = self.tokenizer.decode(
                    output_ids[0][inputs.input_ids.shape[1]:],
                    skip_special_tokens=True
                )
                
                # Return in a format compatible with our API
                return {
                    "choices": [{
                        "text": output_text,
                        "index": 0,
                        "finish_reason": "stop"
                    }]
                }
    
    # Import TextIteratorStreamer for streaming
    from transformers import TextIteratorStreamer
    
    # Initialize model singleton
    model = DeepSeekModel()
    
    @app.route("/", methods=["GET"])
    def index():
        """API documentation endpoint."""
        return jsonify({
            "status": "online",
            "model": "DeepSeek 7B Instruct v1.5",
            "endpoints": {
                "/v1/chat/completions": "Chat completions endpoint (OpenAI-compatible)",
                "/v1/completions": "Text completions endpoint",
                "/health": "Health check endpoint"
            }
        })
    
    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok"})
    
    @app.before_request
    def verify_token():
        """Verify API token before handling request."""
        # Skip authentication for docs and health check
        if request.path in ["/", "/health"]:
            return
            
        auth_token = request.headers.get("Authorization", "")
        if auth_token.startswith("Bearer "):
            auth_token = auth_token[7:]
        
        # Also check X-API-Key header as an alternative
        if not auth_token:
            auth_token = request.headers.get("X-API-Key", "")
            
        if auth_token != TOKEN:
            return jsonify({"error": "Unauthorized: Invalid API key"}), 401
    
    @app.route("/v1/chat/completions", methods=["POST"])
    def chat_completions():
        """OpenAI-compatible chat completions endpoint."""
        try:
            data = request.json
            
            # Extract parameters
            messages = data.get("messages", [])
            if not messages:
                return jsonify({"error": "No messages provided"}), 400
                
            # Extract other parameters
            temperature = data.get("temperature", 0.7)
            max_tokens = data.get("max_tokens", 1024)
            stop = data.get("stop", None)
            stream = data.get("stream", False)
            
            # Custom parameters handling
            params = {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
            }
            
            if stop:
                params["stop"] = stop if isinstance(stop, list) else [stop]
            
            # Process streaming request
            if stream:
                def generate_stream():
                    start_time = time.time()
                    completion_id = f"chatcmpl-{int(start_time * 1000)}"
                    
                    yield f"data: {json.dumps({'id': completion_id, 'object': 'chat.completion.chunk', 'created': int(start_time), 'model': 'deepseek-coder-7b-instruct', 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]})}\n\n"
                    
                    # Get streaming completion
                    full_text = ""
                    for completion in model.generate(messages, **params):
                        delta_text = completion["choices"][0]["text"]
                        full_text += delta_text
                        
                        chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": "deepseek-coder-7b-instruct",
                            "choices": [{
                                "index": 0,
                                "delta": {"content": delta_text},
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                    
                    # Send final chunk
                    end_chunk = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "deepseek-coder-7b-instruct",
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop"
                        }]
                    }
                    yield f"data: {json.dumps(end_chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                
                return Response(
                    stream_with_context(generate_stream()),
                    content_type="text/event-stream"
                )
            
            # Process non-streaming request
            else:
                start_time = time.time()
                completion = model.generate(messages, **params)
                
                response = {
                    "id": f"chatcmpl-{int(start_time * 1000)}",
                    "object": "chat.completion",
                    "created": int(start_time),
                    "model": "deepseek-coder-7b-instruct",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": completion["choices"][0]["text"]
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": -1,  # Token counting not implemented
                        "completion_tokens": -1,
                        "total_tokens": -1
                    }
                }
                
                return jsonify(response)
        
        except Exception as e:
            import traceback
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"Error: {error_msg}\n{stack_trace}")
            return jsonify({"error": error_msg}), 500
    
    # Handle regular completions endpoint
    @app.route("/v1/completions", methods=["POST"])
    def completions():
        """Text completions endpoint."""
        try:
            data = request.json
            
            # Extract prompt and convert to messages format
            prompt = data.get("prompt", "")
            if not prompt:
                return jsonify({"error": "No prompt provided"}), 400
                
            messages = [{"role": "user", "content": prompt}]
            
            # Extract other parameters
            temperature = data.get("temperature", 0.7)
            max_tokens = data.get("max_tokens", 1024)
            stop = data.get("stop", None)
            stream = data.get("stream", False)
            
            # Forward to the chat completions handler with messages
            params = {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
            }
            
            if stop:
                params["stop"] = stop if isinstance(stop, list) else [stop]
            
            # Process request based on streaming mode
            if stream:
                def generate_stream():
                    start_time = time.time()
                    completion_id = f"cmpl-{int(start_time * 1000)}"
                    
                    # Get streaming completion
                    for completion in model.generate(messages, **params):
                        delta_text = completion["choices"][0]["text"]
                        
                        chunk = {
                            "id": completion_id,
                            "object": "text_completion",
                            "created": int(time.time()),
                            "model": "deepseek-coder-7b-instruct",
                            "choices": [{
                                "text": delta_text,
                                "index": 0,
                                "logprobs": None,
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                    
                    # Send final chunk
                    yield "data: [DONE]\n\n"
                
                return Response(
                    stream_with_context(generate_stream()),
                    content_type="text/event-stream"
                )
            
            # Process non-streaming request
            else:
                start_time = time.time()
                completion = model.generate(messages, **params)
                
                response = {
                    "id": f"cmpl-{int(start_time * 1000)}",
                    "object": "text_completion",
                    "created": int(start_time),
                    "model": "deepseek-coder-7b-instruct",
                    "choices": [{
                        "text": completion["choices"][0]["text"],
                        "index": 0,
                        "logprobs": None,
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": -1,
                        "completion_tokens": -1,
                        "total_tokens": -1
                    }
                }
                
                return jsonify(response)
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return app

@app.local_entrypoint()
def main():
    """Deploy and test the Modal API server."""
    # Ensure model is downloaded
    download_model.remote()
    
    # Print the URL for the API
    print(f"✅ API server is running at: {trend_analyzer_api.web_url}")
    
    # Print a test command
    print("\n🧪 Test the API with cURL:")
    print(f'''curl -X POST {trend_analyzer_api.web_url}/v1/chat/completions \\
    -H "Content-Type: application/json" \\
    -H "Authorization: Bearer {TOKEN}" \\
    -d '{{
        "model": "deepseek-coder-7b-instruct",
        "messages": [
            {{"role": "system", "content": "You are a helpful assistant."}},
            {{"role": "user", "content": "Summarize the latest trends in AI based on these stories: [Insert stories here]"}}
        ],
        "temperature": 0.7,
        "max_tokens": 256
    }}'
    ''')

# Run locally with: modal run modal_server.py
