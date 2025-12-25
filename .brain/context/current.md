# Current Context

**Updated**: 2025-12-25 | **Branch**: feat/gemini-oauth

## Active Work
- **Focus**: Gemini Auth Refactor (remove litellm, use direct Gemini API)
- **Status**: PLANNING - Plan created, awaiting approval
- **Plan**: `.brain/plans/gemini-auth-refactor.md`
- **Summary`: Refactor AI assistant to remove litellm dependency and use Google Gemini Pro subscription via OAuth (opencode-gemini-auth pattern)

## Previous Work (Completed)
- Gemini AI Studio OAuth implementation (gemini_oauth.py, OAuth dialog UI)
- PKCE OAuth flow with automatic token refresh
- Tag-based routing for cloud-platform scope

## Code Review Fixes Applied
1. Fixed async/Qt event loop mixing - replaced `QTimer.singleShot` + `asyncio.ensure_future` with `_CallbackWaiterThread` (QThread pattern)
2. Added `@Slot()` decorator to `closeEvent`
3. Replaced `QMessageBox` with styled dialogs (`show_styled_information`, `show_styled_warning`)
4. Added HTTP status check before JSON parsing in token exchange

## Files Changed
- `src/casare_rpa/infrastructure/security/gemini_oauth.py` - OAuth manager for Gemini AI Studio
- `src/casare_rpa/presentation/canvas/ui/dialogs/gemini_studio_oauth_dialog.py` - OAuth dialog UI (fixed per review)
- `scripts/check_http_client_usage.py` - Allow aiohttp in OAuth files

## Quick References
- **Context**: `.brain/context/current.md` (this file)
- **Patterns**: `.brain/systemPatterns.md`
- **Rules**: `.brain/projectRules.md`
- **Nodes Index**: `src/casare_rpa/nodes/_index.md`

## Recent Session Archive
- See `.brain/context/recent.md` for last 7 days
- See `.brain/context/archive/` for historical sessions

---

**Note**: This file should stay under 50 lines. Archive completed work to `recent.md` or daily archive files.
