// =====================================================
// SHOPBOOST AI FRONTEND JAVASCRIPT
// =====================================================

const API_BASE_URL = "http://127.0.0.1:8000";

const body = document.body;
const themeToggle = document.getElementById("themeToggle");
const themeIcon = themeToggle?.querySelector("i");

const searchForm = document.getElementById("searchForm");
const userQuery = document.getElementById("userQuery");
const askButton = document.getElementById("askAI");
const aiResult = document.getElementById("aiResult");
const assistantStatus = document.getElementById("assistantStatus");
const searchMessage = document.getElementById("searchMessage");
const assistantButton = document.getElementById("assistantButton");
const exploreButton = document.getElementById("exploreButton");

// =====================================================
// THEME TOGGLE
// =====================================================

const savedTheme = localStorage.getItem("shopboost-theme");

if (savedTheme === "dark") {
    body.classList.add("dark");
    if (themeIcon) themeIcon.className = "fa-solid fa-moon";
}

if (themeToggle) {
    themeToggle.addEventListener("click", () => {
        body.classList.toggle("dark");
        const dark = body.classList.contains("dark");

        if (themeIcon) {
            themeIcon.className = dark
                ? "fa-solid fa-moon"
                : "fa-solid fa-sun";
        }

        localStorage.setItem("shopboost-theme", dark ? "dark" : "light");
    });
}

// =====================================================
// ASK AI
// =====================================================

if (searchForm) {
    searchForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await askAI();
    });
}

async function askAI() {
    if (!userQuery || !askButton || !aiResult) {
        console.error("ShopBoost AI: required elements are missing.");
        return;
    }

    const query = userQuery.value.trim();

    if (!query) {
        showError("Please enter what you are looking for.");
        userQuery.focus();
        return;
    }

    askButton.disabled = true;
    askButton.innerHTML =
        '<i class="fa-solid fa-spinner fa-spin"></i><span>Thinking...</span>';

    aiResult.classList.add("show");
    aiResult.innerHTML = `
        <div class="ai-loading">
            <i class="fa-solid fa-spinner fa-spin"></i>
            AI is finding the best recommendation for you...
        </div>
    `;

    if (assistantStatus) {
        assistantStatus.textContent =
            "Analyzing products and finding the best option...";
    }
    if (searchMessage) searchMessage.textContent = "";

    try {
        console.log("ShopBoost AI request:", query);

        // IMPORTANT: main.py exposes POST /api/agent and expects { message: ... }
        const response = await fetch(`${API_BASE_URL}/api/agent`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: query })
        });

        const contentType = response.headers.get("content-type") || "";
        const data = contentType.includes("application/json")
            ? await response.json()
            : { success: false, message: await response.text() };

        console.log("ShopBoost AI response:", data);

        if (!response.ok) {
            throw new Error(data.detail || data.message || `Server error: ${response.status}`);
        }

        if (!data.success) {
            throw new Error(data.message || "No suitable product was found.");
        }

        displayAIRecommendation(data);

    } catch (error) {
        console.error("ShopBoost AI error:", error);

        showError(`
            Unable to get the AI recommendation.<br><br>
            Make sure the backend is running at
            <code>${API_BASE_URL}</code>.<br><br>
            <strong>Error:</strong> ${escapeHTML(error.message)}
        `);

        if (assistantStatus) {
            assistantStatus.textContent =
                "AI assistant could not connect to the backend.";
        }
    } finally {
        askButton.disabled = false;
        askButton.innerHTML =
            '<i class="fa-regular fa-paper-plane"></i><span>Ask AI</span>';
    }
}

// =====================================================
// DISPLAY RECOMMENDATION
// =====================================================

function displayAIRecommendation(data) {
    const product = data.product || {};
    const upsell = data.upsell || null;

    const productName = product.name || "Recommended Product";
    const price = product.price ?? "N/A";
    const reason = data.reason || "This product matches your requirements.";
    const rating = product.rating ?? null;
    const confidence = typeof data.confidence === "number"
        ? Math.round(data.confidence * 100)
        : null;

    const upsellHTML = upsell ? `
        <div class="ai-upsell">
            <div class="ai-upsell-title">
                <i class="fa-solid fa-arrow-trend-up"></i>
                Relevant Upsell
            </div>
            <div class="ai-upsell-product">
                ${escapeHTML(upsell.name || "Recommended accessory")}
                <span>₹${escapeHTML(String(upsell.price ?? "N/A"))}</span>
            </div>
            <div class="ai-upsell-reason">
                ${escapeHTML(data.upsell_reason || "This is a relevant addition to the recommended product.")}
            </div>
        </div>
    ` : "";

    aiResult.innerHTML = `
        <div class="ai-result-header">
            <i class="fa-solid fa-robot"></i>
            <span>AI Recommendation</span>
        </div>

        <div class="ai-product-name">${escapeHTML(productName)}</div>
        <div class="ai-price">₹${escapeHTML(String(price))}</div>

        ${rating !== null ? `
            <div class="ai-rating">
                <i class="fa-solid fa-star"></i>
                ${escapeHTML(String(rating))}/5
            </div>
        ` : ""}

        <div class="ai-why">Why AI selected it:</div>
        <div class="ai-reason">${escapeHTML(reason)}</div>

        ${confidence !== null ? `
            <div class="ai-confidence">AI confidence: ${confidence}%</div>
        ` : ""}

        ${upsellHTML}
    `;

    aiResult.classList.add("show");

    if (assistantStatus) {
        assistantStatus.textContent =
            "AI recommendation generated successfully.";
    }
}

function showError(message) {
    if (!aiResult) return;

    aiResult.classList.add("show");
    aiResult.innerHTML = `
        <div class="ai-error">
            <i class="fa-solid fa-circle-exclamation"></i>
            <div>${message}</div>
        </div>
    `;
}

// =====================================================
// ENTER KEY
// =====================================================

if (userQuery) {
    userQuery.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            if (searchForm) searchForm.requestSubmit();
            else askAI();
        }
    });
}

// =====================================================
// HEADER ASSISTANT BUTTON
// =====================================================

if (assistantButton) {
    assistantButton.addEventListener("click", () => {
        if (!userQuery) return;
        userQuery.focus();
        userQuery.scrollIntoView({ behavior: "smooth", block: "center" });
    });
}

// =====================================================
// EXPLORE BUTTON
// =====================================================

if (exploreButton) {
    exploreButton.addEventListener("click", () => {
        document.querySelector(".features")?.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    });
}

// =====================================================
// SAFE HTML
// =====================================================

function escapeHTML(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
