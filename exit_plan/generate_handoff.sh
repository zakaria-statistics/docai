#!/bin/bash

# exit_plan/generate_handoff.sh
# Generates a handoff markdown file for the next LLM session.

EXIT_PLAN_DIR="exit_plan"
SUMMARY_FILE="${EXIT_PLAN_DIR}/summary.md"
NEXT_STEPS_FILE="${EXIT_PLAN_DIR}/next_steps.md"
OUTPUT_FILE="${EXIT_PLAN_DIR}/handoff_to_claude.md"
ISSUES_DIR="issues"

echo "# Context Handoff for Next Session" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "**Generated**: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 1. Summary
echo "## 1. Session Summary" >> "$OUTPUT_FILE"
if [ -f "$SUMMARY_FILE" ]; then
    cat "$SUMMARY_FILE" >> "$OUTPUT_FILE"
else
    echo "No summary provided." >> "$OUTPUT_FILE"
fi
echo "" >> "$OUTPUT_FILE"

# 2. Next Steps
echo "## 2. Next Steps" >> "$OUTPUT_FILE"
if [ -f "$NEXT_STEPS_FILE" ]; then
    cat "$NEXT_STEPS_FILE" >> "$OUTPUT_FILE"
else
    echo "No next steps defined." >> "$OUTPUT_FILE"
fi
echo "" >> "$OUTPUT_FILE"

# 3. Docker Services Status
echo "## 3. Docker Services" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
docker compose ps 2>/dev/null | grep -v "^WARN" >> "$OUTPUT_FILE" || echo "Docker not running" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 4. ChromaDB Status
echo "## 4. ChromaDB Status" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
curl -s http://localhost:8000/api/v1/collections 2>/dev/null | jq -r '.[].name' >> "$OUTPUT_FILE" || echo "ChromaDB not accessible" >> "$OUTPUT_FILE"
CHUNK_COUNT=$(curl -s "http://localhost:8000/api/v1/collections/docai_documents/count" 2>/dev/null || echo "0")
echo "Total chunks indexed: $CHUNK_COUNT" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 5. Recent Issues
echo "## 5. Recent Issues Encountered" >> "$OUTPUT_FILE"
if [ -d "$ISSUES_DIR" ] && [ "$(ls -A $ISSUES_DIR 2>/dev/null)" ]; then
    echo '```' >> "$OUTPUT_FILE"
    ls -1 "$ISSUES_DIR"/*.md 2>/dev/null | tail -5 | while read f; do
        echo "- $(basename "$f")"
    done >> "$OUTPUT_FILE"
    echo '```' >> "$OUTPUT_FILE"
else
    echo "No issues logged." >> "$OUTPUT_FILE"
fi
echo "" >> "$OUTPUT_FILE"

# 6. Git Status
echo "## 6. Git Status" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
git status --short 2>/dev/null >> "$OUTPUT_FILE" || echo "Not a git repo" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 7. Recent Commits
echo "## 7. Recent Commits" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
git log -n 5 --oneline 2>/dev/null >> "$OUTPUT_FILE" || echo "No commits" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 8. Key Files Modified
echo "## 8. Recently Modified Files" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
find . -name "*.py" -o -name "*.yml" -o -name "*.md" 2>/dev/null | xargs ls -lt 2>/dev/null | head -10 | awk '{print $NF}' >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"

echo ""
echo "========================================="
echo "Handoff file generated: $OUTPUT_FILE"
echo "========================================="
echo ""
echo "Copy this to start your next Claude session:"
echo "cat $OUTPUT_FILE | pbcopy  # macOS"
echo "cat $OUTPUT_FILE | xclip   # Linux"
