@echo off
setlocal
set "QDRANT_LOCAL_PATH=C:/Users/Rau/Desktop/CasareRPA/.qdrant"
set "COLLECTION_NAME=casare_codebase"
set "EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2"
C:\Users\Rau\.local\bin\uvx.exe mcp-server-qdrant %*
