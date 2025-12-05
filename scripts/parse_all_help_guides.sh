#!/bin/bash
# Parse all camera help guide PDFs

echo 'Starting parsing of all 24 camera models...'
echo ''

for model_dir in data/help-guides/*/raw/*.pdf; do
  model=$(basename $(dirname $(dirname "$model_dir")))
  pdf_path="data/help-guides/$model/raw/${model}_helpguide.pdf"
  output_path="data/help-guides/$model/parsed/hierarchical_chunks.json"
  
  # Get URL from html-source.md (simplified - we'll pass empty URL for now)
  url=""
  
  if [ -f "$pdf_path" ]; then
    echo "Parsing $model..."
    python -m src.parsing.help_guide_pdf_parser \
      --pdf "$pdf_path" \
      --model "$model" \
      --url "$url" \
      --output "$output_path" 2>&1 | grep -E "^✓|^Error" || true
  fi
done

echo ''
echo 'Parsing complete!'
echo "Total parsed chunks:"
find data/help-guides/*/parsed/hierarchical_chunks.json -type f 2>/dev/null | wc -l
