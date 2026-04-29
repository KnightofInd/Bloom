const queryInput = document.getElementById("queryInput");
const searchBtn = document.getElementById("searchBtn");
const translateBtn = document.getElementById("translateBtn");
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

let currentLang = "en";

const translations = {
  en: {
    tagline: "Calm, caring recommendations for every stage.",
    heroTitle: "Find the right essentials in seconds",
    heroBody: "Tell us how you are feeling and what you need. We will map your request to trusted categories and suggest top products.",
    tabSearch: "Search",
    tabLifecycle: "Lifecycle",
    searchBtn: "Search",
    lifecycleBtn: "Use lifecycle",
    lmpHint: "Enter the first day of your last menstrual period (LMP).",
    queryPlaceholder: "Example: I am 7 months pregnant and have back pain",
    lifecyclePlaceholder: "Optional details: back pain, sleep issues, feeding",
    lifecyclePreview: "Add a date to see trimester.",
    chipGentle: "Gentle picks",
    chipTrusted: "Trusted ratings",
    chipClear: "Clear explanations",
    filtersTitle: "Filters",
    minRating: "Minimum rating",
    maxPrice: "Max price",
    maxPricePlaceholder: "No limit",
    topResults: "Top results",
    candidates: "Candidates per need (k)",
    resetBtn: "Reset",
    resultsTitle: "Recommendations",
    statusReady: "Ready",
    statusSearching: "Searching...",
    statusResultsReady: "Results ready",
    statusSearchFailed: "Search failed",
    statusAddQuery: "Add a query to continue",
    statusAddLmp: "Add an LMP date to continue",
    explanationEmpty: "Run a search to see a personalized explanation.",
    explanationMissing: "No explanation available.",
    explanationError: "We could not complete the request. Please try again.",
    noResults: "No results found.",
    match: "Match",
    priceLabel: "Price",
    ratingLabel: "Rating",
    na: "N/A",
    needLabel: "Need",
    lifecycleLabel: "Lifecycle:",
    lmpPast: "LMP date must be in the past.",
    stage_first_trimester: "First trimester",
    stage_second_trimester: "Second trimester",
    stage_third_trimester: "Third trimester",
    stage_postpartum: "Postpartum",
    translateToAr: "AR",
    translateToEn: "EN",
  },
  ar: {
    tagline: "توصيات هادئة ومطمئنة لكل مرحلة.",
    heroTitle: "اعثري على الأساسيات المناسبة في ثوانٍ",
    heroBody: "أخبرينا بما تشعرين به وما تحتاجينه. سنحوّل طلبك إلى فئات موثوقة ونقترح أفضل المنتجات.",
    tabSearch: "بحث",
    tabLifecycle: "مرحلة الحمل",
    searchBtn: "ابحث",
    lifecycleBtn: "استخدمي المرحلة",
    lmpHint: "أدخلي أول يوم في آخر دورة شهرية (LMP).",
    queryPlaceholder: "مثال: أنا في الشهر السابع وأعاني من ألم الظهر",
    lifecyclePlaceholder: "تفاصيل اختيارية: ألم الظهر، مشاكل النوم، الرضاعة",
    lifecyclePreview: "أدخلي تاريخًا لمعرفة الثلث.",
    chipGentle: "اختيارات لطيفة",
    chipTrusted: "تقييمات موثوقة",
    chipClear: "توضيحات واضحة",
    filtersTitle: "الفلاتر",
    minRating: "الحد الأدنى للتقييم",
    maxPrice: "أقصى سعر",
    maxPricePlaceholder: "بدون حد",
    topResults: "أفضل النتائج",
    candidates: "عدد المرشحين لكل حاجة (k)",
    resetBtn: "إعادة ضبط",
    resultsTitle: "التوصيات",
    statusReady: "جاهز",
    statusSearching: "جارٍ البحث...",
    statusResultsReady: "النتائج جاهزة",
    statusSearchFailed: "فشل البحث",
    statusAddQuery: "أضيفي طلبًا للمتابعة",
    statusAddLmp: "أضيفي تاريخ LMP للمتابعة",
    explanationEmpty: "نفّذي بحثًا لرؤية تفسير مخصص.",
    explanationMissing: "لا يوجد تفسير متاح.",
    explanationError: "تعذر إكمال الطلب. يرجى المحاولة مرة أخرى.",
    noResults: "لم يتم العثور على نتائج.",
    match: "مطابقة",
    priceLabel: "السعر",
    ratingLabel: "التقييم",
    na: "غير متاح",
    needLabel: "الحاجة",
    lifecycleLabel: "المرحلة:",
    lmpPast: "يجب أن يكون تاريخ LMP في الماضي.",
    stage_first_trimester: "الثلث الأول",
    stage_second_trimester: "الثلث الثاني",
    stage_third_trimester: "الثلث الثالث",
    stage_postpartum: "ما بعد الولادة",
    translateToAr: "AR",
    translateToEn: "EN",
  },
};

const t = (key) => translations[currentLang][key] || translations.en[key] || key;

const applyTranslations = () => {
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.getAttribute("data-i18n");
    node.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    const key = node.getAttribute("data-i18n-placeholder");
    node.setAttribute("placeholder", t(key));
  });
  document.documentElement.lang = currentLang;
  document.documentElement.dir = currentLang === "ar" ? "rtl" : "ltr";
  translateBtn.textContent = currentLang === "ar" ? t("translateToEn") : t("translateToAr");
};

const setStatus = (text, tone) => {
  status.textContent = text;
  status.style.background = tone === "error" ? "#ffd8d8" : "#cce9df";
  status.style.color = tone === "error" ? "#8c2c2c" : "#2b5d55";
};

const formatPrice = (value) => {
  if (value === null || value === undefined) return `${t("priceLabel")}: ${t("na")}`;
  return `${t("priceLabel")}: ${value}`;
};

const formatRating = (value) => {
  if (value === null || value === undefined) return `${t("ratingLabel")}: ${t("na")}`;
  return `${t("ratingLabel")}: ${value}`;
};

const clearResults = () => {
  resultsList.innerHTML = "";
  lifecycleMeta.textContent = "";
};

const renderResults = (products) => {
  clearResults();
  if (!products || products.length === 0) {
    resultsList.innerHTML = `<div class='card'>${t("noResults")}</div>`;
    return;
  }

  products.forEach((product) => {
    const card = cardTemplate.content.cloneNode(true);
    card.querySelector(".card-title").textContent = product.name || "Unnamed product";
    card.querySelector(".card-category").textContent = product.category || "";
    card.querySelector(".pill").textContent = product.matched_need || t("match");
    card.querySelector(".card-desc").textContent = product.description || "";
    card.querySelector(".price").textContent = formatPrice(product.price);
    card.querySelector(".rating").textContent = formatRating(product.rating);
    card.querySelector(".need").textContent = `${t("needLabel")}: ${product.matched_need || ""}`;
    resultsList.appendChild(card);
  });
};

const requestRecommendations = async () => {
  const query = queryInput.value.trim();
  if (!query) {
    setStatus(t("statusAddQuery"), "error");
    return;
  }

  setStatus(t("statusSearching"), "normal");
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
    explanation.textContent = data.explanation || t("explanationMissing");
    if (data.meta && data.meta.lifecycle_stage) {
      const weeks = data.meta.lifecycle_weeks ?? "";
      const stageKey = `stage_${data.meta.lifecycle_stage}`;
      const stageLabel = t(stageKey);
      const weeksText = weeks ? `(${weeks} ${currentLang === "ar" ? "أسبوع" : "weeks"})` : "";
      lifecycleMeta.textContent = `${t("lifecycleLabel")} ${stageLabel} ${weeksText}`;
    }
    setStatus(t("statusResultsReady"), "normal");
  } catch (error) {
    setStatus(t("statusSearchFailed"), "error");
    explanation.textContent = t("explanationError");
  }
};

const requestLifecycleRecommendations = async () => {
  const dateValue = lmpDate.value;
  if (!dateValue) {
    setStatus(t("statusAddLmp"), "error");
    return;
  }

  setStatus(t("statusSearching"), "normal");
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
    explanation.textContent = data.explanation || t("explanationMissing");
    if (data.meta && data.meta.lifecycle_stage) {
      const weeks = data.meta.lifecycle_weeks ?? "";
      const stageKey = `stage_${data.meta.lifecycle_stage}`;
      const stageLabel = t(stageKey);
      const weeksText = weeks ? `(${weeks} ${currentLang === "ar" ? "أسبوع" : "weeks"})` : "";
      lifecycleMeta.textContent = `${t("lifecycleLabel")} ${stageLabel} ${weeksText}`;
    }
    setStatus(t("statusResultsReady"), "normal");
  } catch (error) {
    setStatus(t("statusSearchFailed"), "error");
    explanation.textContent = t("explanationError");
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
    lifecyclePreview.textContent = t("lifecyclePreview");
    return;
  }

  const today = new Date();
  const lmp = new Date(`${value}T00:00:00`);
  const diffMs = today - lmp;
  if (Number.isNaN(diffMs) || diffMs < 0) {
    lifecyclePreview.textContent = t("lmpPast");
    return;
  }

  const weeks = Math.floor(diffMs / (1000 * 60 * 60 * 24 * 7));
  let stageKey = "stage_first_trimester";
  if (weeks <= 12) {
    stageKey = "stage_first_trimester";
  } else if (weeks <= 27) {
    stageKey = "stage_second_trimester";
  } else if (weeks <= 40) {
    stageKey = "stage_third_trimester";
  } else {
    stageKey = "stage_postpartum";
  }

  const stageLabel = t(stageKey);
  const weekLabel = currentLang === "ar" ? "الأسبوع" : "week";
  lifecyclePreview.textContent = `${stageLabel} · ${weekLabel} ${weeks}`;
};

lmpDate.addEventListener("change", updateLifecyclePreview);
translateBtn.addEventListener("click", () => {
  currentLang = currentLang === "en" ? "ar" : "en";
  applyTranslations();
  updateLifecyclePreview();
});

resetFilters();
applyTranslations();
updateLifecyclePreview();
