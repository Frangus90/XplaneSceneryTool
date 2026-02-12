# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-02-12

### Added
- Initial release of X-Plane Scenery Tool
- Search airports by ICAO code via X-Plane Gateway API
- View detailed airport information and scenery history
- Download scenery packs with progress tracking
- Auto-extract downloaded sceneries for X-Plane
- Configurable X-Plane installation path
- Configurable download folder
- Dark theme UI with CustomTkinter
- Link to view airports on X-Plane Gateway website
- Parallel scenery fetching for improved performance
- Download queue with status tracking

### Fixed
- Threading deadlock in download queue
- X-Plane path detection for Custom Scenery folder
