#!/bin/bash

# exit_plan/exit_session.sh
# Complete session exit: commit, push, shutdown, generate handoff

set -e

EXIT_PLAN_DIR="exit_plan"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "========================================="
echo "  DocAI Session Exit Script"
echo "========================================="
echo ""

# 1. Update summary (prompt user or use default)
echo "[1/6] Updating session summary..."
if [ -t 0 ]; then
    read -p "Add notes to summary? (y/n): " ADD_NOTES
    if [ "$ADD_NOTES" = "y" ]; then
        echo "Enter notes (Ctrl+D when done):"
        NOTES=$(cat)
        echo -e "\n## Session Notes\n$NOTES" >> "$EXIT_PLAN_DIR/summary.md"
    fi
fi

# 2. Git: Push existing commits first
echo ""
echo "[2/6] Pushing existing commits..."
BRANCH=$(git branch --show-current)
UNPUSHED=$(git log origin/$BRANCH..$BRANCH --oneline 2>/dev/null | wc -l || echo "0")

if [ "$UNPUSHED" -gt 0 ]; then
    echo "$UNPUSHED unpushed commit(s):"
    git log origin/$BRANCH..$BRANCH --oneline 2>/dev/null
    echo ""
    if [ -t 0 ]; then
        read -p "Push to origin/$BRANCH? (y/n): " DO_PUSH
    else
        DO_PUSH="y"
    fi
    if [ "$DO_PUSH" = "y" ]; then
        git push origin "$BRANCH" && echo "✓ Pushed" || echo "⚠ Push failed"
    fi
else
    echo "✓ No unpushed commits"
fi

# 3. Git: Commit staged changes
echo ""
echo "[3/6] Checking staged changes..."
STAGED=$(git diff --cached --name-only | wc -l)

if [ "$STAGED" -gt 0 ]; then
    echo "$STAGED file(s) staged:"
    git diff --cached --name-only
    echo ""
    if [ -t 0 ]; then
        read -p "Commit staged changes? (y/n): " DO_COMMIT_STAGED
    else
        DO_COMMIT_STAGED="y"
    fi
    if [ "$DO_COMMIT_STAGED" = "y" ]; then
        COMMIT_MSG="Session update: $(date '+%Y-%m-%d %H:%M')"
        if [ -t 0 ]; then
            read -p "Commit message [$COMMIT_MSG]: " CUSTOM_MSG
            [ -n "$CUSTOM_MSG" ] && COMMIT_MSG="$CUSTOM_MSG"
        fi
        git commit -m "$COMMIT_MSG

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
        echo "✓ Staged changes committed"
    fi
else
    echo "✓ No staged changes"
fi

# 4. Git: Stage and commit unstaged changes
echo ""
echo "[4/6] Checking unstaged changes..."
UNSTAGED=$(git status --porcelain | grep -v "^[MADRC]" | wc -l)

if [ "$UNSTAGED" -gt 0 ]; then
    echo "$UNSTAGED unstaged file(s):"
    git status --short | grep -v "^[MADRC]"
    echo ""
    if [ -t 0 ]; then
        read -p "Stage and commit all? (y/n): " DO_STAGE
    else
        DO_STAGE="y"
    fi
    if [ "$DO_STAGE" = "y" ]; then
        git add -A
        COMMIT_MSG="Session checkpoint: $(date '+%Y-%m-%d %H:%M')"
        if [ -t 0 ]; then
            read -p "Commit message [$COMMIT_MSG]: " CUSTOM_MSG
            [ -n "$CUSTOM_MSG" ] && COMMIT_MSG="$CUSTOM_MSG"
        fi
        git commit -m "$COMMIT_MSG

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
        echo "✓ All changes committed"
    fi
else
    echo "✓ No unstaged changes"
fi

# 5. Final push
echo ""
echo "[5/6] Final push..."
UNPUSHED=$(git log origin/$BRANCH..$BRANCH --oneline 2>/dev/null | wc -l || echo "0")
if [ "$UNPUSHED" -gt 0 ]; then
    if [ -t 0 ]; then
        read -p "Push all commits to origin/$BRANCH? (y/n): " DO_FINAL_PUSH
    else
        DO_FINAL_PUSH="y"
    fi
    if [ "$DO_FINAL_PUSH" = "y" ]; then
        git push origin "$BRANCH" && echo "✓ All pushed" || echo "⚠ Push failed"
    fi
else
    echo "✓ Everything pushed"
fi

# 6. Generate handoff document
echo ""
echo "[6/7] Generating handoff document..."
bash "$EXIT_PLAN_DIR/generate_handoff.sh" > /dev/null
echo "✓ Handoff generated: $EXIT_PLAN_DIR/handoff_to_claude.md"

# 7. Shutdown Docker services
echo ""
echo "[7/7] Shutting down Docker services..."
if docker compose ps -q 2>/dev/null | grep -q .; then
    if [ -t 0 ]; then
        read -p "Stop Docker services? (y/n): " DO_STOP
    else
        DO_STOP="y"
    fi

    if [ "$DO_STOP" = "y" ]; then
        docker compose down 2>/dev/null | grep -v "^WARN" || true
        echo "✓ Docker services stopped"
    else
        echo "⏭ Services left running"
    fi
else
    echo "✓ No services running"
fi

# 6. Final summary
echo ""
echo "========================================="
echo "  Session Exit Complete"
echo "========================================="
echo ""
echo "Summary:"
git log -1 --oneline 2>/dev/null && echo "" || true
echo "Handoff file: $EXIT_PLAN_DIR/handoff_to_claude.md"
echo ""
echo "To resume next session, provide Claude with:"
echo "  cat $EXIT_PLAN_DIR/handoff_to_claude.md"
echo ""
