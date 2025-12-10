"""
GPU acceleration utilities for CasareRPA.

Provides:
- GPU capability detection (CUDA, OpenCL, OpenGL)
- GPU-accelerated image operations with CPU fallback
- ONNX runtime GPU configuration
- GPU status monitoring
"""

from casare_rpa.utils.gpu.gpu_utils import (
    GPUCapabilities,
    get_gpu_capabilities,
    is_cuda_available,
    is_gpu_available,
    get_gpu_info,
    gpu_accelerated_template_match,
    gpu_accelerated_image_compare,
    configure_onnx_gpu,
)

__all__ = [
    "GPUCapabilities",
    "get_gpu_capabilities",
    "is_cuda_available",
    "is_gpu_available",
    "get_gpu_info",
    "gpu_accelerated_template_match",
    "gpu_accelerated_image_compare",
    "configure_onnx_gpu",
]
