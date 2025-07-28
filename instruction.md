# Instructions for Evaluators
Thank you for evaluating our solution for the Adobe India Hackathon 2025.
---
## Prerequisites
- **Docker** must be installed on your system.
---

## 1. Build the Docker Image
Navigate to the project root directory (where the `Dockerfile` is located) and run:
```sh
docker build -t pdf-frontend .
```
---
## 2. Run the Docker Container
Start the container and map port 8000:
```sh
docker run -p 8000:8000 pdf-frontend
```
- The application will be accessible at: [http://localhost:8000](http://localhost:8000)
---

## 3. Using the Web Application
1. Open your browser and go to [http://localhost:8000](http://localhost:8000)
2. You will see an upload form.
3. Click **Choose File** and select a PDF to upload.
4. Click **Upload**.
5. The app will process the PDF and display the extracted structured data and outline.
6. You can view the JSON output directly on the results page.

---

Thank you for your time and evaluation! 