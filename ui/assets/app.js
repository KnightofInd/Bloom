const queryInput = document.getElementById("queryInput");
const searchBtn = document.getElementById("searchBtn");
const lifecycleBtn = document.getElementById("lifecycleBtn");
const lmpDate = document.getElementById("lmpDate");
const lifecycleQuery = document.getElementById("lifecycleQuery");
const lifecyclePreview = document.getElementById("lifecyclePreview");
const lifecycleMeta = document.getElementById("lifecycleMeta");
const resetBtn = document.getElementById("resetBtn");
const minRating = document.getElementById("minRating");
const maxPrice = document.getElementById("maxPrice");
const topN = document.getElementById("topN");
const kValue = document.getElementById("kValue");
const resultsList = document.getElementById("resultsList");
const explanation = document.getElementById("explanation");
const status = document.getElementById("status");
const tabs = document.querySelectorAll(".mode-tabs .tab");
const searchPanel = document.getElementById("searchPanel");
const lifecyclePanel = document.getElementById("lifecyclePanel");

const cardTemplate = document.getElementById("resultCard");

const setStatus = (text, tone) => {
  status.textContent = text;
  status.style.background = tone === "error" ? "#ffd8d8" : "#cce9df";
  status.style.color = tone === "error" ? "#8c2c2c" : "#2b5d55";
};

const formatPrice = (value) => {
  if (value === null || value === undefined) return "Price: N/A";
  return `Price: ${value}`;
};

const formatRating = (value) => {
  if (value === null || value === undefined) return "Rating: N/A";
  return `Rating: ${value}`;
};

const clearResults = () => {
  resultsList.innerHTML = "";
  lifecycleMeta.textContent = "";
};

const renderResults = (products) => {
  clearResults();
  if (!products || products.length === 0) {
    resultsList.innerHTML = "<div class='card'>No results found.</div>";
    return;
  }

  products.forEach((product) => {
    const card = cardTemplate.content.cloneNode(true);
    card.querySelector(".card-title").textContent = product.name || "Unnamed product";
    card.querySelector(".card-category").textContent = product.category || "";
    card.querySelector(".pill").textContent = product.matched_need || "Match";
    card.querySelector(".card-desc").textContent = product.description || "";
    card.querySelector(".price").textContent = formatPrice(product.price);
    card.querySelector(".rating").textContent = formatRating(product.rating);
    card.querySelector(".need").textContent = `Need: ${product.matched_need || ""}`;
    resultsList.appendChild(card);
  });
};

const requestRecommendations = async () => {
  const query = queryInput.value.trim();
  if (!query) {
    setStatus("Add a query to continue", "error");
    return;
  }

  setStatus("Searching...", "normal");
  explanation.textContent = "";
  explanation.classList.remove("empty");
  clearResults();

  const payload = {
    user_query: query,
    top_n: Number(topN.value || 3),
    k: Number(kValue.value || 5),
    min_rating: Number(minRating.value || 4.2),
    max_price: maxPrice.value ? Number(maxPrice.value) : null,
  };

  try {
    const response = await fetch("/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || "Request failed");
    }

    const data = await response.json();
    renderResults(data.products);
    explanation.textContent = data.explanation || "No explanation available.";
    if (data.meta && data.meta.lifecycle_stage) {
      const weeks = data.meta.lifecycle_weeks ?? "";
      lifecycleMeta.textContent = `Lifecycle: ${data.meta.lifecycle_stage.replace("_", " ")} ${weeks ? `(${weeks} weeks)` : ""}`;
    }
    setStatus("Results ready", "normal");
  } catch (error) {
    setStatus("Search failed", "error");
    explanation.textContent = "We could not complete the request. Please try again.";
  }
};

const requestLifecycleRecommendations = async () => {
  const dateValue = lmpDate.value;
  if (!dateValue) {
    setStatus("Add an LMP date to continue", "error");
    return;
  }

  setStatus("Searching...", "normal");
  explanation.textContent = "";
  explanation.classList.remove("empty");
  clearResults();

  const payload = {
    lmp_date: dateValue,
    user_query: lifecycleQuery.value.trim() || null,
    top_n: Number(topN.value || 3),
    k: Number(kValue.value || 5),
    min_rating: Number(minRating.value || 4.2),
    max_price: maxPrice.value ? Number(maxPrice.value) : null,
  };

  try {
    const response = await fetch("/lifecycle_recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || "Request failed");
    }

    const data = await response.json();
    renderResults(data.products);
    explanation.textContent = data.explanation || "No explanation available.";
    if (data.meta && data.meta.lifecycle_stage) {
      const weeks = data.meta.lifecycle_weeks ?? "";
      lifecycleMeta.textContent = `Lifecycle: ${data.meta.lifecycle_stage.replace("_", " ")} ${weeks ? `(${weeks} weeks)` : ""}`;
    }
    setStatus("Results ready", "normal");
  } catch (error) {
    setStatus("Search failed", "error");
    explanation.textContent = "We could not complete the request. Please try again.";
  }
};

const resetFilters = () => {
  minRating.value = 4.2;
  maxPrice.value = "";
  topN.value = 3;
  kValue.value = 8;
};

searchBtn.addEventListener("click", requestRecommendations);
lifecycleBtn.addEventListener("click", requestLifecycleRecommendations);
queryInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    requestRecommendations();
  }
});
lifecycleQuery.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    requestLifecycleRecommendations();
  }
});
resetBtn.addEventListener("click", resetFilters);

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((item) => item.classList.remove("active"));
    tab.classList.add("active");
    const mode = tab.dataset.mode;
    if (mode === "lifecycle") {
      lifecyclePanel.classList.remove("hidden");
      searchPanel.classList.add("hidden");
    } else {
      searchPanel.classList.remove("hidden");
      lifecyclePanel.classList.add("hidden");
    }
  });
});

const updateLifecyclePreview = () => {
  const value = lmpDate.value;
  if (!value) {
    lifecyclePreview.textContent = "Add a date to see trimester.";
    return;
  }

  const today = new Date();
  const lmp = new Date(`${value}T00:00:00`);
  const diffMs = today - lmp;
  if (Number.isNaN(diffMs) || diffMs < 0) {
    lifecyclePreview.textContent = "LMP date must be in the past.";
    return;
  }

  const weeks = Math.floor(diffMs / (1000 * 60 * 60 * 24 * 7));
  let stage = "First trimester";
  if (weeks <= 12) {
    stage = "First trimester";
  } else if (weeks <= 27) {
    stage = "Second trimester";
  } else if (weeks <= 40) {
    stage = "Third trimester";
  } else {
    stage = "Postpartum";
  }

  lifecyclePreview.textContent = `${stage} · week ${weeks}`;
};

lmpDate.addEventListener("change", updateLifecyclePreview);

resetFilters();
updateLifecyclePreview();
