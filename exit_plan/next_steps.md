# Next Steps

## Immediate
1. Test more document types (PDF, DOCX)
2. Test query functionality: `docai query "your question"`
3. Test summarize: `docai summarize /app/test_docs/file.md`

## Optional Enhancements
- Add OCR for scanned PDFs (currently not supported)
- Add web UI frontend
- Add authentication for API
- Deploy to cloud (K8s)

## Maintenance
- Monitor `issues/` dir for recurring problems
- Update chromadb versions together (client + server)
- Check Ollama model updates: `ollama pull llama3.1:8b`
