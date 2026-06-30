# APG Property Posting Automation - Development Prompt for Codex

## Project Overview
Build an automated system for Alpha Premiere Group (APG) to streamline the posting of property listings to Facebook. The system should replace the current manual workflow that takes 15-20 minutes per property with an automated process taking under 2 minutes.

## Current Manual Workflow (To Be Automated)
1. Find property in APG Listing Drive: https://drive.google.com/drive/folders/1GXeGULYswb7jXcMGCCRm2RQ_h0EKsDll
2. Property names are assigned by supervisor (Ma'am Jean)
3. Each property folder contains: minimum 3 images + 1 document with "caption deets" (minimal property info)
4. Use AI to generate Facebook captions with strict rules:
   - NO emojis
   - AVOID words: "least term", "negotiables"
   - Professional, informative tone
5. Post to Facebook and copy the post URL
6. Update Posting Tracker Sheet: https://docs.google.com/spreadsheets/d/1xzzuq8KHbzrRIGMyIo0AQVgq0LQklDkW8-S9Y__7RvM/edit?gid=291244162#gid=291244162
7. Update Daily Progress Report: https://docs.google.com/document/d/1mctXkKFhZLCEXQtnzO4dmHhUSGOKFdFliF_qL17U68o/edit?tab=t.1itn1x8u6h9x

## System Requirements

### Functional Requirements
1. **Property Queue Management**
   - Accept a list of property names (CSV, Google Sheet, or manual input)
   - Search and locate property folders in Google Drive
   - Validate each folder has ≥3 images and 1 caption document
   - Queue validated properties for processing
   - Log errors for incomplete/missing properties

2. **Content Extraction**
   - Download minimum 3 images from each property folder
   - Extract text from caption details document (support PDF, DOCX, TXT formats)
   - Validate image formats (JPG, PNG) and reasonable file sizes
   - Create content bundle: {property_id, images[], caption_details}

3. **AI Caption Generation**
   - Use Claude API or OpenAI API for caption generation
   - Apply strict content rules:
     * Remove all emojis
     * Detect and avoid phrases: "least term", "negotiables"
     * Generate professional, informative captions
   - Validate generated caption against rules
   - Retry if rules violated
   - Fallback to manual review if generation fails after 3 attempts

4. **Facebook Posting**
   - Post images (3+) with generated caption to Facebook Page
   - Use Facebook Graph API
   - Support photo carousel/album format
   - Capture and return post URL and post ID
   - Handle API errors with retry logic (3 attempts)

5. **Tracking Updates**
   - Update Google Sheets (Posting Tracker):
     * Columns: Date, Property Name, Post URL, Status, Posted By
     * Append new row for each successful post
   - Update Google Docs (Daily Progress Report):
     * Append formatted entry with date, property name, and post link
     * Format: "• [Property Name] - Posted at [time]\n  Link: [post_url]"

6. **Error Handling & Logging**
   - Log all operations with timestamps
   - Handle errors gracefully:
     * Property not found → Log, notify, skip
     * Insufficient images → Log, request more content
     * Caption generation fails → Retry, then manual fallback
     * Facebook API error → Retry 3x, queue for manual posting
     * Tracking update fails → Store locally, retry next run
   - Generate daily summary report with success/error counts

### Non-Functional Requirements
1. **Performance**
   - Process time: <2 minutes per property
   - Support batch processing: 20-30 properties per day
   - Concurrent processing where possible

2. **Reliability**
   - Target success rate: 95%+
   - Error rate: <5%
   - Automatic retry for transient failures

3. **Security**
   - Store API keys/tokens in environment variables
   - Use OAuth 2.0 for Google services
   - Facebook App token for posting
   - Never commit credentials to repository

4. **Maintainability**
   - Clean, documented code
   - Modular architecture
   - Configuration file for settings
   - Easy to update caption rules

## Technical Stack Recommendations

### Backend: Python
```
Required Libraries:
- google-api-python-client (Google Drive, Sheets, Docs)
- google-auth-oauthlib (Authentication)
- facebook-sdk (Facebook Graph API)
- anthropic or openai (AI caption generation)
- python-dotenv (Environment variables)
- Pillow (Image processing)
- python-docx (DOCX parsing)
- PyPDF2 (PDF parsing)
- requests (HTTP requests)
- pandas (Data manipulation)
```

### APIs Required
1. **Google Drive API** - Read property folders, download files
2. **Google Sheets API** - Update posting tracker
3. **Google Docs API** - Append to daily report
4. **Facebook Graph API** - Post to Facebook Page
   - Required permissions: `manage_pages`, `publish_pages`
5. **Claude API** or **OpenAI API** - Caption generation

## System Architecture

```
src/
├── main.py                 # Entry point, orchestration
├── config.py              # Configuration management
├── .env.example           # Environment variables template
├── modules/
│   ├── google_drive.py    # Google Drive operations
│   ├── content_extractor.py  # Download and extract content
│   ├── caption_generator.py  # AI caption generation
│   ├── facebook_poster.py    # Facebook posting
│   ├── tracker_updater.py    # Update Google Sheets/Docs
│   └── queue_manager.py      # Property queue management
├── utils/
│   ├── logger.py          # Logging setup
│   ├── validators.py      # Input validation
│   └── error_handler.py   # Error handling utilities
├── tests/
│   └── test_*.py          # Unit tests
└── logs/
    └── automation.log     # Log files
```

## Configuration File Example (config.yaml)

```yaml
google_drive:
  listings_folder_id: "1GXeGULYswb7jXcMGCCRm2RQ_h0EKsDll"
  
facebook:
  page_id: "YOUR_PAGE_ID"
  
caption_rules:
  no_emojis: true
  forbidden_phrases:
    - "least term"
    - "negotiables"
  style: "professional, informative"
  max_length: 2000
  
tracking:
  posting_tracker_sheet_id: "1xzzuq8KHbzrRIGMyIo0AQVgq0LQklDkW8-S9Y__7RvM"
  posting_tracker_gid: "291244162"
  daily_report_doc_id: "1mctXkKFhZLCEXQtnzO4dmHhUSGOKFdFliF_qL17U68o"
  
processing:
  min_images: 3
  max_retries: 3
  batch_size: 5
  concurrent_tasks: 3
```

## Environment Variables (.env)

```
# Google API
GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json

# Facebook API
FACEBOOK_ACCESS_TOKEN=your_facebook_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id

# AI API (choose one)
ANTHROPIC_API_KEY=your_anthropic_key
# OR
OPENAI_API_KEY=your_openai_key

# Tracking
POSTING_TRACKER_SHEET_ID=1xzzuq8KHbzrRIGMyIo0AQVgq0LQklDkW8-S9Y__7RvM
DAILY_REPORT_DOC_ID=1mctXkKFhZLCEXQtnzO4dmHhUSGOKFdFliF_qL17U68o
```

## Implementation Priority

### Phase 1: Core Pipeline (Week 1)
1. Set up project structure
2. Implement Google Drive connection and file listing
3. Implement content extraction (images + documents)
4. Create basic logging and error handling

### Phase 2: AI & Posting (Week 2)
5. Implement AI caption generation with rule validation
6. Implement Facebook posting functionality
7. Add retry logic and error handling

### Phase 3: Tracking & Integration (Week 3)
8. Implement Google Sheets update
9. Implement Google Docs update
10. Create queue management system
11. Add batch processing support

### Phase 4: Testing & Refinement (Week 4)
12. Write unit tests
13. End-to-end testing with real data
14. Performance optimization
15. Documentation and deployment guide

## Key Implementation Details

### Caption Generation Prompt Template
```python
caption_prompt = f"""
Create a professional Facebook post caption for this property listing.

Property Details:
{caption_details}

Requirements:
- Professional and informative tone
- NO emojis whatsoever
- DO NOT use phrases: "least term", "negotiables"
- Highlight key features and selling points
- Include relevant property details (location, size, price if mentioned)
- Keep it concise but compelling (under 2000 characters)

Generate the caption now:
"""
```

### Caption Validation Function
```python
def validate_caption(caption: str) -> tuple[bool, list[str]]:
    """
    Validate generated caption against rules.
    Returns (is_valid, list_of_violations)
    """
    violations = []
    
    # Check for emojis
    if contains_emojis(caption):
        violations.append("Contains emojis")
    
    # Check for forbidden phrases
    forbidden = ["least term", "negotiables"]
    for phrase in forbidden:
        if phrase.lower() in caption.lower():
            violations.append(f"Contains forbidden phrase: '{phrase}'")
    
    return len(violations) == 0, violations
```

### Facebook Posting Function Signature
```python
def post_to_facebook(
    page_id: str,
    access_token: str,
    images: list[str],  # Local file paths
    caption: str
) -> dict:
    """
    Post images with caption to Facebook Page.
    Returns: {
        'success': bool,
        'post_id': str,
        'post_url': str,
        'error': str (if failed)
    }
    """
```

## Success Criteria
- [ ] System can process 20-30 properties per day
- [ ] Average processing time <2 minutes per property
- [ ] Caption generation success rate >95%
- [ ] All tracking updates occur automatically
- [ ] Error logging and reporting functional
- [ ] No hardcoded credentials
- [ ] Comprehensive error handling
- [ ] Unit test coverage >80%

## Testing Checklist
- [ ] Test with property folders having exactly 3 images
- [ ] Test with property folders having >3 images
- [ ] Test error handling for <3 images
- [ ] Test caption generation with various property details
- [ ] Test caption validation (emoji detection, forbidden phrases)
- [ ] Test Facebook posting with single and multiple images
- [ ] Test Google Sheets update
- [ ] Test Google Docs update
- [ ] Test batch processing
- [ ] Test error recovery and retry logic

## Deliverables
1. Source code in GitHub repository
2. README.md with setup instructions
3. requirements.txt with all dependencies
4. .env.example template
5. config.yaml example
6. User documentation
7. API authentication setup guide
8. Deployment guide

## Questions to Clarify Before Starting
1. Which Facebook Page should posts go to? (Need Page ID)
2. Who will provide the list of assigned property names? (Format: CSV, Google Sheet, manual?)
3. Should the system run on a schedule or be triggered manually?
4. Preferred AI service: Claude (Anthropic) or OpenAI?
5. Should there be a review/approval step before posting, or fully automated?
6. What timezone for timestamps in tracking?
7. Should failed posts be retried automatically or require manual intervention?

## Budget Estimate
**Time:** 3-4 weeks for complete implementation and testing
**Cost:**
- Claude API: ~$0.01-0.05 per caption (depending on length)
- OpenAI API: ~$0.02-0.08 per caption
- Monthly estimate (600 properties): $6-48/month for AI captions
- Google/Facebook APIs: Free within quota limits

---

## Additional Notes
- Start with a simple prototype to validate the approach
- Run parallel with manual process for first 2 weeks
- Monitor caption quality and adjust prompts as needed
- Gather feedback from Ma'am Jean and team
- Iterate based on real-world usage

## Support & Maintenance
- Weekly review of error logs
- Monthly caption quality review
- Quarterly system optimization
- Update API integrations as needed