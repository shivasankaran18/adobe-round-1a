from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
import tempfile
import sys
from pathlib import Path

# Add parent directory to path to import modules
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

try:
    from main import extract_pdf_lines_cleaned_and_merged
    from outline_hierarchy import load_blocks, get_font_sizes, find_headings, extract_title_from_page1
    
    def build_outline_hierarchy(extracted_data):
        try:
            blocks = load_blocks(extracted_data)
            if not blocks:
                return {"title": "", "outline": []}
            
            font_sizes = get_font_sizes(blocks)
            outline = find_headings(blocks, font_sizes, max_level=4)
            title = extract_title_from_page1(extracted_data)
            return {"title": title, "outline": outline}
        except Exception as e:
            return {"error": f"Hierarchy processing failed: {str(e)}"}
            
    print(" Successfully imported PDF processing modules")
    
except ImportError as e:
    print(f" Warning: Could not import processing modules: {e}")
    def extract_pdf_lines_cleaned_and_merged(pdf_path):
        return {"error": "PDF processing module not available", "file": pdf_path}
    
    def build_outline_hierarchy(data):
        return {"error": "Hierarchy processing module not available"}

app = FastAPI(title="PDF Processing API", description="Upload PDF files and get structured JSON output")

templates = Jinja2Templates(directory="templates")

os.makedirs("templates", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("upload_clean.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    
    if not file.filename.lower().endswith('.pdf'):
        return templates.TemplateResponse("result_clean.html", {
            "request": request,
            "error": "Please upload a PDF file",
            "filename": file.filename
        })
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        print(f" Processing PDF: {file.filename}")
        
        extracted_data = extract_pdf_lines_cleaned_and_merged(temp_file_path)
        
        if isinstance(extracted_data, dict) and "error" in extracted_data:
            raise Exception(extracted_data["error"])
        
        print(f" Extracted {len(extracted_data)} pages")
        
        try:
            hierarchy_data = build_outline_hierarchy(extracted_data)
            print(f" Built hierarchy: {len(hierarchy_data.get('outline', []))} items")
            print(f" Hierarchy data: {hierarchy_data}")
        except Exception as e:
            print(f" Hierarchy error: {e}")
            hierarchy_data = {"error": f"Hierarchy processing failed: {str(e)}"}
        
        os.unlink(temp_file_path)
        
        result_data = {
            "filename": file.filename,
            "title": hierarchy_data.get("title", ""),
            "outline": hierarchy_data.get("outline", []),
            "status": "success",
            "pages_processed": len(extracted_data),
            "total_hierarchy_items": len(hierarchy_data.get("outline", [])) if hierarchy_data.get("outline") else 0
        }
        
        if hierarchy_data.get("error"):
            result_data["error"] = hierarchy_data["error"]
            result_data["raw_extracted_data"] = extracted_data
        
        print(f"Final result data keys: {list(result_data.keys())}")
        
        return templates.TemplateResponse("result_clean.html", {
            "request": request,
            "result": result_data,
            "filename": file.filename,
            "json_data": json.dumps(result_data, indent=2, ensure_ascii=False)
        })
        
    except Exception as e:
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        print(f"Error processing {file.filename}: {e}")
        return templates.TemplateResponse("result_clean.html", {
            "request": request,
            "error": f"Error processing file: {str(e)}",
            "filename": file.filename
        })

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "PDF Processing API is running"}

@app.post("/api/process", response_class=JSONResponse)
async def api_process_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse(
            status_code=400,
            content={"error": "Please upload a PDF file", "filename": file.filename}
        )

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        extracted_data = extract_pdf_lines_cleaned_and_merged(temp_file_path)

        if isinstance(extracted_data, dict) and "error" in extracted_data:
            os.unlink(temp_file_path)
            return JSONResponse(
                status_code=500,
                content={"error": extracted_data["error"], "filename": file.filename}
            )

        try:
            hierarchy_data = build_outline_hierarchy(extracted_data)
        except Exception as e:
            hierarchy_data = {"error": f"Hierarchy processing failed: {str(e)}"}

        os.unlink(temp_file_path)

        result_data = {
            "filename": file.filename,
            "title": hierarchy_data.get("title", ""),
            "outline": hierarchy_data.get("outline", []),
            "status": "success",
            "pages_processed": len(extracted_data),
            "total_hierarchy_items": len(hierarchy_data.get("outline", [])) if hierarchy_data.get("outline") else 0
        }
        
        if hierarchy_data.get("error"):
            result_data["error"] = hierarchy_data["error"]

        return JSONResponse(content=result_data)

    except Exception as e:
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass

        return JSONResponse(
            status_code=500,
            content={"error": f"Error processing file: {str(e)}", "filename": file.filename}
        )
