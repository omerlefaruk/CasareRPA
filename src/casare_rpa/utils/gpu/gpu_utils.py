"""
GPU acceleration utilities for CasareRPA.

Provides GPU detection, configuration, and accelerated operations
with automatic CPU fallback when GPU is not available.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger


@dataclass
class GPUCapabilities:
    """GPU capability detection results."""

    cuda_available: bool = False
    cuda_version: str | None = None
    cuda_device_name: str | None = None
    cuda_memory_mb: int = 0

    opencl_available: bool = False
    opengl_available: bool = False
    opengl_version: str | None = None

    onnx_gpu_available: bool = False
    opencv_cuda_available: bool = False

    def __str__(self) -> str:
        parts = []
        if self.cuda_available:
            parts.append(f"CUDA {self.cuda_version} ({self.cuda_device_name})")
        if self.opencv_cuda_available:
            parts.append("OpenCV CUDA")
        if self.onnx_gpu_available:
            parts.append("ONNX GPU")
        if self.opengl_available:
            parts.append(f"OpenGL {self.opengl_version}")
        return ", ".join(parts) if parts else "CPU only"


# Cached capabilities
_cached_capabilities: GPUCapabilities | None = None


def get_gpu_capabilities(force_refresh: bool = False) -> GPUCapabilities:
    """
    Detect available GPU capabilities.

    Results are cached for performance. Use force_refresh=True to re-detect.

    Returns:
        GPUCapabilities with detection results
    """
    global _cached_capabilities

    if _cached_capabilities is not None and not force_refresh:
        return _cached_capabilities

    caps = GPUCapabilities()

    # Check CUDA via PyTorch (most reliable)
    try:
        import torch

        if torch.cuda.is_available():
            caps.cuda_available = True
            caps.cuda_version = torch.version.cuda
            caps.cuda_device_name = torch.cuda.get_device_name(0)
            caps.cuda_memory_mb = torch.cuda.get_device_properties(0).total_memory // (1024 * 1024)
            logger.debug(f"CUDA detected via PyTorch: {caps.cuda_device_name}")
    except ImportError:
        pass

    # Check CUDA via CuPy (alternative)
    if not caps.cuda_available:
        try:
            import cupy

            caps.cuda_available = True
            caps.cuda_device_name = cupy.cuda.runtime.getDeviceProperties(0)["name"]
            caps.cuda_memory_mb = cupy.cuda.runtime.getDeviceProperties(0)["totalGlobalMem"] // (
                1024 * 1024
            )
            logger.debug(f"CUDA detected via CuPy: {caps.cuda_device_name}")
        except (ImportError, Exception):
            pass

    # Check OpenCV CUDA support
    try:
        import cv2

        # Check if CUDA is available in OpenCV build
        build_info = cv2.getBuildInformation()
        if "CUDA" in build_info and "YES" in build_info.split("CUDA")[1][:50]:
            # Verify we can actually create a GPU mat
            try:
                cv2.cuda_GpuMat()
                caps.opencv_cuda_available = True
                logger.debug("OpenCV CUDA support detected")
            except Exception:
                pass
    except ImportError:
        pass

    # Check ONNX Runtime GPU providers
    try:
        import onnxruntime as ort

        providers = ort.get_available_providers()
        if "CUDAExecutionProvider" in providers:
            caps.onnx_gpu_available = True
            logger.debug("ONNX CUDAExecutionProvider available")
        elif "DmlExecutionProvider" in providers:
            # DirectML for AMD/Intel GPUs on Windows
            caps.onnx_gpu_available = True
            logger.debug("ONNX DmlExecutionProvider available")
    except ImportError:
        pass

    # Check OpenGL (always available on modern systems)
    try:
        from PySide6.QtGui import QOpenGLContext

        caps.opengl_available = True
        # Version is detected when context is active
        caps.opengl_version = "3.3+"  # Minimum we require
    except ImportError:
        pass

    _cached_capabilities = caps
    logger.debug(f"GPU capabilities: {caps}")
    return caps


def is_cuda_available() -> bool:
    """Check if CUDA is available."""
    return get_gpu_capabilities().cuda_available


def is_gpu_available() -> bool:
    """Check if any GPU acceleration is available."""
    caps = get_gpu_capabilities()
    return caps.cuda_available or caps.opencv_cuda_available or caps.onnx_gpu_available


def get_gpu_info() -> dict[str, Any]:
    """Get GPU information as a dictionary for UI display."""
    caps = get_gpu_capabilities()
    return {
        "cuda_available": caps.cuda_available,
        "cuda_device": caps.cuda_device_name,
        "cuda_memory_mb": caps.cuda_memory_mb,
        "opencv_cuda": caps.opencv_cuda_available,
        "onnx_gpu": caps.onnx_gpu_available,
        "opengl": caps.opengl_available,
        "summary": str(caps),
    }


def configure_onnx_gpu() -> list[str]:
    """
    Configure ONNX Runtime to use GPU if available.

    Returns:
        List of execution providers to use (in priority order)
    """
    caps = get_gpu_capabilities()

    providers = []
    if caps.onnx_gpu_available:
        try:
            import onnxruntime as ort

            available = ort.get_available_providers()
            if "CUDAExecutionProvider" in available:
                providers.append("CUDAExecutionProvider")
            if "DmlExecutionProvider" in available:
                providers.append("DmlExecutionProvider")
        except ImportError:
            pass

    # Always include CPU as fallback
    providers.append("CPUExecutionProvider")
    logger.debug(f"ONNX providers configured: {providers}")
    return providers


def gpu_accelerated_template_match(
    image: np.ndarray,
    template: np.ndarray,
    method: int = None,
) -> tuple[np.ndarray, str | None]:
    """
    GPU-accelerated template matching with CPU fallback.

    Args:
        image: Source image (grayscale or color)
        template: Template to match
        method: OpenCV match method (default: TM_CCOEFF_NORMED)

    Returns:
        Tuple of (result array, backend used: "cuda" or "cpu")
    """
    import cv2

    if method is None:
        method = cv2.TM_CCOEFF_NORMED

    caps = get_gpu_capabilities()

    # Try GPU first
    if caps.opencv_cuda_available:
        try:
            # Upload to GPU
            gpu_image = cv2.cuda_GpuMat()
            gpu_template = cv2.cuda_GpuMat()
            gpu_image.upload(image)
            gpu_template.upload(template)

            # Create template matcher
            matcher = cv2.cuda.createTemplateMatching(gpu_image.type(), method)
            gpu_result = matcher.match(gpu_image, gpu_template)

            # Download result
            result = gpu_result.download()
            return result, "cuda"
        except Exception as e:
            logger.debug(f"GPU template match failed, using CPU: {e}")

    # CPU fallback
    result = cv2.matchTemplate(image, template, method)
    return result, "cpu"


def gpu_accelerated_image_compare(
    img1: np.ndarray,
    img2: np.ndarray,
) -> tuple[float, str | None]:
    """
    GPU-accelerated image similarity comparison with CPU fallback.

    Args:
        img1: First image
        img2: Second image (same size as img1)

    Returns:
        Tuple of (similarity 0.0-1.0, backend used)
    """
    caps = get_gpu_capabilities()

    # Try CuPy for GPU array operations
    if caps.cuda_available:
        try:
            import cupy as cp

            # Upload to GPU
            gpu_img1 = cp.asarray(img1.astype(np.float32))
            gpu_img2 = cp.asarray(img2.astype(np.float32))

            # Calculate difference
            diff = cp.abs(gpu_img1 - gpu_img2)
            max_diff = float(img1.max()) * img1.size
            actual_diff = float(cp.sum(diff))

            similarity = 1.0 - (actual_diff / max_diff) if max_diff > 0 else 1.0
            return similarity, "cuda"
        except Exception as e:
            logger.debug(f"GPU image compare failed, using CPU: {e}")

    # CPU fallback with NumPy
    diff = np.abs(img1.astype(np.float64) - img2.astype(np.float64))
    max_diff = float(img1.max()) * img1.size
    actual_diff = float(np.sum(diff))

    similarity = 1.0 - (actual_diff / max_diff) if max_diff > 0 else 1.0
    return similarity, "cpu"


# Initialize on module load
def _init_gpu():
    """Initialize GPU detection on first import."""
    try:
        get_gpu_capabilities()
    except Exception as e:
        logger.warning(f"GPU detection failed: {e}")


_init_gpu()
