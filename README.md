# Fake News Detector

A Chrome browser extension that analyzes news articles and compares their claims with currently available online news evidence.

## Project Overview

Fake news and misleading information can spread quickly through online platforms. This project provides a simple browser-based tool that helps users check a news article by comparing its headline and content with current online news reports.

The system uses a Chrome extension connected to a Flask backend. The backend searches live news coverage and analyzes the relevance, source diversity, and freshness of the available evidence.

## Key Features

- Chrome browser extension
- One-click article analysis
- Extracts the current article headline, text, and URL
- Live web-based news search
- Comparison with multiple news sources
- Evidence-strength scoring
- Supporting and conflicting evidence detection
- Related coverage display
- User-friendly verification results
- Disclaimer explaining that the result is not a guarantee of truth or falsity

## Technology Stack

### Frontend
- HTML
- CSS
- JavaScript
- Chrome Extension Manifest V3

### Backend
- Python
- Flask
- Requests
- Google News RSS

## How It Works

```text
User opens a news article
        ↓
Chrome Extension
        ↓
Extracts headline and article content
        ↓
Sends information to Flask backend
        ↓
Backend searches current online news
        ↓
Relevant reports are collected
        ↓
Evidence is analyzed
        ↓
Evidence strength is calculated
        ↓
Result is displayed in the extension