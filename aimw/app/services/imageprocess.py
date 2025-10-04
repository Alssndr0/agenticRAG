import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from pdf2image import convert_from_path
from PIL import Image


class ImageQuality(Enum):
    """Enum for image quality assessment."""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"


@dataclass
class QualityMetrics:
    """Data class to hold image quality metrics."""

    width: int
    height: int
    total_pixels: int
    megapixels: float
    aspect_ratio: float
    color_mode: str
    file_size_mb: float

    # Quality metrics
    sharpness_score: float
    contrast_std: float
    brightness_mean: float
    dynamic_range: int

    # Assessments
    overall_quality: ImageQuality
    issues: List[str]
    warnings: List[str]

    # VLLM compatibility
    suitable_for_gemini: bool
    suitable_for_qwen: bool
    estimated_gemini_tokens: int
    estimated_qwen_tokens: int


class ImageQualityChecker:
    """
    Production-grade image quality checker for VLLM document processing.
    """

    # Quality thresholds
    MIN_SHARPNESS = 100.0
    MIN_CONTRAST = 30.0
    MIN_DYNAMIC_RANGE = 100
    MIN_BRIGHTNESS = 50
    MAX_BRIGHTNESS = 200

    # VLLM requirements
    GEMINI_MIN_PIXELS = 384 * 384
    GEMINI_TILE_SIZE = 768
    GEMINI_TOKENS_PER_TILE = 258
    QWEN_MIN_PIXELS = 224 * 224
    QWEN_PIXELS_PER_TOKEN = 32 * 32

    @staticmethod
    def calculate_sharpness(img_array: np.ndarray) -> float:
        """
        Calculate image sharpness using Laplacian variance method.
        Higher values indicate sharper images.

        Args:
            img_array: Grayscale image as numpy array

        Returns:
            Sharpness score (higher is better)
        """
        # Laplacian kernel for edge detection
        laplacian_kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])

        # Apply convolution manually (avoids scipy dependency)
        h, w = img_array.shape
        kh, kw = laplacian_kernel.shape
        edges = np.zeros((h - kh + 1, w - kw + 1))

        for i in range(edges.shape[0]):
            for j in range(edges.shape[1]):
                edges[i, j] = np.sum(
                    img_array[i : i + kh, j : j + kw] * laplacian_kernel
                )

        # Variance of Laplacian
        sharpness = np.var(edges)
        return float(sharpness)

    @staticmethod
    def estimate_gemini_tokens(width: int, height: int) -> int:
        """
        Estimate token count for Gemini models.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Estimated token count
        """
        total_pixels = width * height

        # If image is small enough, it's just 258 tokens
        if total_pixels <= ImageQualityChecker.GEMINI_MIN_PIXELS:
            return ImageQualityChecker.GEMINI_TOKENS_PER_TILE

        # Calculate number of tiles needed
        tile_size = ImageQualityChecker.GEMINI_TILE_SIZE
        tiles_x = int(np.ceil(width / tile_size))
        tiles_y = int(np.ceil(height / tile_size))
        total_tiles = tiles_x * tiles_y

        return total_tiles * ImageQualityChecker.GEMINI_TOKENS_PER_TILE

    @staticmethod
    def estimate_qwen_tokens(width: int, height: int) -> int:
        """
        Estimate token count for Qwen models.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Estimated token count
        """
        total_pixels = width * height
        tokens = max(
            4, int(np.ceil(total_pixels / ImageQualityChecker.QWEN_PIXELS_PER_TOKEN))
        )
        return tokens

    @classmethod
    def assess_quality(cls, metrics: Dict) -> Tuple[ImageQuality, List[str], List[str]]:
        """
        Assess overall image quality based on metrics.

        Args:
            metrics: Dictionary of quality metrics

        Returns:
            Tuple of (quality_rating, issues, warnings)
        """
        issues = []
        warnings = []
        score = 0  # Higher is better

        # Check sharpness
        if metrics["sharpness_score"] < cls.MIN_SHARPNESS:
            issues.append(
                f"Low sharpness ({metrics['sharpness_score']:.1f} < {cls.MIN_SHARPNESS})"
            )
            score -= 2
        elif metrics["sharpness_score"] < cls.MIN_SHARPNESS * 2:
            warnings.append(f"Moderate sharpness ({metrics['sharpness_score']:.1f})")
        else:
            score += 2

        # Check contrast
        if metrics["contrast_std"] < cls.MIN_CONTRAST:
            issues.append(f"Low contrast (std={metrics['contrast_std']:.1f})")
            score -= 2
        elif metrics["contrast_std"] < cls.MIN_CONTRAST * 1.5:
            warnings.append(f"Moderate contrast (std={metrics['contrast_std']:.1f})")
        else:
            score += 1

        # Check brightness
        if metrics["brightness_mean"] < cls.MIN_BRIGHTNESS:
            issues.append(f"Too dark (brightness={metrics['brightness_mean']:.1f})")
            score -= 2
        elif metrics["brightness_mean"] > cls.MAX_BRIGHTNESS:
            issues.append(
                f"Too bright/washed out (brightness={metrics['brightness_mean']:.1f})"
            )
            score -= 2
        elif (
            cls.MIN_BRIGHTNESS + 20
            < metrics["brightness_mean"]
            < cls.MAX_BRIGHTNESS - 20
        ):
            score += 1

        # Check dynamic range
        if metrics["dynamic_range"] < cls.MIN_DYNAMIC_RANGE:
            issues.append(f"Limited dynamic range ({metrics['dynamic_range']})")
            score -= 1
        else:
            score += 1

        # Check resolution
        if metrics["total_pixels"] < 1_000_000:  # Less than 1 megapixel
            warnings.append(f"Low resolution ({metrics['megapixels']:.1f} MP)")
        elif metrics["total_pixels"] > 50_000_000:  # More than 50 megapixels
            warnings.append(
                f"Very high resolution ({metrics['megapixels']:.1f} MP) - may be unnecessarily large"
            )
        else:
            score += 1

        # Determine overall quality
        if score >= 4:
            quality = ImageQuality.EXCELLENT
        elif score >= 2:
            quality = ImageQuality.GOOD
        elif score >= 0:
            quality = ImageQuality.ACCEPTABLE
        elif score >= -2:
            quality = ImageQuality.POOR
        else:
            quality = ImageQuality.UNACCEPTABLE

        if not issues:
            issues.append("No critical issues detected")

        return quality, issues, warnings

    @classmethod
    def check_image_quality(cls, image_path: str) -> QualityMetrics:
        """
        Comprehensive image quality check for VLLM document processing.

        Args:
            image_path: Path to the image file

        Returns:
            QualityMetrics object with all assessment results
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                total_pixels = width * height
                megapixels = total_pixels / 1_000_000
                aspect_ratio = width / height
                color_mode = img.mode

                # Get file size
                file_size_mb = os.path.getsize(image_path) / (1024 * 1024)

                # Convert to grayscale for analysis
                img_gray = img.convert("L")
                img_array = np.array(img_gray, dtype=np.float32)

                # Calculate quality metrics
                sharpness_score = cls.calculate_sharpness(img_array)
                contrast_std = float(np.std(img_array))
                brightness_mean = float(np.mean(img_array))
                dynamic_range = int(np.max(img_array) - np.min(img_array))

                # Assess quality
                metrics_dict = {
                    "sharpness_score": sharpness_score,
                    "contrast_std": contrast_std,
                    "brightness_mean": brightness_mean,
                    "dynamic_range": dynamic_range,
                    "total_pixels": total_pixels,
                    "megapixels": megapixels,
                }

                quality, issues, warnings = cls.assess_quality(metrics_dict)

                # VLLM compatibility
                suitable_for_gemini = total_pixels >= cls.GEMINI_MIN_PIXELS
                suitable_for_qwen = total_pixels >= cls.QWEN_MIN_PIXELS
                estimated_gemini_tokens = cls.estimate_gemini_tokens(width, height)
                estimated_qwen_tokens = cls.estimate_qwen_tokens(width, height)

                return QualityMetrics(
                    width=width,
                    height=height,
                    total_pixels=total_pixels,
                    megapixels=round(megapixels, 2),
                    aspect_ratio=round(aspect_ratio, 2),
                    color_mode=color_mode,
                    file_size_mb=round(file_size_mb, 2),
                    sharpness_score=round(sharpness_score, 2),
                    contrast_std=round(contrast_std, 2),
                    brightness_mean=round(brightness_mean, 1),
                    dynamic_range=dynamic_range,
                    overall_quality=quality,
                    issues=issues,
                    warnings=warnings,
                    suitable_for_gemini=suitable_for_gemini,
                    suitable_for_qwen=suitable_for_qwen,
                    estimated_gemini_tokens=estimated_gemini_tokens,
                    estimated_qwen_tokens=estimated_qwen_tokens,
                )
        except Exception as e:
            raise RuntimeError(f"Failed to analyze image {image_path}: {str(e)}")


def pdf_to_images(
    pdf_path: str,
    output_folder: str = "output_images",
    dpi: int = 300,
    fmt: str = "PNG",
) -> List[str]:
    """
    Convert a PDF file to images (one image per page).

    Args:
        pdf_path: Path to the PDF file
        output_folder: Folder where images will be saved
        dpi: Resolution for the conversion (default: 300)
        fmt: Output image format (default: PNG)

    Returns:
        List of paths to the generated image files

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        RuntimeError: If conversion fails
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # Get the PDF filename without extension
    pdf_name = Path(pdf_path).stem

    try:
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=dpi)
    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF: {str(e)}")

    # Save images and collect their paths
    image_paths = []
    for i, image in enumerate(images, start=1):
        image_path = os.path.join(output_folder, f"{pdf_name}_page_{i}.{fmt.lower()}")
        image.save(image_path, fmt)
        image_paths.append(image_path)
        print(f"✓ Saved: {image_path}")

    print(f"\n✓ Total pages converted: {len(image_paths)}")
    return image_paths


def analyze_images_for_vllm(
    image_paths: List[str], verbose: bool = True
) -> Dict[str, QualityMetrics]:
    """
    Analyze multiple images for VLLM processing suitability.

    Args:
        image_paths: List of paths to image files
        verbose: If True, print detailed analysis

    Returns:
        Dictionary mapping image paths to QualityMetrics
    """
    results = {}

    if verbose:
        print("\n" + "=" * 80)
        print("IMAGE QUALITY ANALYSIS FOR VLLM PROCESSING")
        print("=" * 80)

    for img_path in image_paths:
        filename = Path(img_path).name

        try:
            metrics = ImageQualityChecker.check_image_quality(img_path)
            results[img_path] = metrics

            if verbose:
                print(f"\n📄 {filename}")
                print(f"  {'─' * 76}")

                # Basic info
                print(
                    f"  📐 Dimensions: {metrics.width} × {metrics.height} pixels "
                    f"({metrics.megapixels} MP)"
                )
                print(f"  📊 Aspect ratio: {metrics.aspect_ratio:.2f}:1")
                print(f"  🎨 Color mode: {metrics.color_mode}")
                print(f"  💾 File size: {metrics.file_size_mb} MB")

                # Quality metrics
                print("\n  Quality Metrics:")
                print(
                    f"    • Sharpness: {metrics.sharpness_score:.1f} "
                    f"{'✓' if metrics.sharpness_score >= ImageQualityChecker.MIN_SHARPNESS else '⚠'}"
                )
                print(
                    f"    • Contrast (std): {metrics.contrast_std:.1f} "
                    f"{'✓' if metrics.contrast_std >= ImageQualityChecker.MIN_CONTRAST else '⚠'}"
                )
                print(
                    f"    • Brightness: {metrics.brightness_mean:.1f} "
                    f"{'✓' if ImageQualityChecker.MIN_BRIGHTNESS < metrics.brightness_mean < ImageQualityChecker.MAX_BRIGHTNESS else '⚠'}"
                )
                print(
                    f"    • Dynamic range: {metrics.dynamic_range} "
                    f"{'✓' if metrics.dynamic_range >= ImageQualityChecker.MIN_DYNAMIC_RANGE else '⚠'}"
                )

                # Overall assessment
                quality_emoji = {
                    ImageQuality.EXCELLENT: "🟢",
                    ImageQuality.GOOD: "🟢",
                    ImageQuality.ACCEPTABLE: "🟡",
                    ImageQuality.POOR: "🟠",
                    ImageQuality.UNACCEPTABLE: "🔴",
                }
                print(
                    f"\n  {quality_emoji[metrics.overall_quality]} Overall Quality: "
                    f"{metrics.overall_quality.value.upper()}"
                )

                # Issues and warnings
                if (
                    len(metrics.issues) > 1
                    or metrics.issues[0] != "No critical issues detected"
                ):
                    print("  ⚠️  Issues:")
                    for issue in metrics.issues:
                        if issue != "No critical issues detected":
                            print(f"      • {issue}")

                if metrics.warnings:
                    print("  ⚡ Warnings:")
                    for warning in metrics.warnings:
                        print(f"      • {warning}")

                # VLLM compatibility
                print("\n  VLLM Compatibility:")
                print(
                    f"    • Gemini: {'✓ Suitable' if metrics.suitable_for_gemini else '✗ Not suitable'} "
                    f"(~{metrics.estimated_gemini_tokens} tokens)"
                )
                print(
                    f"    • Qwen: {'✓ Suitable' if metrics.suitable_for_qwen else '✗ Not suitable'} "
                    f"(~{metrics.estimated_qwen_tokens} tokens)"
                )

        except Exception as e:
            print(f"\n❌ {filename}")
            print(f"  Error: {str(e)}")
            results[img_path] = None

    if verbose:
        print("\n" + "=" * 80)
        _print_summary(results)

    return results


def _print_summary(results: Dict[str, Optional[QualityMetrics]]) -> None:
    """Print summary statistics of image analysis."""
    successful = [m for m in results.values() if m is not None]

    if not successful:
        print("No images successfully analyzed.")
        return

    print("\n📊 SUMMARY")
    print("─" * 80)

    quality_counts = {}
    for quality in ImageQuality:
        count = sum(1 for m in successful if m.overall_quality == quality)
        if count > 0:
            quality_counts[quality] = count

    print("  Quality Distribution:")
    for quality, count in quality_counts.items():
        print(f"    • {quality.value.capitalize()}: {count}")

    avg_sharpness = np.mean([m.sharpness_score for m in successful])
    avg_contrast = np.mean([m.contrast_std for m in successful])
    avg_brightness = np.mean([m.brightness_mean for m in successful])

    print("\n  Average Metrics:")
    print(f"    • Sharpness: {avg_sharpness:.1f}")
    print(f"    • Contrast: {avg_contrast:.1f}")
    print(f"    • Brightness: {avg_brightness:.1f}")

    gemini_compatible = sum(1 for m in successful if m.suitable_for_gemini)
    qwen_compatible = sum(1 for m in successful if m.suitable_for_qwen)

    print("\n  VLLM Compatibility:")
    print(f"    • Gemini-ready: {gemini_compatible}/{len(successful)}")
    print(f"    • Qwen-ready: {qwen_compatible}/{len(successful)}")


# Example usage
if __name__ == "__main__":
    # Example: Convert PDF to images and analyze
    pdf_file = "/Users/alessandro/Development/agenticRAG/data/TestCreditLetter.pdf"

    if os.path.exists(pdf_file):
        try:
            # Convert PDF to images with high DPI for better quality
            image_files = pdf_to_images(
                pdf_path=pdf_file,
                output_folder="pdf_images",
                dpi=300,  # 300 DPI is good for document processing
                fmt="PNG",
            )

            # Analyze all images for VLLM processing
            analysis_results = analyze_images_for_vllm(image_files, verbose=True)

            # Example: Filter for high-quality images only
            high_quality_images = [
                path
                for path, metrics in analysis_results.items()
                if metrics
                and metrics.overall_quality
                in [ImageQuality.EXCELLENT, ImageQuality.GOOD]
            ]

            print(
                f"\n✓ High-quality images suitable for processing: {len(high_quality_images)}"
            )

        except Exception as e:
            print(f"❌ Error: {str(e)}")
    else:
        print(f"❌ PDF file '{pdf_file}' not found.")
        print("\nExample usage:")
        print("  image_paths = pdf_to_images('document.pdf', dpi=300)")
        print("  results = analyze_images_for_vllm(image_paths)")
