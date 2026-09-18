const checkNewsButton = document.getElementById("checkNews");
const statusElement = document.getElementById("status");
const resultElement = document.getElementById("result");


function createElement(tag, className, text = "") {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    if (text) {
        element.textContent = text;
    }

    return element;
}


function createEvidenceCard(article) {
    const card = createElement("div", "news-article");

    const link = document.createElement("a");

    link.href = article.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";

    link.textContent =
        article.title || "View source article";

    const domain = createElement(
        "div",
        "news-domain",
        article.source || "Unknown source"
    );

    card.appendChild(link);
    card.appendChild(domain);

    if (article.published) {
        const date = createElement(
            "div",
            "news-date",
            article.published
        );

        card.appendChild(date);
    }

    return card;
}


function addEvidenceSection(title, articles) {
    if (!articles || articles.length === 0) {
        return;
    }

    const sectionTitle = createElement(
        "div",
        "evidence-group-title",
        title
    );

    resultElement.appendChild(sectionTitle);

    articles.forEach((article) => {
        resultElement.appendChild(
            createEvidenceCard(article)
        );
    });
}


function showError(message) {
    resultElement.innerHTML = "";

    const errorBox = createElement(
        "div",
        "error-message",
        message
    );

    resultElement.appendChild(errorBox);

    resultElement.style.display = "block";
}


/*
 * Convert whatever status the backend sends
 * into one of our five standard statuses.
 */
function normalizeStatus(data) {

    const rawStatus =
        data.verification_status ||
        data.status ||
        data.prediction ||
        data.result ||
        "";

    const status = String(rawStatus)
        .toLowerCase()
        .trim();


    if (
        status === "strong" ||
        status.includes("strongly supported")
    ) {
        return "strong";
    }


    if (
        status === "supported" ||
        status.includes("support")
    ) {
        return "supported";
    }


    if (
        status === "contradicted" ||
        status.includes("contradict")
    ) {
        return "contradicted";
    }


    if (
        status === "limited" ||
        status.includes("limited")
    ) {
        return "limited";
    }


    if (
        status === "unverified" ||
        status.includes("unverified")
    ) {
        return "unverified";
    }


    /*
     * Fallback:
     * If the backend gives supporting evidence but
     * does not provide a recognizable status, treat
     * it as supported rather than showing an error.
     */

    const supportingCount =
        data.supporting_count ||
        data.supporting_articles?.length ||
        0;

    const conflictingCount =
        data.conflicting_count ||
        data.conflicting_articles?.length ||
        0;


    if (supportingCount > 0 && supportingCount >= conflictingCount) {
        return "supported";
    }


    if (conflictingCount > 0 && conflictingCount > supportingCount) {
        return "contradicted";
    }


    return "unverified";
}


function getVerdictText(status) {

    switch (status) {

        case "strong":
            return "Looks Supported";

        case "supported":
            return "Some Evidence Supports This";

        case "limited":
            return "Not Enough Information";

        case "unverified":
            return "Could Not Verify";

        case "contradicted":
            return "Conflicting Information Found";

        default:
            return "Could Not Verify";
    }
}


function getResultClass(status) {

    if (
        status === "strong" ||
        status === "supported"
    ) {
        return "real";
    }


    if (status === "contradicted") {
        return "fake";
    }


    return "limited";
}


function getExplanation(status) {

    switch (status) {

        case "strong":
            return "Multiple current sources strongly support the main claim in this article.";

        case "supported":
            return "We found current online sources that support this story, but additional checking is recommended.";

        case "limited":
            return "We found some related information, but there is not enough reliable evidence to reach a clear conclusion.";

        case "unverified":
            return "We could not find enough relevant current information to verify this story.";

        case "contradicted":
            return "Current sources contain information that conflicts with the main claim. Check the sources before reaching a conclusion.";

        default:
            return "We could not confidently verify this article.";
    }
}


function displayResult(data) {

    resultElement.innerHTML = "";

    /*
     * FIX:
     * Correctly determine the verification status
     * from the backend response.
     */

    const status = normalizeStatus(data);


    resultElement.className =
        `result ${getResultClass(status)}`;


    /* Verdict */

    const prediction = createElement(
        "div",
        "prediction-text",
        getVerdictText(status)
    );

    resultElement.appendChild(prediction);


    /* Explanation */

    const explanation = createElement(
        "div",
        "summary-text",
        getExplanation(status)
    );

    resultElement.appendChild(explanation);


    /* Evidence strength */

    if (
        typeof data.confidence !== "undefined" &&
        data.confidence !== null
    ) {

        const confidence = createElement(
            "div",
            "confidence",
            `Live evidence strength: ${data.confidence}%`
        );

        resultElement.appendChild(confidence);
    }


    /* What we found */

    const evidenceSummary = createElement(
        "div",
        "evidence-summary"
    );


    const summaryTitle = createElement(
        "div",
        "summary-title",
        "What we found"
    );

    evidenceSummary.appendChild(summaryTitle);


    const totalReports =
        data.total_articles ||
        data.live_articles?.length ||
        0;


    const sourceCount =
        data.source_count ||
        0;


    let summaryText;


    if (
        totalReports > 0 &&
        sourceCount > 0
    ) {

        summaryText =
            `${totalReports} related reports from ${sourceCount} different sources.`;

    } else if (totalReports > 0) {

        summaryText =
            `${totalReports} related reports were found online.`;

    } else {

        summaryText =
            "No closely related current reports were found.";
    }


    const summaryTextElement = createElement(
        "div",
        "summary-text",
        summaryText
    );

    evidenceSummary.appendChild(
        summaryTextElement
    );


    const supportingCount =
        data.supporting_count ||
        data.supporting_articles?.length ||
        0;


    const conflictingCount =
        data.conflicting_count ||
        data.conflicting_articles?.length ||
        0;


    if (supportingCount > 0) {

        const detail = createElement(
            "div",
            "summary-detail",
            `${supportingCount} report${supportingCount === 1 ? "" : "s"} strongly support${supportingCount === 1 ? "s" : ""} the story.`
        );

        evidenceSummary.appendChild(detail);
    }


    if (conflictingCount > 0) {

        const detail = createElement(
            "div",
            "summary-detail",
            `${conflictingCount} report${conflictingCount === 1 ? "" : "s"} contain${conflictingCount === 1 ? "s" : ""} conflicting information.`
        );

        evidenceSummary.appendChild(detail);
    }


    resultElement.appendChild(
        evidenceSummary
    );


    /* Supporting Information */

    addEvidenceSection(
        "✓ Supporting Information",
        data.supporting_articles
    );


    /* Conflicting Information */

    addEvidenceSection(
        "⚠ Conflicting Information",
        data.conflicting_articles
    );


    /* Related Coverage */

    addEvidenceSection(
        "Related Coverage",
        data.related_articles
    );


    /* No evidence */

    if (totalReports === 0) {

        const noEvidence = createElement(
            "div",
            "no-evidence",
            "Try checking the article again later or compare it with trusted news sources."
        );

        resultElement.appendChild(
            noEvidence
        );
    }


    /* Disclaimer */

    const disclaimer = createElement(
        "div",
        "disclaimer",
        "This tool compares the story with currently available web evidence. It does not guarantee that a claim is true or false."
    );

    resultElement.appendChild(
        disclaimer
    );


    resultElement.style.display = "block";
}


async function getCurrentArticle() {

    const tabs = await chrome.tabs.query({
        active: true,
        currentWindow: true
    });


    if (!tabs || !tabs[0]) {
        throw new Error(
            "No active tab found."
        );
    }


    const tab = tabs[0];


    let articleData;


    try {

        const results =
            await chrome.scripting.executeScript({

                target: {
                    tabId: tab.id
                },

                func: () => {

                    const article =
                        document.querySelector("article") ||
                        document.querySelector("main") ||
                        document.querySelector('[role="main"]');


                    const headline =
                        document.querySelector("h1")?.innerText ||
                        document.querySelector("h2")?.innerText ||
                        document
                            .querySelector(
                                'meta[property="og:title"]'
                            )
                            ?.content ||
                        document.title ||
                        "";


                    const articleText =
                        article?.innerText ||
                        document.body?.innerText ||
                        "";


                    return {
                        headline: headline.trim(),
                        articleText: articleText.trim(),
                        url: window.location.href
                    };
                }
            });


        articleData =
            results?.[0]?.result;


    } catch (error) {

        throw new Error(
            "This page cannot be analyzed by the extension."
        );
    }


    if (!articleData) {

        throw new Error(
            "Could not read the current article."
        );
    }


    if (!articleData.headline) {

        throw new Error(
            "No article headline was found on this page."
        );
    }


    return articleData;
}


async function checkArticle() {

    checkNewsButton.disabled = true;

    checkNewsButton.classList.add(
        "loading"
    );


    statusElement.textContent =
        "Reading the article and checking current web evidence...";


    resultElement.style.display =
        "none";

    resultElement.innerHTML = "";


    try {

        const article =
            await getCurrentArticle();


        statusElement.textContent =
            "Searching current online sources...";


        const response =
            await fetch(
                "http://127.0.0.1:5000/verify",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        headline: article.headline,
                        article_text: article.articleText,
                        url: article.url
                    })
                }
            );


        if (!response.ok) {

            throw new Error(
                "Verification request failed."
            );
        }


        const data =
            await response.json();


        displayResult(data);


        statusElement.textContent =
            "Analysis complete.";


    } catch (error) {

        console.error(error);


        statusElement.textContent =
            "Something went wrong.";


        showError(
            "Please try again in a moment. If the problem continues, the verification service may be temporarily unavailable."
        );


    } finally {

        checkNewsButton.disabled = false;

        checkNewsButton.classList.remove(
            "loading"
        );
    }
}


checkNewsButton.addEventListener(
    "click",
    checkArticle
);