# Docker build and run instructions

## Build the image

```bash
docker build -t silicon-to-phonopy .
```

## Run the container

```bash
docker run -p 8000:8000 -p 5173:5173 silicon-to-phonopy
```

- Backend API will be available at http://localhost:8000
- Frontend will be available at http://localhost:5173

## Notes
- Ensure you have Docker installed.
- GPAW is optional and should be installed via conda if needed.
- The container builds both backend and frontend, then serves both.
