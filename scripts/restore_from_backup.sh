#!/bin/bash
# Restore from Week 1 Migration Backup
# Created: 2025-08-18T17:11:30.560224

echo "🔄 Restoring from backup: backups\week1_migration_20250818_171130"

# Restore original files
cp "backups\week1_migration_20250818_171130/UI/app.py" "UI/app.py"
cp "backups\week1_migration_20250818_171130/requirements.txt" "requirements.txt" 2>/dev/null || echo "⚠️  requirements.txt not in backup"
cp "backups\week1_migration_20250818_171130/.env" ".env" 2>/dev/null || echo "⚠️  .env not in backup"
cp "backups\week1_migration_20250818_171130/.env.testing" ".env.testing" 2>/dev/null || echo "⚠️  .env.testing not in backup"

echo "✅ Files restored from backup"
echo "⚠️  Note: This will restore your original app.py"
echo "   The refactored services will remain in place"
echo "   You can re-run the migration later if needed"
