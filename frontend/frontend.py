from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
import tempfile
import sys
from pathlib import Path
from typing import List
from datetime import datetime

parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

try:
    from main import extract_pdf_lines_cleaned_and_merged
    from outline_hierarchy import load_blocks, get_font_sizes, find_headings, extract_title_from_page1

    def build_outline_hierarchy(data):
        try:
            blocks = load_blocks(data)
            if not blocks:
                return {"title": "", "outline": []}
            font_sizes = get_font_sizes(blocks)
            outline = find_headings(blocks, font_sizes, max_level=4)
            title = extract_title_from_page1(data)
            return {"title": title, "outline": outline}
        except Exception as e:
            return {"error": f"Hierarchy processing failed: {str(e)}"}

except ImportError as e:
    def extract_pdf_lines_cleaned_and_merged(pdf_path):
        return {"error": "PDF processing module not available", "file": pdf_path}

    def build_outline_hierarchy(data):
        return {"error": "Hierarchy processing module not available"}

def process_multiple_pdfs(files, persona_role, job_to_be_done):
    """Process multiple PDFs and extract relevant sections based on the job to be done"""
    results = {
        "metadata": {
            "input_documents": [f.filename for f in files],
            "persona": persona_role,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.now().isoformat()
        },
        "documents_processed": [],
        "extracted_sections": [],
        "summary": {
            "total_documents": len(files),
            "total_pages": 0,
            "total_sections": 0
        }
    }
    
    importance_rank = 1
    temp_files = []
    
    try:
        for file in files:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                content = file.file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
                temp_files.append(temp_file_path)
            
            # Process the PDF
            try:
                extracted_data = extract_pdf_lines_cleaned_and_merged(temp_file_path)
                
                if isinstance(extracted_data, dict) and "error" in extracted_data:
                    results["documents_processed"].append({
                        "filename": file.filename,
                        "status": "error",
                        "error": extracted_data["error"]
                    })
                    continue
                
                # Build hierarchy
                hierarchy_data = build_outline_hierarchy(extracted_data)
                
                # Count pages and extract relevant sections
                total_pages = len(extracted_data) if extracted_data else 0
                results["summary"]["total_pages"] += total_pages
                
                # Extract sections based on keywords related to the job
                job_keywords = job_to_be_done.lower().split()
                relevant_sections = []
                
                for page in extracted_data:
                    page_num = page.get("page_number", 0)
                    for line in page.get("content", []):
                        text = line.get("text", "").lower()
                        # Check if line contains job-related keywords and looks like a heading
                        if (any(keyword in text for keyword in job_keywords) and 
                            (line.get("bold", False) or line.get("font_size", 0) > 12)):
                            relevant_sections.append({
                                "document": file.filename,
                                "section_title": line.get("text", ""),
                                "importance_rank": importance_rank,
                                "page_number": page_num,
                                "font_size": line.get("font_size"),
                                "is_bold": line.get("bold", False)
                            })
                            importance_rank += 1
                
                results["documents_processed"].append({
                    "filename": file.filename,
                    "status": "success",
                    "pages": total_pages,
                    "sections_found": len(relevant_sections),
                    "hierarchy": hierarchy_data
                })
                
                results["extracted_sections"].extend(relevant_sections)
                
            except Exception as e:
                results["documents_processed"].append({
                    "filename": file.filename,
                    "status": "error",
                    "error": str(e)
                })
    
    finally:
        # Clean up temporary files
        for temp_file_path in temp_files:
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    results["summary"]["total_sections"] = len(results["extracted_sections"])
    return results

app = FastAPI(title="PDF Processing API", description="Upload PDF files and get structured JSON output")

templates = Jinja2Templates(directory="templates")

os.makedirs("templates", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    """Display the single file upload form"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/multiple", response_class=HTMLResponse)
async def upload_multiple_form(request: Request):
    return templates.TemplateResponse("upload_multiple.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        return templates.TemplateResponse("result_simple.html", {
            "request": request,
            "error": "Please upload a PDF file",
            "filename": file.filename
        })

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        extracted_data = extract_pdf_lines_cleaned_and_merged(temp_file_path)

        if isinstance(extracted_data, dict) and "error" in extracted_data:
            raise Exception(extracted_data["error"])

        try:
            hierarchy_data = build_outline_hierarchy(extracted_data)
        except Exception as e:
            hierarchy_data = {"error": f"Hierarchy processing failed: {str(e)}"}

        os.unlink(temp_file_path)

        result_data = {
            "filename": file.filename,
            "extracted_lines": extracted_data,
            "hierarchy": hierarchy_data,
            "status": "success"
        }

        return templates.TemplateResponse("result_simple.html", {
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

        return templates.TemplateResponse("result_simple.html", {
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

        return JSONResponse(content={
            "filename": file.filename,
            "extracted_lines": extracted_data,
            "hierarchy": hierarchy_data,
            "status": "success"
        })

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

@app.post("/api/process-multiple", response_class=JSONResponse)
async def api_process_multiple_pdfs(
    files: List[UploadFile] = File(...),
    persona_role: str = Form(...),
    job_to_be_done: str = Form(...)
):
    """API endpoint to process multiple PDFs with a specific job/question"""
    
    # Validate that all files are PDFs
    non_pdf_files = [f.filename for f in files if not f.filename.lower().endswith('.pdf')]
    if non_pdf_files:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Non-PDF files detected: {', '.join(non_pdf_files)}",
                "message": "Please upload only PDF files"
            }
        )
    
    if len(files) == 0:
        return JSONResponse(
            status_code=400,
            content={"error": "No files provided", "message": "Please upload at least one PDF file"}
        )
    
    try:
        result = process_multiple_pdfs(files, persona_role, job_to_be_done)
        return JSONResponse(content=result)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Error processing files: {str(e)}",
                "files": [f.filename for f in files]
            }
        )

@app.post("/process-multiple", response_class=HTMLResponse)
async def web_process_multiple_pdfs(
    request: Request,
    files: List[UploadFile] = File(...),
    persona_role: str = Form(...),
    job_to_be_done: str = Form(...)
):
    """Web interface endpoint to process multiple PDFs"""
    
    # Validate that all files are PDFs
    non_pdf_files = [f.filename for f in files if not f.filename.lower().endswith('.pdf')]
    if non_pdf_files:
        return templates.TemplateResponse("result_simple.html", {
            "request": request,
            "error": f"Non-PDF files detected: {', '.join(non_pdf_files)}. Please upload only PDF files.",
            "filename": "Multiple files"
        })
    
    if len(files) == 0:
        return templates.TemplateResponse("result_simple.html", {
            "request": request,
            "error": "No files provided. Please upload at least one PDF file.",
            "filename": "No files"
        })
    
    try:
        result = process_multiple_pdfs(files, persona_role, job_to_be_done)
        
        return templates.TemplateResponse("result_simple.html", {
            "request": request,
            "result": result,
            "filename": f"Multiple files ({len(files)} PDFs)",
            "json_data": json.dumps(result, indent=2, ensure_ascii=False)
        })
        
    except Exception as e:
        return templates.TemplateResponse("result_simple.html", {
            "request": request,
            "error": f"Error processing files: {str(e)}",
            "filename": f"Multiple files ({len(files)} PDFs)"
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

