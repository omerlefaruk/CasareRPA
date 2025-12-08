# Utility & Media Nodes Implementation Plan

## Overview
Implement 9 new nodes (window management already exists).

## Existing Window Nodes (Skip)
- ActivateWindowNode, GetWindowListNode, WaitForWindowNode
- ResizeWindowNode, MoveWindowNode, MaximizeWindowNode
- MinimizeWindowNode, RestoreWindowNode, GetWindowPropertiesNode, SetWindowStateNode

## Nodes to Implement

### Utility Nodes (6) → nodes/system/utility_system_nodes.py (new)
| Node | Purpose | Key Properties | Outputs |
|------|---------|----------------|---------|
| FileWatcherNode | Monitor file/folder changes | path, events (create/modify/delete), timeout | event_type, file_path, triggered |
| QRCodeNode | Generate/read QR codes | action (generate/read), data/image_path, size | image_path/data, success |
| Base64Node | Encode/decode base64 | action (encode/decode), input | output, success |
| UUIDGeneratorNode | Generate UUIDs | version (1/4), count | uuid, uuids (list) |
| AssertNode | Validate conditions | condition, message, fail_workflow | passed, message |
| LogToFileNode | Write to log file | file_path, message, level, append | success, lines_written |

### Media Nodes (3) → nodes/system/media_nodes.py (new)
| Node | Purpose | Key Properties | Outputs |
|------|---------|----------------|---------|
| TextToSpeechNode | Read text aloud | text, voice, rate, volume | success, duration |
| PDFPreviewDialogNode | Preview PDF | pdf_path, page, zoom | confirmed, page_count |
| WebcamCaptureNode | Capture from webcam | camera_id, output_path, show_preview | image_path, success |

## Dependencies
- watchdog: FileWatcher
- qrcode, pyzbar, Pillow: QRCode
- pyttsx3: TextToSpeech
- PyMuPDF (fitz): PDF preview
- opencv-python: Webcam

## File Structure
```
nodes/system/
  utility_system_nodes.py  (FileWatcher, QRCode, Base64, UUID, Assert, LogToFile)
  media_nodes.py           (TextToSpeech, PDFPreview, WebcamCapture)
```

## Registration (6 files)
1. nodes/system/__init__.py
2. nodes/__init__.py (_NODE_REGISTRY)
3. utils/workflow/workflow_loader.py (NODE_TYPE_MAP)
4. visual_nodes/system/nodes.py
5. visual_nodes/system/__init__.py
6. visual_nodes/__init__.py (_VISUAL_NODE_REGISTRY)

## Implementation Order
1. Utility nodes (simpler, fewer deps)
2. Media nodes
3. Registration
4. Quality/Review
