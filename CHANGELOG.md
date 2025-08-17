# Changelog

## [1.1.1] - 2025-08-17

### Changed
- **Agent Thinking**: Completely restructured matching logic to use thinking patterns
  - No hardcoded fuzzy matching - agent learns HOW to think about similarity
  - Added similarity scoring as a thinking concept (0-100 confidence)
  - Teaches agent about common typos (double letters, swapped letters, etc.)
  - Agent now calculates confidence in matches through thinking

### Fixed
- **Critical**: Bot no longer defaults to first item when no match found
  - Previously would update wrong adset when user made typos (e.g., "brroklyn")
  - Now returns error and asks for clarification when confidence is low
  - Prevents dangerous data integrity issues

### Added
- **Uncertainty Handling**: Agent now thinks about uncertainty
  - Never defaults without confidence
  - Asks for clarification when uncertain
  - Shows available options to user
  - Explains why it's uncertain

### Technical Philosophy
- Teaches agent HOW to think, not WHAT to think
- Uses thinking patterns for fuzzy matching, not hardcoded rules
- Agent learns concepts like edit distance and phonetic similarity
- Implements confidence thresholds through thinking (70% minimum)

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