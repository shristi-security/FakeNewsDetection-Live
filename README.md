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
```

## Verification Results

The extension provides different results depending on the available evidence:

- **Looks Supported** — strong current corroboration was found.
- **Some Evidence Supports This** — supporting evidence was found, but additional checking is recommended.
- **Not Enough Information** — there is not enough relevant evidence to make a strong assessment.
- **Could Not Verify** — the system could not find sufficient relevant coverage.
- **Conflicting Information Found** — relevant sources contain information that conflicts with the article.

The evidence strength shown by the extension is a heuristic score based on factors such as relevance, source diversity, and freshness. It is not a probability that an article is true or false.

## Project Structure

```text
FakeNewsDetection-Live/
│
├── extension/
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.css
│   └── popup.js
│
├── templates/
│   └── index.html
│
├── app.py
├── requirements.txt
├── README.md
└── LICENSE
```

## Installation

### 1. Install Python

Make sure Python is installed on your system.

### 2. Install Dependencies

Open a terminal in the project folder and run:

```bash
pip install -r requirements.txt
```

### 3. Start the Flask Backend

Run:

```bash
python app.py
```

The backend will start locally at:

```text
http://127.0.0.1:5000/
```

### 4. Load the Chrome Extension

1. Open Google Chrome.
2. Go to:

```text
chrome://extensions/
```

3. Enable **Developer mode**.
4. Click **Load unpacked**.
5. Select the project's `extension` folder.
6. The **Fake News Detector** extension will appear in Chrome.

### 5. Verify an Article

1. Open a news article in Chrome.
2. Click the Fake News Detector extension.
3. Click **Check This Article**.
4. Wait for the live verification.
5. Review the result and supporting/related coverage.

## Important Note

This project is designed as an evidence-assistance tool. It compares an article against currently available online news coverage but does not guarantee that a claim is true or false.

The availability and quality of online news coverage can change over time, and multiple websites may report the same underlying source.

## Future Improvements

- Integration with dedicated fact-checking databases
- More news and fact-checking sources
- Improved claim-level analysis
- Advanced natural language processing
- Better detection of conflicting claims
- Support for additional browsers
- Improved source credibility analysis

## Project Purpose

This project was developed as an academic cybersecurity and technology project to explore how browser extensions, web technologies, and automated evidence analysis can be used to help users evaluate online news information.
