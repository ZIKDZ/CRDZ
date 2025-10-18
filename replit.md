# Overview

This is a Discord bot for Clash Royale that provides player profile management, deck visualization, and emote features. The bot integrates with the Clash Royale API to fetch player data, card information, and generate deck images. It uses Discord's slash commands for user interaction and includes admin tools for API health checks.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
- **Technology**: Discord.py with slash commands (app_commands)
- **Command Structure**: Cog-based architecture for modularity
- **Rationale**: Cogs allow separation of concerns (player management, deck handling, emotes, admin tools) and easier maintenance

## API Integration
- **Primary API**: Clash Royale Official API (api.clashroyale.com)
- **Authentication**: Bearer token-based authentication via CR_API_TOKEN
- **Async HTTP Client**: aiohttp for non-blocking API requests
- **Caching Strategy**: 
  - Card data is cached globally after first fetch to reduce API calls
  - Uses asyncio locks to prevent race conditions during cache initialization
  - Emote URLs are scraped once and cached for subsequent random selections

## Data Persistence
- **Storage Format**: JSON file-based system (players.json)
- **Data Model**: Simple key-value store mapping Discord user IDs to Clash Royale player tags
- **Location**: Configured via config.ini (DATA_FILE path)
- **Rationale**: Lightweight solution suitable for small-to-medium user base; no database overhead

## Configuration Management
- **Format**: INI file (config.ini) parsed with configparser
- **Sections**:
  - Tokens: Discord and Clash Royale API credentials
  - Roles: Trophy-based role IDs for auto-assignment
  - Emojis: Custom emoji identifiers for bot responses
  - Paths: File system paths for data and fonts
- **Rationale**: Separates secrets and configuration from code; easy to modify without touching source

## Image Generation
- **Library**: Pillow (PIL)
- **Use Case**: Generates 4x2 grid deck images with card icons, levels, and average elixir
- **Process**:
  1. Fetches card icon URLs from Clash Royale API
  2. Downloads images asynchronously via aiohttp
  3. Composites into styled grid with custom fonts
  4. Returns as Discord-uploadable BytesIO object
- **Styling**: Clash Royale-themed colors (blues, panel backgrounds)

## Role Management
- **Trophy Thresholds**: Automatic role assignment based on player trophies
  - Under 5000
  - 5000-9999
  - 10000+
- **Nickname System**: Appends Clash Royale name to Discord nickname (e.g., "User | CRName")
- **Permissions**: Requires manage_nicknames permission for profile setup

## Web Scraping
- **Target**: Clash Royale Fandom Wiki for emote images
- **Library**: BeautifulSoup4 for HTML parsing
- **Caching**: First scrape populates EMOTE_CACHE list, subsequent calls use cache
- **URL Manipulation**: Regex-based image dimension adjustment for optimization

## Error Handling
- **API Failures**: Graceful degradation with user-friendly error messages
- **Timeout Configuration**: 10-second timeout for API requests, 8 seconds for admin checks
- **Permission Errors**: Catches Discord.Forbidden for nickname/role assignment failures
- **Status Code Handling**: Specific messages for 403 (forbidden), 401 (unauthorized), timeouts

## Command Structure
- **Player Management**: `/profile-setup` (admin-only) links Discord users to CR profiles
- **Admin Tools**: `/check-api` verifies API connectivity and token validity
- **Deck Handling**: Reusable CopyDeckView component with link buttons
- **Emote System**: Random emote fetching with dimension customization

# External Dependencies

## APIs
- **Clash Royale API** (https://api.clashroyale.com/v1/)
  - Authentication: Bearer token
  - Endpoints used:
    - `/players/{tag}` - Player profile data
    - `/cards` - Full card metadata
  - Rate limiting: Not explicitly handled; relies on reasonable request patterns

## Third-Party Services
- **ipify.org** (https://api.ipify.org)
  - Purpose: Fetch public IP address on bot startup
  - No authentication required

- **Clash Royale Fandom Wiki** (https://clashroyale.fandom.com)
  - Purpose: Scrape emote image URLs
  - Method: HTTP GET with User-Agent header
  - No API key required

## Discord Integration
- **Discord Gateway**: WebSocket connection for real-time events
- **Slash Commands**: Registered via Discord application commands API
- **Intents Required**:
  - members: Access to member join/update events
  - message_content: Read message content (if needed for future prefix commands)

## Python Libraries
- **discord.py**: Discord bot framework
- **aiohttp**: Async HTTP requests
- **Pillow**: Image generation and manipulation
- **BeautifulSoup4**: HTML parsing for web scraping
- **requests**: Sync HTTP (used only for IP fetch and admin API check)

## File System
- **players.json**: Persistent user-to-player tag mappings
- **config.ini**: Configuration file (not in repository, must be created)
- **Font File**: Custom TrueType font for deck image text rendering (path configured in config.ini)

## Discord Server Resources
- **Custom Emojis**: Referenced by emoji IDs in config.ini
- **Roles**: Trophy-based roles must be pre-created with IDs in config
- **Permissions**: Bot requires manage_nicknames and manage_roles permissions