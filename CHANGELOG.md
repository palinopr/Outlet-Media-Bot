# Changelog

## [1.1.0] - 2024-01-17

### Fixed
- **Critical**: Fixed Meta API updates not actually executing on Facebook
  - Changed from `.update()` to `.api_update()` in all SDK methods
  - Budget updates now actually change values on Meta Ads Manager
  - Pause/resume operations now work correctly

- **Adset Selection**: Fixed incorrect adset being updated
  - Bot now correctly matches lowercase city names (e.g., "brooklyn")
  - Previously only matched capitalized words, causing wrong adset selection

- **Error Reporting**: Fixed false error reports for successful operations
  - LLM prompt now checks for success indicators first
  - Correctly interprets `has_errors: false` and `success: true`
  - No longer reports errors when operations succeed

### Technical Details
- SDK methods affected: `update_adset_budget`, `update_campaign_budget`, `pause_adset`, `resume_adset`, `pause_campaign`, `resume_campaign`
- All update methods now use Facebook's `api_update()` instead of `update()`
- Pattern matching improved to handle any word >2 characters, not just capitalized

## [1.0.0] - 2024-01-16

### Initial Release
- Discord bot for Meta Ads management
- LangGraph-based autonomous agent
- Support for budget updates, campaign management, and reporting