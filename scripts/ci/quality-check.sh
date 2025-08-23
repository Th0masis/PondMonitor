#!/bin/bash
# Quality check script for linting, formatting, and type checking

set -e

# Change to project root
cd "$(dirname "$0")/../.."

echo "🔍 PondMonitor Quality Checks"
echo "============================="

# Exit codes
EXIT_CODE=0

# Check if tools are available
echo "📦 Checking required tools..."
TOOLS_MISSING=0

check_tool() {
    if ! python -c "import $1" 2>/dev/null; then
        echo "❌ $1 not found"
        TOOLS_MISSING=1
    else
        echo "✅ $1 available"
    fi
}

check_tool "flake8"
check_tool "black"
check_tool "mypy"

if [ $TOOLS_MISSING -eq 1 ]; then
    echo ""
    echo "⚠️  Install missing tools with:"
    echo "   pip install flake8 black mypy"
    if [ "$CI" = "true" ]; then
        exit 1
    fi
fi

# Python code formatting check with Black
echo ""
echo "🎨 Checking code formatting with Black..."
if python -m black --check --diff . ; then
    echo "✅ Code formatting: PASSED"
else
    echo "❌ Code formatting: FAILED"
    echo "💡 Run 'python -m black .' to fix formatting"
    EXIT_CODE=1
fi

# Linting with flake8
echo ""
echo "🔧 Running linting with flake8..."

# Critical errors that should always fail
echo "Checking critical errors..."
if python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics; then
    echo "✅ Critical errors: NONE"
else
    echo "❌ Critical errors found"
    EXIT_CODE=1
fi

# Style and complexity checks (warnings)
echo "Checking style and complexity..."
python -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics > flake8-report.txt

WARNINGS=$(cat flake8-report.txt | tail -1 | awk '{print $1}')
if [ "$WARNINGS" = "0" ]; then
    echo "✅ Style checks: PASSED (0 warnings)"
else
    echo "⚠️  Style checks: $WARNINGS warnings"
    echo "📄 Details in flake8-report.txt"
    
    # Show top issues
    echo "Top issues:"
    head -10 flake8-report.txt || true
fi

# Type checking with mypy
echo ""
echo "🔍 Running type checking with mypy..."
if python -m mypy . --ignore-missing-imports --no-error-summary > mypy-report.txt 2>&1; then
    echo "✅ Type checking: PASSED"
else
    MYPY_ERRORS=$(wc -l < mypy-report.txt)
    echo "⚠️  Type checking: $MYPY_ERRORS issues found"
    echo "📄 Details in mypy-report.txt"
    
    # Show first few errors
    echo "Sample issues:"
    head -5 mypy-report.txt || true
    
    # Don't fail on type errors in CI for now (warnings only)
    if [ "$STRICT_TYPES" = "true" ]; then
        EXIT_CODE=1
    fi
fi

# Security linting with bandit (if available)
echo ""
echo "🔒 Security linting..."
if python -c "import bandit" 2>/dev/null; then
    if python -m bandit -r . -f txt > bandit-report.txt 2>&1; then
        echo "✅ Security check: PASSED"
    else
        echo "⚠️  Security issues found"
        echo "📄 Details in bandit-report.txt"
        
        # Show summary
        grep -E "(Total lines of code|Total issues)" bandit-report.txt || true
        
        # Don't fail CI on security warnings for now
        if [ "$STRICT_SECURITY" = "true" ]; then
            EXIT_CODE=1
        fi
    fi
else
    echo "⚠️  bandit not available, skipping security check"
fi

# Import sorting check with isort (if available)
echo ""
echo "📚 Checking import sorting..."
if python -c "import isort" 2>/dev/null; then
    if python -m isort --check-only --diff .; then
        echo "✅ Import sorting: PASSED"
    else
        echo "❌ Import sorting: FAILED"
        echo "💡 Run 'python -m isort .' to fix import order"
        # Don't fail CI on import sorting for now
    fi
else
    echo "⚠️  isort not available, skipping import sort check"
fi

# Docstring check (basic)
echo ""
echo "📝 Checking basic docstring coverage..."
MISSING_DOCSTRINGS=$(python -c "
import ast
import os
missing = 0
for root, dirs, files in os.walk('.'):
    if 'venv' in root or '.git' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            try:
                with open(os.path.join(root, file), 'r') as f:
                    tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not ast.get_docstring(node):
                        if not node.name.startswith('_'):
                            missing += 1
            except:
                pass
print(missing)
")

if [ "$MISSING_DOCSTRINGS" = "0" ]; then
    echo "✅ Docstring coverage: GOOD"
else
    echo "⚠️  Missing docstrings: $MISSING_DOCSTRINGS functions/classes"
fi

# Summary
echo ""
echo "📊 Quality Check Summary"
echo "========================"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Overall: PASSED"
    echo "🎉 Code quality looks good!"
else
    echo "❌ Overall: FAILED"
    echo "🔧 Please fix the issues above"
fi

# Generate GitHub summary if in CI
if [ -n "$GITHUB_STEP_SUMMARY" ]; then
    echo "## 🔍 Quality Check Results" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ **Overall Status: PASSED**" >> $GITHUB_STEP_SUMMARY
    else
        echo "❌ **Overall Status: FAILED**" >> $GITHUB_STEP_SUMMARY
    fi
    
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "### Checks:" >> $GITHUB_STEP_SUMMARY
    echo "- Formatting: $([ $EXIT_CODE -eq 0 ] && echo '✅ Passed' || echo '❌ Issues found')" >> $GITHUB_STEP_SUMMARY
    echo "- Linting: ⚠️ $WARNINGS warnings" >> $GITHUB_STEP_SUMMARY
    echo "- Type Checking: Available in artifacts" >> $GITHUB_STEP_SUMMARY
    echo "- Security: Available in artifacts" >> $GITHUB_STEP_SUMMARY
fi

exit $EXIT_CODE