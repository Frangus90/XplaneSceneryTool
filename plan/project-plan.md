# X-Plane Scenery Tool - Project Plan

## Project Summary

**Goal:** Build a Windows desktop GUI application that allows X-Plane flight simulator users to search for and download airport sceneries from the X-Plane Scenery Gateway by ICAO code.

**Target User:** End users (flight sim enthusiasts) who want a simple, time-saving tool to manage scenery downloads.

**Scope:** MVP-first approach focusing on core functionality with simple architecture suitable for a beginner's first desktop app.

## Key Requirements

1. **Search by ICAO Code:** Users can enter airport ICAO codes (e.g., "KJFK", "EGLL") to find sceneries
2. **Show Last Update:** Display when the airport scenery was last updated
3. **Airport Details View:** Click on an airport to see detailed information including:
   - Airport metadata (name, location, coordinates)
   - Scenery version history and changelog
   - Artist comments describing changes made
   - Moderator comments and approval status
   - WED version, X-Plane compatibility, features (taxi routes, 3D, etc.)
   - Recommended scenery pack
4. **Download Sceneries:** Fetch and extract scenery packages from Gateway API
5. **Auto-detect X-Plane:** Automatically locate X-Plane installation directory
6. **Batch Downloads:** Queue and download multiple sceneries
7. **Version Management:** Track installed sceneries and their versions
8. **Cross-version Support:** Detect and support both X-Plane 11 and 12 automatically

## Technology Stack Recommendation

### **Python + CustomTkinter (Recommended)**

**Rationale:**

- **Beginner-friendly:** Python has excellent learning resources and readable syntax
- **CustomTkinter:** Modern, attractive GUI library built on tkinter with native look
- **Great for MVP:** Quick development with built-in widgets for forms, lists, buttons
- **Windows-native feel:** CustomTkinter provides modern UI that doesn't look "web-like"
- **Simple packaging:** PyInstaller creates standalone .exe for distribution
- **Rich ecosystem:** `requests` for API calls, `zipfile` for extraction, built-in JSON support

**Key Libraries:**

- `customtkinter` - Modern GUI framework
- `requests` - HTTP client for Gateway API
- `tkintermapview` - Optional: future map view support
- Standard library: `zipfile`, `json`, `pathlib`, `base64`

### Alternative Considered: Electron

Rejected because: Larger bundle size, web tech overhead unnecessary for simple app, Python better for learning and file system operations.

## Architecture Overview

```
XplaneSceneryTool/
├── src/
│   ├── main.py                 # Entry point, app initialization
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py      # Main application window
│   │   ├── search_panel.py     # ICAO search interface
│   │   ├── results_panel.py    # Search results display
│   │   ├── details_panel.py    # Airport/scenery details view (NEW)
│   │   └── downloads_panel.py  # Download queue and progress
│   ├── core/
│   │   ├── __init__.py
│   │   ├── gateway_client.py   # X-Plane Gateway API client
│   │   ├── xplane_detector.py  # Detect X-Plane installation
│   │   ├── scenery_manager.py  # Install, track sceneries
│   │   └── download_queue.py   # Batch download management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── airport.py          # Airport data model
│   │   └── scenery.py          # Scenery package model
│   └── utils/
│       ├── __init__.py
│       ├── config.py            # App configuration
│       └── logger.py            # Logging setup
├── data/
│   └── installed_sceneries.json # Track installed sceneries
├── requirements.txt             # Python dependencies
├── .gitignore
├── README.md
└── LICENSE

```

## Implementation Phases

### Phase 1: Project Setup & Gateway API Client

**Files:** `requirements.txt`, `src/core/gateway_client.py`, `src/models/airport.py`, `src/models/scenery.py`

1. Initialize Python project structure
2. Create requirements.txt with dependencies
3. Implement Gateway API client:
   - `search_airport(icao: str)` - GET /apiv1/airport/[ICAO]
   - `get_scenery(scenery_id: int)` - GET /apiv1/scenery/[ID]
   - Parse JSON responses into Airport and Scenery models
   - Handle base64-encoded ZIP file decoding
4. Add error handling for API failures and rate limiting
5. Write simple test script to verify API connectivity

### Phase 2: X-Plane Detection & Scenery Installation

**Files:** `src/core/xplane_detector.py`, `src/core/scenery_manager.py`, `data/installed_sceneries.json`

1. Implement X-Plane installation detector:
   - Check common Windows locations (Program Files, Steam, etc.)
   - Read X-Plane version from `X-Plane.exe` or version file
   - Validate Custom Scenery folder exists
2. Create scenery installer:
   - Extract ZIP to correct Custom Scenery subfolder
   - Create/update scenery_packs.ini if needed
   - Track installed sceneries in JSON database
   - Verify installation success
3. Version management:
   - Store scenery metadata (ID, ICAO, version, install date)
   - Check for updates against Gateway API
   - Support uninstall/removal

### Phase 3: Basic GUI - Search & Display

**Files:** `src/main.py`, `src/gui/main_window.py`, `src/gui/search_panel.py`, `src/gui/results_panel.py`

1. Create main application window with CustomTkinter
2. Build search panel:
   - ICAO code text input (validation: 3-4 uppercase letters)
   - Search button
   - Status label for feedback
3. Implement results panel:
   - Display airport name, ICAO, location
   - **Show last update date** for the airport
   - List available scenery packs with metadata (artist, date, type)
   - Show recommended/approved scenery
   - **Make airport entries clickable** to view details
   - Download button per scenery or "Download All"
4. Wire search → API call → display results
5. Add loading indicators and error messages

### Phase 3.5: Airport Details View (NEW)

**Files:** `src/gui/details_panel.py`

1. Create details panel that displays when user clicks on an airport:
   - **Airport header:** Name, ICAO, location (lat/lon)
   - **Recommended scenery pack** highlighted at top
   - **Scenery version history:** Chronological list of all submissions
2. For each scenery version, show:
   - Scenery ID and submission date
   - **Status badge:** Approved/Declined/Pending with color coding
   - Artist name and avatar (if available)
   - WED version used
   - X-Plane compatibility version
   - **Features list:** Taxi routes, ground routes, 3D status, ATC flows
   - Download availability
   - **Artist comments:** What changes were made (expandable text)
   - **Moderator comments:** Approval/rejection reasoning (expandable text)
   - Parent version reference (iteration history)
3. UI features:
   - Back button to return to search results
   - Download button for each version
   - Scroll view for long version histories
   - Collapsible comments sections to save space

### Phase 4: Download Queue & Progress

**Files:** `src/core/download_queue.py`, `src/gui/downloads_panel.py`

1. Implement download queue system:
   - Queue multiple downloads
   - Process downloads sequentially (avoid API abuse)
   - Show progress per download
2. Create downloads panel:
   - List queued/active/completed downloads
   - Progress bars with percentage
   - Cancel/retry functionality
3. Integrate with scenery manager:
   - Auto-extract and install after download
   - Update installed sceneries database
   - Show success/failure notifications

### Phase 5: Configuration & Polish

**Files:** `src/utils/config.py`, `src/utils/logger.py`, `README.md`, `.gitignore`

1. Add configuration system:
   - Custom X-Plane path override
   - Download location preference
   - Theme selection (light/dark)
   - Save/load from JSON config file
2. Implement logging:
   - Log API calls, errors, installations
   - Help users troubleshoot issues
3. Polish UI:
   - Keyboard shortcuts (Enter to search)
   - Window icon and title
   - About dialog with version info
4. Create README with:
   - Installation instructions
   - Usage guide with screenshots
   - Troubleshooting section

### Phase 6: Packaging & Distribution

**Files:** `build.spec`, `setup.py`

1. Use PyInstaller to create standalone .exe
2. Test on clean Windows machine
3. Create simple installer or ZIP distribution
4. Add GitHub release with download link

## Critical Files to Create

1. `requirements.txt` - Dependencies
2. `src/core/gateway_client.py` - API integration (core functionality)
3. `src/core/xplane_detector.py` - X-Plane installation detection
4. `src/core/scenery_manager.py` - Scenery installation logic
5. `src/gui/main_window.py` - Main UI window
6. `src/gui/search_panel.py` - Search interface
7. `src/gui/results_panel.py` - Results display with last update date
8. `src/gui/details_panel.py` - Airport details and version history view (NEW)
9. `src/main.py` - Application entry point

## API Integration Details

### X-Plane Gateway API Endpoints

**Search Airport:**

```
GET https://gateway.x-plane.com/apiv1/airport/{ICAO}
Response: Airport object with scenery pack IDs
```

**Get Scenery:**

```
GET https://gateway.x-plane.com/apiv1/scenery/{sceneryId}
Response: Scenery object with base64-encoded ZIP in 'masterZipBlob' field
```

**Key Fields:**

- `airport.scenery[]` - Array of scenery pack IDs
- `airport.recommendedSceneryId` - Gateway's recommended pack
- `scenery.masterZipBlob` - Base64-encoded ZIP file
- `scenery.type` - "2D" or "3D"
- `scenery.artistName`, `scenery.dateUploaded`, `scenery.dateAccepted`, `scenery.dateApproved`
- `scenery.Status` - "Approved", "Declined", or "Pending"
- `scenery.artistComments` - Description of changes made
- `scenery.moderatorComments` - Approval/rejection reasoning
- `scenery.features` - List of features (taxi routes, 3D, ground routes, etc.)
- `scenery.WEDVersion` - WorldEditor version used
- `scenery.XPlaneVersion` - X-Plane compatibility version
- `scenery.parentScenery` - Previous version reference for iteration history
- `scenery.EditorsChoice` - Notable submission flag

### Rate Limiting Considerations

- No formal rate limits, but "be considerate"
- For MVP: Add 1-second delay between download requests
- Implement exponential backoff on errors
- Consider caching search results locally in future

## X-Plane Installation Detection Strategy

**Common Windows Locations:**

1. `C:\Program Files\X-Plane 12\` or `X-Plane 11\`
2. `C:\Program Files (x86)\X-Plane 12\` or `X-Plane 11\`
3. `C:\X-Plane 12\` or `C:\X-Plane 11\`
4. Steam: `C:\Program Files (x86)\Steam\steamapps\common\X-Plane 12\` or `X-Plane 11\`
5. Check Windows Registry for installation path (if available)

**Validation:**

- Verify `X-Plane.exe` or `X-Plane.app` exists
- Check for `Custom Scenery` folder
- Read version from executable metadata or version file

**Scenery Installation Path:**

- `{X-Plane Root}/Custom Scenery/{SceneryPackName}/`
- Update `{X-Plane Root}/Custom Scenery/scenery_packs.ini` with new entry

## Data Models

### Airport

```python
@dataclass
class Airport:
    icao: str
    name: str
    latitude: float
    longitude: float
    scenery_ids: List[int]
    recommended_scenery_id: Optional[int]
    last_updated: str  # Date of most recent scenery update (NEW)
```

### Scenery

```python
@dataclass
class Scenery:
    id: int
    airport_icao: str
    artist_name: str
    date_uploaded: str
    date_accepted: Optional[str]  # NEW
    date_approved: Optional[str]
    type: str  # "2D" or "3D"
    status: str  # "Approved", "Declined", "Pending"
    master_zip_blob: str  # base64
    features: List[str]  # taxi routes, ground routes, 3D, ATC flows, etc.
    wed_version: Optional[str]  # WorldEditor version used (NEW)
    xplane_version: Optional[str]  # X-Plane compatibility (NEW)
    artist_comments: Optional[str]  # What was changed (NEW)
    moderator_comments: Optional[str]  # Approval/rejection reasons (NEW)
    parent_scenery_id: Optional[int]  # Previous version ID (NEW)
    is_editors_choice: bool  # Notable submission flag (NEW)
```

### InstalledScenery

```python
@dataclass
class InstalledScenery:
    scenery_id: int
    airport_icao: str
    installed_date: str
    install_path: str
    version: str
```

## Error Handling Strategy

1. **API Errors:**
   - Network failures → Show friendly error, allow retry
   - Invalid ICAO → Show "Airport not found" message
   - Rate limiting → Implement exponential backoff
   - Malformed responses → Log error, show generic message

2. **File System Errors:**
   - X-Plane not found → Prompt user to select manually
   - Permission denied → Show elevation prompt or manual instructions
   - Disk full → Clear error message with space needed
   - Corrupt ZIP → Skip and notify user

3. **User Input Validation:**
   - ICAO format: 3-4 uppercase letters, trim whitespace
   - Empty searches → Disable search button until input valid
   - Duplicate downloads → Detect and skip or ask to reinstall

## Testing Strategy (Manual MVP)

Since this is a learning project focused on quick MVP, we'll use manual testing:

1. **API Integration Testing:**
   - Test valid ICAO codes: KJFK, EGLL, KSFO
   - Test invalid codes: XXXX, 123, empty
   - Test network failure (disconnect internet)

2. **Installation Detection:**
   - Test on machine with X-Plane installed
   - Test on machine without X-Plane
   - Test with non-standard install location

3. **Download & Installation:**
   - Download single scenery, verify extraction
   - Download multiple sceneries in queue
   - Verify scenery_packs.ini updated correctly
   - Test re-download/reinstall same scenery

4. **UI Testing:**
   - Test all buttons and inputs
   - Verify progress bars update
   - Check error messages display correctly
   - Test window resize behavior

## Security Considerations

1. **API Safety:**
   - Use HTTPS for all API calls (Gateway uses HTTPS)
   - Validate JSON responses before parsing
   - Set reasonable timeouts (30s for API, 5min for downloads)

2. **File System Safety:**
   - Validate ZIP contents before extraction (no path traversal)
   - Only write to X-Plane Custom Scenery folder
   - Create backup of scenery_packs.ini before modifying
   - Use Python's `zipfile` with safe extraction

3. **Input Validation:**
   - Sanitize ICAO input (uppercase, alphanumeric only)
   - Validate file paths before operations
   - Prevent code injection in logging

4. **No Authentication Needed:**
   - Read-only API operations (no PUT)
   - No user accounts or sensitive data

## Future Enhancements (Post-MVP)

Consider after completing MVP and getting user feedback:

- Map view for geographic search
- Browse by region/category
- Screenshot previews
- Update checker for installed sceneries
- Conflict detection between overlapping sceneries
- Export/import installed scenery lists
- Dark mode theme
- Multi-language support

## Verification & Testing Plan

After implementation, verify the following:

1. **Core Functionality:**
   - Search for "KJFK" → Returns JFK airport with scenery options
   - Download a scenery → ZIP extracts to Custom Scenery folder
   - Check installed sceneries list → Shows downloaded items
   - Launch X-Plane → New scenery appears in sim

2. **Batch Operations:**
   - Queue 3 sceneries → All download sequentially
   - Cancel mid-download → Queue updates correctly

3. **Edge Cases:**
   - Search invalid ICAO → Clear error message
   - X-Plane not detected → Allows manual path selection
   - Internet disconnects → Graceful failure with retry option

4. **UI/UX:**
   - All buttons respond to clicks
   - Progress bars show real progress
   - Window can be resized without breaking layout
   - Application closes cleanly without errors

## Success Criteria

MVP is complete when:

- ✅ User can search by ICAO and see results
- ✅ User can download and install sceneries to X-Plane
- ✅ App detects X-Plane installation automatically
- ✅ Multiple sceneries can be queued for download
- ✅ Installed sceneries are tracked and visible
- ✅ Application runs standalone on Windows without Python installed
- ✅ Clear error messages guide user through problems

## Development Time Estimate

Not providing time estimates (per project guidelines), but phases are ordered by priority. Focus on completing Phase 1-3 for a functional prototype, then iterate based on testing feedback.

---

**Ready to start with Phase 1: Setting up the project structure and Gateway API client.**
