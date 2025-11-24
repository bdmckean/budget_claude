"""
Langfuse tracing integration for budget_claude.

This module provides utilities to trace LLM calls and other operations
for monitoring and debugging transaction categorization.
"""

import os
import time
from typing import Optional, Dict, Any
from functools import wraps

try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False


class LangfuseTracer:
    """Wrapper for Langfuse client with budget_claude-specific configuration."""

    def __init__(self):
        """Initialize the Langfuse tracer with environment variables."""
        # Only enable if LANGFUSE_PUBLIC_KEY is explicitly set
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.enabled = LANGFUSE_AVAILABLE and public_key is not None and public_key.strip() != ""
        self.client = None

        if self.enabled:
            try:
                self.client = Langfuse(
                    public_key=public_key,
                    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                    host=os.getenv("LANGFUSE_HOST", "http://localhost:3001"),
                )
            except Exception as e:
                print(f"Warning: Failed to initialize Langfuse: {e}")
                self.enabled = False
        else:
            # Silently disable if no public key set
            self.enabled = False

    def is_enabled(self) -> bool:
        """Check if Langfuse tracing is enabled and available."""
        return self.enabled

    def create_trace(
        self,
        name: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Create a new trace for monitoring an operation.

        Args:
            name: Name of the operation (e.g., "categorize_transaction")
            user_id: Optional user ID for tracking
            metadata: Optional metadata dictionary

        Returns:
            Trace object or None if tracing is disabled
        """
        if not self.enabled or not self.client:
            return None

        try:
            return self.client.trace(
                name=name,
                user_id=user_id or "system",
                metadata=metadata or {},
            )
        except Exception as e:
            print(f"Warning: Failed to create trace: {e}")
            return None

    def add_generation(
        self,
        trace,
        name: str,
        model: str,
        input_text: str,
        output_text: str,
        usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an LLM generation (API call) to the trace.

        Args:
            trace: Trace object from create_trace()
            name: Name of the generation (e.g., "ollama_categorization")
            model: Model name (e.g., "llama3.1:8b")
            input_text: Input/prompt sent to the model
            output_text: Output/response from the model
            usage: Optional dict with "prompt_tokens" and "completion_tokens"
            metadata: Optional additional metadata
        """
        if not trace:
            return

        try:
            # Create metadata with size information
            gen_metadata = metadata or {}
            gen_metadata["input_length"] = len(input_text) if input_text else 0
            gen_metadata["output_length"] = len(output_text) if output_text else 0

            # For large prompts (>10KB), truncate the input to first 5KB and last 2KB for readability
            truncated_input = input_text
            if len(input_text) > 10000:
                truncated_input = input_text[:5000] + "\n\n[... truncated ...]\n\n" + input_text[-2000:]
                gen_metadata["input_truncated"] = True

            # For large outputs (>5KB), truncate to first 2KB and last 2KB
            truncated_output = output_text
            if len(output_text) > 5000:
                truncated_output = output_text[:2000] + "\n\n[... truncated ...]\n\n" + output_text[-2000:]
                gen_metadata["output_truncated"] = True

            # Build kwargs for generation call, only including usage if it has valid data
            gen_kwargs = {
                "name": name,
                "model": model,
                "input": truncated_input,
                "output": truncated_output,
                "metadata": gen_metadata,
            }

            # Only add usage if it has the required fields
            if usage and any(k in usage for k in ['promptTokens', 'completionTokens', 'totalTokens', 'input', 'output']):
                gen_kwargs["usage"] = usage

            trace.generation(**gen_kwargs)
        except Exception as e:
            print(f"Warning: Failed to add generation to trace: {e}")

    def add_span(
        self,
        trace,
        name: str,
        input_text: Optional[str] = None,
        output_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a span (non-LLM operation) to the trace.

        Args:
            trace: Trace object from create_trace()
            name: Name of the span (e.g., "load_categories")
            input_text: Optional input data
            output_text: Optional output data
            metadata: Optional additional metadata
        """
        if not trace:
            return

        try:
            trace.span(
                name=name,
                input=input_text or "",
                output=output_text or "",
                metadata=metadata or {},
            )
        except Exception as e:
            print(f"Warning: Failed to add span to trace: {e}")

    def trace_llm_call(self, trace_name: str = "llm_call"):
        """
        Decorator to trace a function that calls the LLM.

        Usage:
            @tracer.trace_llm_call("categorize_transaction")
            def categorize_transaction(transaction_data):
                # Function that calls LLM
                pass
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                trace = self.create_trace(name=trace_name)
                try:
                    result = func(*args, trace=trace, **kwargs)
                    return result
                except Exception as e:
                    if trace:
                        self.add_span(
                            trace,
                            name="error",
                            input_text=func.__name__,
                            output_text=str(e),
                            metadata={"error": True, "error_type": type(e).__name__},
                        )
                    raise
                finally:
                    # Ensure trace is flushed
                    if trace and self.enabled and self.client:
                        try:
                            self.client.flush()
                        except Exception:
                            pass

            return wrapper

        return decorator


# Global instance
_tracer = None


def get_tracer() -> LangfuseTracer:
    """Get or create the global Langfuse tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = LangfuseTracer()
    return _tracer


def initialize_tracing():
    """Initialize Langfuse tracing (call this at app startup)."""
    tracer = get_tracer()
    if tracer.is_enabled():
        print("✓ Langfuse tracing enabled")
    else:
        print("⚠ Langfuse tracing disabled (check .env configuration)")
