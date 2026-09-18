from flask import Flask, render_template, request, jsonify
import requests
import xml.etree.ElementTree as ET
import re
from urllib.parse import quote_plus, urlparse
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone


app = Flask(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

MIN_RELEVANCE = 0.35
MAX_DISPLAY_ARTICLES = 8
MAX_SEARCH_RESULTS = 8


# ============================================================
# TEXT HELPERS
# ============================================================

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to",
    "in", "on", "for", "with", "from", "by", "at", "as",
    "is", "are", "was", "were", "be", "been", "has", "have",
    "had", "this", "that", "these", "those", "it", "its",
    "he", "she", "they", "them", "his", "her", "their",
    "after", "before", "into", "over", "under", "about",
    "than", "also", "said", "says", "according", "new",
    "news", "report", "reports", "latest", "today",
    "will", "would", "could", "should", "may", "might"
}


def clean_text(text):
    """Normalize text for comparison."""

    if not text:
        return ""

    text = text.lower()

    # Remove URLs
    text = re.sub(
        r"http\S+|www\S+|https\S+",
        " ",
        text
    )

    # Keep letters, numbers and spaces
    text = re.sub(
        r"[^a-zA-Z0-9\s]",
        " ",
        text
    )

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def get_keywords(text):
    """Extract useful keywords."""

    words = clean_text(text).split()

    return [
        word
        for word in words
        if len(word) >= 4
        and word not in STOP_WORDS
    ]


def similarity_score(text1, text2):
    """Calculate textual similarity."""

    a = clean_text(text1)
    b = clean_text(text2)

    if not a or not b:
        return 0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def keyword_overlap(text1, text2):
    """Calculate keyword overlap."""

    words1 = set(
        get_keywords(text1)
    )

    words2 = set(
        get_keywords(text2)
    )

    if not words1:
        return 0

    return (
        len(words1.intersection(words2))
        / len(words1)
    )


# ============================================================
# FRESHNESS
# ============================================================

def calculate_freshness(pub_date):
    """
    Estimate how recent an article is.

    100 = very recent
    0   = very old or invalid
    """

    if not pub_date:
        return 0

    try:
        published = parsedate_to_datetime(
            pub_date
        )

        if published.tzinfo is None:
            published = published.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(
            timezone.utc
        )

        age_hours = (
            now
            - published.astimezone(
                timezone.utc
            )
        ).total_seconds() / 3600

        if age_hours <= 24:
            return 100

        if age_hours <= 72:
            return 90

        if age_hours <= 168:
            return 75

        if age_hours <= 720:
            return 50

        if age_hours <= 2160:
            return 25

        return 10

    except Exception:
        return 0


# ============================================================
# SOURCE HELPERS
# ============================================================

def normalize_source(source):
    """Normalize publisher names."""

    if not source:
        return ""

    source = source.lower().strip()

    source = re.sub(
        r"\b(online|news|media|network|official)\b",
        "",
        source
    )

    source = re.sub(
        r"[^a-z0-9\s]",
        " ",
        source
    )

    source = re.sub(
        r"\s+",
        " ",
        source
    )

    return source.strip()


def get_domain(url):
    """Extract domain from URL."""

    try:
        domain = urlparse(
            url
        ).netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:
        return ""


# ============================================================
# CONFLICT SIGNALS
# ============================================================

CONFLICT_PATTERNS = [
    r"\bfalse\b",
    r"\bfake\b",
    r"\bfact check\b",
    r"\bfact-check\b",
    r"\bdebunked\b",
    r"\bdebunks\b",
    r"\bdebunk\b",
    r"\bmisleading\b",
    r"\bmisinformation\b",
    r"\bdisinformation\b",
    r"\buntrue\b",
    r"\bnot true\b",
    r"\bno evidence\b",
    r"\bdenied\b",
    r"\bdenies\b",
    r"\bdenial\b",
    r"\bhoax\b",
    r"\bclaim is wrong\b",
    r"\bclaim was wrong\b",
    r"\bclaim is false\b",
    r"\bclaim was false\b"
]


def contains_conflict_signal(title):
    """
    Detect whether a result headline contains
    language commonly associated with a disputed
    or fact-checked claim.

    This is NOT treated as proof by itself.
    """

    text = clean_text(title)

    for pattern in CONFLICT_PATTERNS:

        if re.search(
            pattern,
            text
        ):
            return True

    return False


# ============================================================
# GOOGLE NEWS LIVE SEARCH
# ============================================================

def search_google_news(
    query,
    max_results=MAX_SEARCH_RESULTS
):

    try:

        encoded_query = quote_plus(
            query
        )

        url = (
            "https://news.google.com/rss/search"
            f"?q={encoded_query}"
            "&hl=en-IN"
            "&gl=IN"
            "&ceid=IN:en"
        )

        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent":
                    "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        root = ET.fromstring(
            response.content
        )

        articles = []

        for item in root.findall(
            ".//item"
        )[:max_results]:

            title = item.findtext(
                "title",
                ""
            ).strip()

            link = item.findtext(
                "link",
                ""
            ).strip()

            pub_date = item.findtext(
                "pubDate",
                ""
            ).strip()

            source_element = item.find(
                "source"
            )

            source = ""

            if source_element is not None:

                source = (
                    source_element.text
                    or ""
                ).strip()

            if title and link:

                articles.append({

                    "title": title,

                    "url": link,

                    "source": source,

                    "date": pub_date
                })

        return {
            "error": None,
            "articles": articles
        }

    except Exception as e:

        print(
            "Google News search error:",
            e
        )

        return {
            "error": str(e),
            "articles": []
        }


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(articles):

    unique_articles = []

    seen_titles = set()

    for article in articles:

        title = clean_text(
            article.get(
                "title",
                ""
            )
        )

        if not title:
            continue

        if title in seen_titles:
            continue

        seen_titles.add(title)

        unique_articles.append(
            article
        )

    return unique_articles


def keep_best_per_source(articles):
    """
    Keep the strongest result from each
    publisher so one publisher cannot dominate
    the evidence list.
    """

    best_by_source = {}

    for article in articles:

        source = normalize_source(
            article.get(
                "source",
                ""
            )
        )

        if not source:

            source = get_domain(
                article.get(
                    "url",
                    ""
                )
            )

        score = article.get(
            "final_score",
            0
        )

        if (
            source not in best_by_source
            or score >
            best_by_source[source].get(
                "final_score",
                0
            )
        ):

            best_by_source[
                source
            ] = article

    return list(
        best_by_source.values()
    )


# ============================================================
# EVIDENCE CLASSIFICATION
# ============================================================

def classify_evidence(
    article,
    headline
):
    """
    Classify an article as:

    supporting
    conflicting
    related

    Conflict classification requires both
    meaningful relevance and conflict language.
    """

    relevance = article.get(
        "relevance",
        0
    )

    title = article.get(
        "title",
        ""
    )

    conflict_signal = (
        contains_conflict_signal(
            title
        )
    )

    # A conflict keyword alone is NOT enough.
    # The result must also be meaningfully
    # related to the original headline.
    if (
        conflict_signal
        and relevance >= 0.42
    ):

        return "conflicting"

    # Strong matching evidence
    if relevance >= 0.55:

        return "supporting"

    return "related"


# ============================================================
# LIVE EVIDENCE ANALYSIS
# ============================================================

def analyze_live_evidence(
    headline,
    article_text
):

    headline = headline.strip()

    # Limit body size so very long pages
    # do not generate excessive search terms.
    body_text = article_text[:5000]

    headline_keywords = get_keywords(
        headline
    )

    body_keywords = get_keywords(
        body_text
    )

    # --------------------------------------------------------
    # SEARCH QUERIES
    # --------------------------------------------------------

    exact_query = headline

    keyword_query = " ".join(
        headline_keywords[:8]
    )

    body_keyword_query = " ".join(
        body_keywords[:8]
    )

    fact_check_query = (
        f'"{headline}" fact check'
    )

    queries = [
        exact_query,
        keyword_query,
        body_keyword_query,
        fact_check_query
    ]

    # Remove empty and duplicate queries
    queries = list(
        dict.fromkeys(
            query
            for query in queries
            if query
        )
    )

    main_query = exact_query

    all_articles = []

    search_errors = []

    # --------------------------------------------------------
    # LIVE SEARCH
    # --------------------------------------------------------

    for query in queries:

        result = search_google_news(
            query
        )

        if result["error"]:

            search_errors.append(
                result["error"]
            )

        all_articles.extend(
            result["articles"]
        )

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    all_articles = remove_duplicates(
        all_articles
    )

    # --------------------------------------------------------
    # SCORE EACH ARTICLE
    # --------------------------------------------------------

    relevant_articles = []

    for article in all_articles:

        title = article.get(
            "title",
            ""
        )

        # Headline similarity
        headline_similarity = (
            similarity_score(
                headline,
                title
            )
        )

        # Headline keyword overlap
        headline_overlap = (
            keyword_overlap(
                headline,
                title
            )
        )

        # Body keyword overlap
        body_overlap = (
            keyword_overlap(
                body_text,
                title
            )
        )

        # Relevance combines:
        # 50% headline similarity
        # 30% headline keywords
        # 20% article-body keywords
        relevance = (
            headline_similarity * 0.50
            + headline_overlap * 0.30
            + body_overlap * 0.20
        )

        freshness = calculate_freshness(
            article.get(
                "date",
                ""
            )
        )

        # Final article quality:
        # 80% relevance
        # 20% freshness
        final_score = (
            relevance * 0.80
            + (freshness / 100) * 0.20
        )

        article["headline_similarity"] = round(
            headline_similarity * 100,
            1
        )

        article["keyword_overlap"] = round(
            headline_overlap * 100,
            1
        )

        article["body_overlap"] = round(
            body_overlap * 100,
            1
        )

        article["relevance"] = round(
            relevance,
            4
        )

        article["relevance_percent"] = round(
            relevance * 100,
            1
        )

        article["freshness"] = round(
            freshness,
            1
        )

        article["final_score"] = round(
            final_score * 100,
            1
        )

        # Classify evidence
        evidence_type = classify_evidence(
            article,
            headline
        )

        article[
            "evidence_type"
        ] = evidence_type

        # Keep sufficiently relevant results
        if relevance >= MIN_RELEVANCE:

            relevant_articles.append(
                article
            )

    # --------------------------------------------------------
    # SORT BY QUALITY
    # --------------------------------------------------------

    relevant_articles.sort(
        key=lambda x: x.get(
            "final_score",
            0
        ),
        reverse=True
    )

    # --------------------------------------------------------
    # KEEP BEST RESULT PER SOURCE
    # --------------------------------------------------------

    relevant_articles = (
        keep_best_per_source(
            relevant_articles
        )
    )

    relevant_articles.sort(
        key=lambda x: x.get(
            "final_score",
            0
        ),
        reverse=True
    )

    # Maximum displayed results
    relevant_articles = (
        relevant_articles[
            :MAX_DISPLAY_ARTICLES
        ]
    )

    # --------------------------------------------------------
    # SEPARATE EVIDENCE
    # --------------------------------------------------------

    supporting_articles = [
        article
        for article in relevant_articles
        if article.get(
            "evidence_type"
        ) == "supporting"
    ]

    conflicting_articles = [
        article
        for article in relevant_articles
        if article.get(
            "evidence_type"
        ) == "conflicting"
    ]

    related_articles = [
        article
        for article in relevant_articles
        if article.get(
            "evidence_type"
        ) == "related"
    ]

    # --------------------------------------------------------
    # COUNT DISTINCT SOURCES
    # --------------------------------------------------------

    sources = set()

    for article in relevant_articles:

        source = normalize_source(
            article.get(
                "source",
                ""
            )
        )

        if not source:

            source = get_domain(
                article.get(
                    "url",
                    ""
                )
            )

        if source:

            sources.add(
                source
            )

    source_count = len(
        sources
    )

    article_count = len(
        relevant_articles
    )

    supporting_count = len(
        supporting_articles
    )

    conflicting_count = len(
        conflicting_articles
    )

    # --------------------------------------------------------
    # EVIDENCE SCORE
    # --------------------------------------------------------

    if article_count == 0:

        evidence_score = 0

    else:

        average_relevance = (
            sum(
                article.get(
                    "relevance_percent",
                    0
                )
                for article
                in relevant_articles
            )
            / article_count
        )

        average_freshness = (
            sum(
                article.get(
                    "freshness",
                    0
                )
                for article
                in relevant_articles
            )
            / article_count
        )

        source_bonus = min(
            source_count * 5,
            20
        )

        evidence_score = (
            average_relevance * 0.65
            + average_freshness * 0.15
            + source_bonus
        )

        evidence_score = min(
            round(evidence_score),
            100
        )

    # --------------------------------------------------------
    # FINAL USER-FRIENDLY RESULT
    # --------------------------------------------------------

    # Conflicting evidence takes priority
    # only when meaningful relevant results exist.
    if (
        conflicting_count >= 2
        and conflicting_count
        >= supporting_count
    ):

        verification_level = (
            "contradicted"
        )

        verification_status = (
            "CONFLICTING INFORMATION FOUND"
        )

        prediction = (
            "CONFLICTING INFORMATION FOUND"
        )

        explanation = (
            f"We found {conflicting_count} "
            "relevant report(s) containing "
            "information that conflicts with "
            "the story. The claim should be "
            "checked against reliable sources "
            "before being trusted."
        )

    elif (
        supporting_count >= 4
        and source_count >= 4
        and evidence_score >= 60
    ):

        verification_level = "strong"

        verification_status = (
            "STRONG SUPPORTING EVIDENCE"
        )

        prediction = (
            "LOOKS SUPPORTED"
        )

        explanation = (
            f"We found {supporting_count} "
            "strongly related recent report(s) "
            f"from {source_count} distinct "
            "source(s) that support the story."
        )

    elif (
        supporting_count >= 2
        and source_count >= 2
        and evidence_score >= 40
    ):

        verification_level = "supported"

        verification_status = (
            "SUPPORTING INFORMATION FOUND"
        )

        prediction = (
            "LIKELY SUPPORTED"
        )

        explanation = (
            f"We found {supporting_count} "
            "relevant recent report(s) from "
            f"{source_count} distinct source(s) "
            "that support the story. "
            "Additional verification is "
            "recommended."
        )

    elif article_count > 0:

        verification_level = "limited"

        verification_status = (
            "NOT ENOUGH INFORMATION"
        )

        prediction = (
            "NOT ENOUGH INFORMATION"
        )

        explanation = (
            f"We found {article_count} "
            "related report(s), but there "
            "isn't enough clear evidence to "
            "confirm the story."
        )

    else:

        verification_level = "unverified"

        verification_status = (
            "COULD NOT VERIFY"
        )

        prediction = (
            "COULD NOT VERIFY"
        )

        explanation = (
            "We couldn't find enough relevant "
            "recent information to verify "
            "this story."
        )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {

        "prediction":
            prediction,

        "verification_status":
            verification_status,

        "verification_level":
            verification_level,

        # Kept as confidence for compatibility
        # with current popup.js.
        "confidence":
            evidence_score,

        "explanation":
            explanation,

        "articles":
            relevant_articles,

        "supporting_articles":
            supporting_articles,

        "conflicting_articles":
            conflicting_articles,

        "related_articles":
            related_articles,

        "source_count":
            source_count,

        "article_count":
            article_count,

        "supporting_count":
            supporting_count,

        "conflicting_count":
            conflicting_count,

        "search_query":
            main_query,

        "search_errors":
            search_errors
    }


# ============================================================
# HOME PAGE
# ============================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# LIVE VERIFICATION API
# ============================================================

@app.route(
    "/verify",
    methods=["POST"]
)
def verify():

    data = request.get_json()

    if not data:

        return jsonify({
            "error":
                "No article data received."
        }), 400

    headline = data.get(
        "headline",
        ""
    ).strip()

    article_text = data.get(
        "article_text",
        ""
    ).strip()

    article_url = data.get(
        "url",
        ""
    ).strip()

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not article_text:

        return jsonify({
            "error":
                "No article text found."
        }), 400

    # --------------------------------------------------------
    # FALLBACK HEADLINE
    # --------------------------------------------------------

    if not headline:

        words = article_text.split()

        headline = " ".join(
            words[:15]
        )

    # --------------------------------------------------------
    # LOG REQUEST
    # --------------------------------------------------------

    print(
        "\n======================================"
    )

    print(
        "LIVE VERIFICATION REQUEST"
    )

    print(
        "======================================"
    )

    print(
        "Headline:",
        headline
    )

    print(
        "URL:",
        article_url
    )

    print(
        "======================================\n"
    )

    # --------------------------------------------------------
    # ANALYZE
    # --------------------------------------------------------

    analysis = analyze_live_evidence(
        headline,
        article_text
    )

    # --------------------------------------------------------
    # RETURN JSON
    # --------------------------------------------------------

    return jsonify({

        "status":
            "success",

        "prediction":
            analysis[
                "prediction"
            ],

        "verification_status":
            analysis[
                "verification_status"
            ],

        "verification_level":
            analysis[
                "verification_level"
            ],

        "confidence":
            analysis[
                "confidence"
            ],

        "explanation":
            analysis[
                "explanation"
            ],

        "headline":
            headline,

        "search_query":
            analysis[
                "search_query"
            ],

        "article_url":
            article_url,

        "source_count":
            analysis[
                "source_count"
            ],

        "article_count":
            analysis[
                "article_count"
            ],

        "supporting_count":
            analysis[
                "supporting_count"
            ],

        "conflicting_count":
            analysis[
                "conflicting_count"
            ],

        "live_articles":
            analysis[
                "articles"
            ],

        "supporting_articles":
            analysis[
                "supporting_articles"
            ],

        "conflicting_articles":
            analysis[
                "conflicting_articles"
            ],

        "related_articles":
            analysis[
                "related_articles"
            ],

        "live_search_error":
            analysis[
                "search_errors"
            ]
    })


# ============================================================
# RUN FLASK
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )