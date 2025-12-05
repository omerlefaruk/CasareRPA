# OCR Technology Research Report 2024-2025

**Date**: 2025-12-04
**Researcher**: Claude (Research Specialist)
**Purpose**: Evaluate modern OCR technologies for CasareRPA platform

---

## Executive Summary

This report evaluates modern OCR technologies to replace pytesseract in CasareRPA. The research covers cloud-based APIs, local/offline libraries, and specialized solutions. Key findings:

1. **Best Overall Local OCR**: PaddleOCR (accuracy) or EasyOCR (ease of use)
2. **Best Cloud OCR**: Google Cloud Vision (general) or AWS Textract (documents)
3. **Best for Documents**: docTR or Surya OCR
4. **Best for Handwriting**: TrOCR (Microsoft)
5. **Best for Tables**: img2table + PaddleOCR backend

---

## 1. Cloud-Based OCR APIs

### 1.1 Google Cloud Vision OCR

| Attribute | Details |
|-----------|---------|
| **Accuracy** | 95-99% on printed text, excellent multilingual |
| **Best Use Cases** | General OCR, scene text, document scanning |
| **Pricing** | $1.50/1000 units (1001-5M), $0.60/1000 (5M+), First 1000 free/month |
| **Python SDK** | `google-cloud-vision` |
| **Features** | TEXT_DETECTION (scene text), DOCUMENT_TEXT_DETECTION (dense documents), handwriting support |
| **Languages** | 100+ languages |

**Pros**:
- Industry-leading accuracy
- Excellent documentation
- $300 free credits for new accounts
- Handles scene text and documents

**Cons**:
- Requires internet connection
- Per-image pricing can add up
- Google Cloud account required

### 1.2 AWS Textract

| Attribute | Details |
|-----------|---------|
| **Accuracy** | 95-98% on documents, excellent for forms/tables |
| **Best Use Cases** | Invoices, receipts, forms, tables, IDs |
| **Pricing** | $0.0015/page (Detect Text), $0.015/page (Forms+Tables+Queries) |
| **Python SDK** | `boto3`, `amazon-textract-textractor` (v1.9.2) |
| **Features** | Text detection, form extraction, table extraction, signature detection |
| **Free Tier** | 1000 pages/month for 3 months |

**Pros**:
- Best-in-class for structured documents
- Native table/form extraction
- Low per-page cost
- Excellent for invoices/receipts

**Cons**:
- AWS account required
- Complex API for advanced features
- US-focused pricing

### 1.3 Azure Computer Vision (Read API)

| Attribute | Details |
|-----------|---------|
| **Accuracy** | 94-98% on printed text, good handwriting |
| **Best Use Cases** | Enterprise documents, Microsoft ecosystem |
| **Pricing** | Tiered per 1000 transactions, Free tier (F0) available |
| **Python SDK** | `azure-ai-vision-imageanalysis` (replaces deprecated `azure-cognitiveservices-vision-computervision`) |
| **Features** | Printed/handwritten text, layout analysis |
| **Languages** | 100+ languages |

**Pros**:
- Good Microsoft ecosystem integration
- Competitive pricing
- Strong enterprise support

**Cons**:
- SDK deprecated in 2024, must use new package
- Azure account required
- Less specialized for documents than Textract

---

## 2. Local/Offline OCR Libraries

### 2.1 PaddleOCR (Recommended)

| Attribute | Details |
|-----------|---------|
| **Accuracy** | 95%+ on documents, state-of-the-art for Asian languages |
| **Speed** | Fast with GPU, moderate on CPU |
| **Python Package** | `paddlepaddle`, `paddleocr` |
| **Model Size** | ~150MB (depends on language model) |
| **License** | Apache 2.0 |
| **Languages** | 80+ languages |

**Pros**:
- Best open-source accuracy
- Excellent for Chinese/Japanese/Korean
- Table recognition (PP-StructureV3)
- Active development by Baidu

**Cons**:
- Heavier dependencies (PaddlePaddle framework)
- Complex installation on Windows
- GPU recommended for speed

### 2.2 EasyOCR (Recommended for Ease of Use)

| Attribute | Details |
|-----------|---------|
| **Accuracy** | 90-95% on printed text |
| **Speed** | Fast on GPU, slow on CPU |
| **Python Package** | `easyocr` |
| **Model Size** | ~90MB+ per language |
| **License** | Apache 2.0 |
| **Languages** | 80+ languages |

**Pros**:
- Simplest API (one-liner usage)
- Good out-of-the-box results
- No preprocessing needed
- PyTorch-based (familiar to ML devs)

**Cons**:
- Slow on CPU (4x slower than GPU)
- Higher memory usage
- Less accurate than PaddleOCR

### 2.3 Tesseract 5.x (Legacy, Still Viable)

| Attribute | Details |
|-----------|---------|
| **Accuracy** | 85-95% (with preprocessing), LSTM-based in v5 |
| **Speed** | Fast on CPU |
| **Python Package** | `pytesseract` |
| **Model Size** | ~40MB |
| **License** | Apache 2.0 |
| **Languages** | 116 languages |

**Pros**:
- Lightweight, CPU-friendly
- Mature, well-documented
- Smallest model size
- Best language coverage

**Cons**:
- Requires preprocessing for best results
- Outdated architecture (non-transformer)
- Struggles with complex layouts

### 2.4 docTR (Mindee)

| Attribute | Details |
|-----------|---------|
| **Accuracy** | Comparable to Google Vision/AWS Textract |
| **Speed** | Moderate (GPU recommended) |
| **Python Package** | `python-doctr` |
| **Model Size** | ~200MB |
| **License** | Apache 2.0 |
| **Languages** | Multiple (document-focused) |

**Pros**:
- Modern transformer architecture
- Part of PyTorch ecosystem
- Excellent for documents
- Layout analysis included

**Cons**:
- Requires Python 3.10+
- Heavier than Tesseract
- GPU recommended

### 2.5 Surya OCR

| Attribute | Details |
|-----------|---------|
| **Accuracy** | High on documents, 90+ languages |
| **Speed** | Fast on GPU |
| **Python Package** | `surya-ocr` |
| **Model Size** | Custom models |
| **License** | MIT (commercial OK) |
| **Languages** | 90+ languages |

**Pros**:
- Modern (2024), actively developed
- Reading order detection
- Table recognition
- Layout analysis

**Cons**:
- Document-specialized (not for photos)
- Printed text only
- Newer, less community support

---

## 3. Specialized OCR Solutions

### 3.1 Document OCR (Invoices, Receipts, Forms)

| Solution | Best For | Python Package |
|----------|----------|----------------|
| AWS Textract | Invoices, forms, tables | `amazon-textract-textractor` |
| Mindee API | Receipts, invoices | `mindee` |
| docTR | General documents | `python-doctr` |
| invoice2data | Invoice extraction | `invoice2data` |
| Veryfi | Receipts (50+ fields) | `veryfi-python` |

### 3.2 Handwriting Recognition

| Solution | Accuracy | Python Package |
|----------|----------|----------------|
| TrOCR (Microsoft) | 90-96%+ | `transformers` (HuggingFace) |
| Google Vision | 85-95% | `google-cloud-vision` |
| EasyOCR | 80-90% | `easyocr` |

**TrOCR Example**:
```python
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')

image = Image.open("handwritten.png").convert("RGB")
pixel_values = processor(images=image, return_tensors="pt").pixel_values
generated_ids = model.generate(pixel_values)
text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
```

### 3.3 Table/Structured Data Extraction

| Solution | Description | Python Package |
|----------|-------------|----------------|
| img2table | Table detection + OCR backends | `img2table` |
| Camelot | PDF table extraction | `camelot-py` |
| Tabula | PDF table extraction | `tabula-py` |
| AWS Textract Tables | Cloud table extraction | `boto3` |
| PP-StructureV3 | Part of PaddleOCR | `paddleocr` |

**img2table Example** (supports multiple OCR backends):
```python
from img2table.ocr import PaddleOCR  # or TesseractOCR, EasyOCR
from img2table.document import Image

ocr = PaddleOCR(lang="en")
doc = Image("table_image.png")
tables = doc.extract_tables(ocr=ocr, implicit_rows=True)
```

### 3.4 Multi-Language Support

| Solution | Languages | Strength |
|----------|-----------|----------|
| Tesseract | 116 | Most comprehensive |
| PaddleOCR | 80+ | Best for Asian languages |
| EasyOCR | 80+ | Good mix |
| Google Vision | 100+ | Best overall |
| Surya OCR | 90+ | Modern multilingual |

### 3.5 Real-Time/Video OCR

| Solution | FPS Capability | Notes |
|----------|----------------|-------|
| EasyOCR + GPU | 10-30 FPS | Best for real-time |
| PaddleOCR + GPU | 15-40 FPS | Fastest |
| Tesseract | 2-5 FPS | CPU only, limited |

---

## 4. Comprehensive Comparison Table

| Library/API | Type | Best For | Accuracy | Speed | Python Package | License/Cost |
|-------------|------|----------|----------|-------|----------------|--------------|
| **PaddleOCR** | Local | General, Asian langs | 95%+ | Fast (GPU) | `paddleocr` | Apache 2.0 |
| **EasyOCR** | Local | Easy integration | 90-95% | Fast (GPU) | `easyocr` | Apache 2.0 |
| **Tesseract 5** | Local | CPU-only, lightweight | 85-95% | Fast (CPU) | `pytesseract` | Apache 2.0 |
| **docTR** | Local | Documents | 95%+ | Moderate | `python-doctr` | Apache 2.0 |
| **Surya OCR** | Local | Documents, layout | 93%+ | Fast (GPU) | `surya-ocr` | MIT |
| **TrOCR** | Local | Handwriting | 90-96% | Moderate | `transformers` | MIT |
| **Google Vision** | Cloud | General, scene text | 95-99% | Fast | `google-cloud-vision` | $1.50/1000 |
| **AWS Textract** | Cloud | Documents, forms | 95-98% | Fast | `boto3` | $0.0015-0.015/page |
| **Azure Vision** | Cloud | Enterprise | 94-98% | Fast | `azure-ai-vision-imageanalysis` | Per-transaction |
| **img2table** | Local | Tables | Backend-dependent | Moderate | `img2table` | MIT |

---

## 5. Recommendations for CasareRPA Dropdown

### Recommended OCR Engines (5 Options)

| # | Engine | Reason | Implementation Complexity |
|---|--------|--------|---------------------------|
| 1 | **Tesseract** | Lightweight default, CPU-friendly, wide language support | Low |
| 2 | **EasyOCR** | Best accuracy-to-ease ratio, PyTorch-based, no preprocessing | Low |
| 3 | **PaddleOCR** | Highest accuracy local option, excellent for Asian languages | Medium |
| 4 | **Google Cloud Vision** | Industry-leading cloud accuracy, good for production | Medium |
| 5 | **AWS Textract** | Best for documents/invoices/forms/tables | Medium |

### Implementation Strategy

```python
from enum import Enum

class OCREngine(Enum):
    TESSERACT = "tesseract"      # Default, lightweight
    EASYOCR = "easyocr"          # Easy, accurate
    PADDLEOCR = "paddleocr"      # Best local accuracy
    GOOGLE_VISION = "google"     # Cloud - general
    AWS_TEXTRACT = "aws"         # Cloud - documents
```

### Required Dependencies

```toml
# pyproject.toml - Optional dependencies
[project.optional-dependencies]
ocr-tesseract = ["pytesseract>=0.3.10"]
ocr-easyocr = ["easyocr>=1.7.0"]
ocr-paddleocr = ["paddlepaddle>=2.6.0", "paddleocr>=2.7.0"]
ocr-google = ["google-cloud-vision>=3.4.0"]
ocr-aws = ["boto3>=1.34.0", "amazon-textract-textractor>=1.9.0"]
ocr-all = [
    "pytesseract>=0.3.10",
    "easyocr>=1.7.0",
    "paddlepaddle>=2.6.0",
    "paddleocr>=2.7.0",
    "google-cloud-vision>=3.4.0",
    "boto3>=1.34.0",
]
```

### Node Schema PropertyDef

```python
OCR_ENGINE_PROP = PropertyDef(
    "ocr_engine",
    PropertyType.CHOICE,
    default="tesseract",
    choices=[
        ("tesseract", "Tesseract (Default, CPU)"),
        ("easyocr", "EasyOCR (PyTorch, GPU)"),
        ("paddleocr", "PaddleOCR (Best Accuracy)"),
        ("google", "Google Cloud Vision"),
        ("aws", "AWS Textract"),
    ],
    label="OCR Engine",
    description="Select OCR engine for text extraction",
    tab="properties",
)
```

---

## 6. Additional Considerations

### Windows Compatibility

All recommended solutions work on Windows:
- **Tesseract**: Requires separate installation (tesseract-ocr-w64-setup-5.x.exe)
- **EasyOCR**: Works with pip install, GPU requires CUDA
- **PaddleOCR**: Windows wheels available, some installation complexity
- **Cloud APIs**: Work anywhere with internet

### GPU Acceleration

| Engine | GPU Support | Speedup |
|--------|-------------|---------|
| Tesseract | No | N/A |
| EasyOCR | CUDA | 4-7x |
| PaddleOCR | CUDA | 3-5x |
| docTR | CUDA | 3-4x |

### Memory Requirements

| Engine | RAM (Min) | VRAM (GPU) |
|--------|-----------|------------|
| Tesseract | 500MB | N/A |
| EasyOCR | 2GB | 2-4GB |
| PaddleOCR | 2GB | 2-4GB |
| docTR | 2GB | 2-4GB |

---

## 7. Sources

### Local OCR Libraries
- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)
- [EasyOCR GitHub](https://github.com/JaidedAI/EasyOCR)
- [docTR GitHub](https://github.com/mindee/doctr)
- [Surya OCR GitHub](https://github.com/datalab-to/surya)
- [TrOCR on HuggingFace](https://huggingface.co/docs/transformers/model_doc/trocr)
- [img2table GitHub](https://github.com/xavctn/img2table)

### Cloud OCR APIs
- [Google Cloud Vision Pricing](https://cloud.google.com/vision/pricing)
- [AWS Textract Pricing](https://aws.amazon.com/textract/pricing/)
- [Azure Computer Vision Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/computer-vision/)
- [Amazon Textract Python SDK](https://pypi.org/project/amazon-textract-textractor/)

### Benchmarks and Comparisons
- [OCR Comparison - Plugger.ai](https://www.plugger.ai/blog/comparison-of-paddle-ocr-easyocr-kerasocr-and-tesseract-ocr)
- [8 Top Open-Source OCR Models - Modal Blog](https://modal.com/blog/8-top-open-source-ocr-models-compared)
- [Tesseract vs EasyOCR - Roboflow](https://roboflow.com/compare/tesseract-vs-easyocr)
- [EasyOCR vs Tesseract vs Textract - Francesco Pochetti](https://francescopochetti.com/easyocr-vs-tesseract-vs-amazon-textract-an-ocr-engine-comparison/)
- [Best Tesseract Alternatives - Klippa](https://www.klippa.com/en/blog/information/the-best-alternative-to-tesseract/)

---

## 8. Conclusion

For CasareRPA, the recommended approach is:

1. **Default Engine**: Tesseract (lightweight, no extra dependencies)
2. **Upgrade Path**: EasyOCR for better accuracy with minimal complexity
3. **Power User**: PaddleOCR for best local accuracy
4. **Enterprise/Cloud**: Google Vision or AWS Textract based on use case

The dropdown should expose all 5 options with clear labels indicating trade-offs (CPU/GPU, cloud/local, accuracy).
