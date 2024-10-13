FROM ollama/ollama:latest

ARG OLLAMA_URL

ENV OLLAMA_URL $OLLAMA_URL

# Ollama API Port
EXPOSE 11434

ENTRYPOINT ["/bin/ollama"]
CMD ["serve"]  