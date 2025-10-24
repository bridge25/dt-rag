# dt-rag Repository Migration Guide

## 🔗 Previous Repository
This project was migrated from the monorepo:
- **Original**: https://github.com/bridge25/Unmanned
- **Path**: `/dt-rag/`
- **Migration Date**: 2025-10-24
- **Last Shared Commit**: d389e29 (2025-10-24)

## 📜 Historical References
All commits before 2025-10-24 can be found in the original Unmanned repository.

### Key Historical Commits
| Date | Commit | Description | Reference |
|------|--------|-------------|-----------|
| 2025-09-21 | dac9a90 | Complete mypy type error resolution | [Unmanned#dac9a90](https://github.com/bridge25/Unmanned/commit/dac9a90) |
| 2025-10-24 | d389e29 | SPEC-CICD-001 Phase 2 completion | [Unmanned#d389e29](https://github.com/bridge25/Unmanned/commit/d389e29) |

## 🔍 How to Access Full History
```bash
# Clone original repository for full history
git clone https://github.com/bridge25/Unmanned.git
cd Unmanned/dt-rag

# Or add as remote to current dt-rag
git remote add unmanned-origin https://github.com/bridge25/Unmanned.git
git fetch unmanned-origin
```

## ⚠️ Why This Migration Happened
The project experienced repeated file loss due to Git repository structure mismatch:
- Git root was at `/Unmanned` but work happened in `/Unmanned/dt-rag`
- Path prefix confusion caused files to be incorrectly deleted during Git operations
- Separating into independent repository eliminates this issue permanently

## 📞 Questions?
See the original Unmanned repository for full historical context.
