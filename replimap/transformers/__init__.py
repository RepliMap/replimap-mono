"""
Transformers for RepliMap.

Transformers modify the resource graph before Terraform generation:
- Sanitization: Remove sensitive data
- Downsizing: Reduce instance sizes for cost savings
- Renaming: Apply environment-specific naming patterns
- Network remapping: Update network references for new VPC
"""

from .base import BaseTransformer, TransformationPipeline

__all__ = [
    "BaseTransformer",
    "TransformationPipeline",
]
