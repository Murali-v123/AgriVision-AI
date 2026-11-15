import mimetypes
import os
from pathlib import Path
from django.http import HttpResponse, Http404

FRONTEND_ROOT = Path(__file__).resolve().parent.parent.parent

def serve_frontend(request, path=""):
    """
    Serves frontend static HTML, CSS, JS and assets for single-service deployment
    on platforms like Render.
    """
    # Normalize empty path to index.html
    clean_path = path.strip("/") if path else ""
    if not clean_path:
        clean_path = "index.html"
    
    try:
        target_path = (FRONTEND_ROOT / clean_path).resolve()
        # Security check: avoid directory traversal outside project root
        if not target_path.is_relative_to(FRONTEND_ROOT.resolve()):
            raise Http404("Invalid path")
    except (ValueError, RuntimeError):
        raise Http404("Invalid path")
    
    if target_path.is_dir():
        target_path = target_path / "index.html"
        
    if not target_path.exists() or not target_path.is_file():
        raise Http404(f"File not found: {clean_path}")
        
    content_type, encoding = mimetypes.guess_type(str(target_path))
    content_type = content_type or "application/octet-stream"
    
    # Ensure correct javascript mime type
    if str(target_path).endswith(".js"):
        content_type = "application/javascript"
    elif str(target_path).endswith(".css"):
        content_type = "text/css"
    elif str(target_path).endswith(".html"):
        content_type = "text/html"
    
    with open(target_path, "rb") as f:
        content = f.read()
        
    response = HttpResponse(content, content_type=content_type)
    if encoding:
        response["Content-Encoding"] = encoding
    return response
