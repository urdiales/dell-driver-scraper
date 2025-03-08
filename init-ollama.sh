#!/bin/bash

# Pull the Llama3 model to Ollama
docker exec -it ollama ollama pull llama3

echo "Llama3 model has been downloaded to Ollama."
echo "You can now use the Dell Driver Scraper with Ollama integration."