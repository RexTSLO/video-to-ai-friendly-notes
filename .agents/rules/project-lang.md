---
trigger: always_on
glob: "*"
description: Project language convention - only README.zh-TW.md uses Chinese; all other files use English.
---

# Project Language Convention

To keep the codebase consistent and standardized:
- **README.zh-TW.md**: This is the ONLY file in the repository permitted to contain Chinese text.
- **All Other Files**: All other files in the repository MUST be written in English. This applies to:
  - CLI argument help strings and group descriptions.
  - Source code comments, docstrings, and print/log statements.
  - Test names, test documentation, and test assertions (excluding test inputs representing mock Chinese subtitles/transcriptions).
  - Other documentation files, including `README.md`.
