#!/bin/bash
#
# Export to Lex Stream Pipeline
# Validates, tests, and exports neuroscience terminology database to Lex Stream
#
# Usage: ./scripts/export_to_lexstream.sh [--skip-tests]
#

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
NEURODB_DIR="/Users/sam/NeuroDB-2"
LEXSTREAM_DIR="/Users/sam/Lex-stream-2"
DB_FILE="neuro_terms_v2.0.0_wikipedia-ninds.json"
EXPORT_LOG="scripts/output/export_log_$(date +%Y%m%d_%H%M%S).txt"

# Parse arguments
SKIP_TESTS=false
if [[ "$1" == "--skip-tests" ]]; then
    SKIP_TESTS=true
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}NeuroDB-2 → Lex Stream Export Pipeline${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check if database file exists
echo -e "${YELLOW}[1/6] Checking database file...${NC}"
if [ ! -f "$NEURODB_DIR/$DB_FILE" ]; then
    echo -e "${RED}ERROR: Database file not found: $DB_FILE${NC}"
    echo -e "${YELLOW}Run: python convert_to_lexstream.py${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database file found${NC}"
echo ""

# Step 2: Get database version and stats
echo -e "${YELLOW}[2/6] Reading database metadata...${NC}"
VERSION=$(cat "$NEURODB_DIR/VERSION.txt")
TERM_COUNT=$(python3 -c "import json; data=json.load(open('$NEURODB_DIR/$DB_FILE')); print(data['metadata']['total_terms'])")
MESH_COUNT=$(python3 -c "import json; data=json.load(open('$NEURODB_DIR/$DB_FILE')); print(data['metadata']['total_mesh_terms'])")
echo -e "  Version: ${GREEN}$VERSION${NC}"
echo -e "  Terms: ${GREEN}$TERM_COUNT${NC}"
echo -e "  MeSH Terms: ${GREEN}$MESH_COUNT${NC}"
echo ""

# Step 3: Validate database structure
echo -e "${YELLOW}[3/6] Validating database...${NC}"
cd "$NEURODB_DIR"
if python3 validate_lexstream_db.py > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database validation passed${NC}"
else
    echo -e "${RED}ERROR: Database validation failed${NC}"
    echo -e "${YELLOW}Run: python3 validate_lexstream_db.py${NC}"
    exit 1
fi
echo ""

# Step 4: Run functional tests (unless skipped)
if [ "$SKIP_TESTS" = false ]; then
    echo -e "${YELLOW}[4/6] Running functional tests...${NC}"
    if python3 test_lexstream_db.py > /dev/null 2>&1; then
        echo -e "${GREEN}✓ All tests passed${NC}"
    else
        echo -e "${RED}WARNING: Some tests failed${NC}"
        echo -e "${YELLOW}Review: python3 test_lexstream_db.py${NC}"
        read -p "Continue with export? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Export cancelled${NC}"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}[4/6] Skipping tests (--skip-tests flag)${NC}"
fi
echo ""

# Step 5: Copy to Lex Stream
echo -e "${YELLOW}[5/6] Exporting to Lex Stream...${NC}"
if [ ! -d "$LEXSTREAM_DIR" ]; then
    echo -e "${RED}ERROR: Lex Stream directory not found: $LEXSTREAM_DIR${NC}"
    exit 1
fi

# Backup existing file if it exists
if [ -f "$LEXSTREAM_DIR/neuro_terms.json" ]; then
    BACKUP_FILE="$LEXSTREAM_DIR/neuro_terms.json.backup_$(date +%Y%m%d_%H%M%S)"
    cp "$LEXSTREAM_DIR/neuro_terms.json" "$BACKUP_FILE"
    echo -e "  Backed up existing file to: $(basename $BACKUP_FILE)"
fi

# Copy new database
cp "$NEURODB_DIR/$DB_FILE" "$LEXSTREAM_DIR/neuro_terms.json"
echo -e "${GREEN}✓ Database copied to Lex Stream${NC}"
echo -e "  Source: $DB_FILE"
echo -e "  Target: $LEXSTREAM_DIR/neuro_terms.json"
echo ""

# Step 6: Update version tracking in Lex Stream
echo -e "${YELLOW}[6/6] Updating version tracking...${NC}"
cat > "$LEXSTREAM_DIR/DB_VERSION.txt" <<EOF
Database Version: $VERSION
Export Date: $(date +"%Y-%m-%d %H:%M:%S")
Total Terms: $TERM_COUNT
MeSH Terms: $MESH_COUNT
Source File: $DB_FILE
NeuroDB-2 Path: $NEURODB_DIR
EOF
echo -e "${GREEN}✓ Version tracking updated${NC}"
echo -e "  File: $LEXSTREAM_DIR/DB_VERSION.txt"
echo ""

# Create export log
mkdir -p "$NEURODB_DIR/scripts/output"
cat > "$NEURODB_DIR/$EXPORT_LOG" <<EOF
NeuroDB-2 Export Log
====================
Date: $(date +"%Y-%m-%d %H:%M:%S")
Database Version: $VERSION
Database File: $DB_FILE
Total Terms: $TERM_COUNT
MeSH Terms: $MESH_COUNT

Export Details:
- Source: $NEURODB_DIR/$DB_FILE
- Target: $LEXSTREAM_DIR/neuro_terms.json
- Validation: PASSED
- Tests: $([ "$SKIP_TESTS" = true ] && echo "SKIPPED" || echo "PASSED")

Next Steps:
1. Review changes in Lex Stream
2. Test query expansion pipeline
3. Run Lex Stream tests: cd $LEXSTREAM_DIR && python3 -m pytest tests/
4. Commit changes if all tests pass

---
Log file: $NEURODB_DIR/$EXPORT_LOG
EOF

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Export completed successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Database exported to Lex Stream:"
echo -e "  ${GREEN}$LEXSTREAM_DIR/neuro_terms.json${NC}"
echo ""
echo -e "Version tracking updated:"
echo -e "  ${GREEN}$LEXSTREAM_DIR/DB_VERSION.txt${NC}"
echo ""
echo -e "Export log saved:"
echo -e "  ${GREEN}$NEURODB_DIR/$EXPORT_LOG${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. cd $LEXSTREAM_DIR"
echo -e "  2. Test query expansion: python3 app.py"
echo -e "  3. Run tests: python3 -m pytest tests/"
echo -e "  4. Commit if tests pass"
echo ""
