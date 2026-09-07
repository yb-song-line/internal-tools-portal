const state = { tools: [], references: [], section: "tools", category: "전체", query: "" };
const isPublicMirror = window.location.hostname === "yb-song-line.github.io";
const assetVersion = "20260907-1";
const sectionSettings = {
  tools: {
    kicker: "WORK TOOLS",
    title: "업무 도구",
    description: "업무에 필요한 기능을 바로 실행할 수 있습니다.",
    countLabel: "사용 가능한 도구",
    searchPlaceholder: "도구명, 설명, 태그 검색",
  },
  references: {
    kicker: "INSIGHT LIBRARY",
    title: "인사이트 라이브러리",
    description: "외부 공개 정보로 작성한 HTML 보고서와 분석 자료를 확인할 수 있습니다.",
    countLabel: "공개 참고 자료",
    searchPlaceholder: "자료명, 설명, 태그 검색",
  },
};
const elements = {
  title: document.getElementById("portalTitle"),
  subtitle: document.getElementById("portalSubtitle"),
  notice: document.getElementById("portalNotice"),
  sectionNotice: document.getElementById("sectionNotice"),
  accessBadge: document.getElementById("portalAccessBadge"),
  count: document.getElementById("contentCount"),
  countLabel: document.getElementById("contentCountLabel"),
  search: document.getElementById("searchInput"),
  categories: document.getElementById("categoryFilter"),
  grid: document.getElementById("contentGrid"),
  empty: document.getElementById("emptyState"),
  emptyTitle: document.getElementById("emptyTitle"),
  emptyDescription: document.getElementById("emptyDescription"),
  sectionKicker: document.getElementById("sectionKicker"),
  sectionTitle: document.getElementById("sectionTitle"),
  sectionDescription: document.getElementById("sectionDescription"),
  tabs: [...document.querySelectorAll("[data-section]")],
};

function text(value) {
  return String(value ?? "").trim();
}

function currentItems() {
  return state.section === "references" ? state.references : state.tools;
}

function itemSearchText(item) {
  return [item.name, item.description, item.category, item.basis, ...(item.tags || [])]
    .map(text)
    .join(" ")
    .toLocaleLowerCase("ko");
}

function accessLabel(access) {
  if (access === "enterprise-protected") return { label: "사내 Git 인증", className: "protected" };
  if (access === "portal-protected") return { label: "포털 내 보호", className: "protected" };
  return { label: "외부 공개 URL", className: "public" };
}

function createContentCard(item) {
  const isReference = state.section === "references";
  const card = document.createElement("article");
  card.className = `tool-card${item.featured ? " featured" : ""}`;

  const head = document.createElement("div");
  head.className = "tool-card-head";
  const icon = document.createElement("span");
  icon.className = "tool-icon";
  icon.textContent = text(item.icon) || (isReference ? "▤" : "↗");
  const access = accessLabel(item.access);
  const badge = document.createElement("span");
  badge.className = `access-badge ${access.className}`;
  badge.textContent = access.label;
  head.append(icon, badge);

  const category = document.createElement("p");
  category.className = "tool-category";
  category.textContent = item.category;
  const title = document.createElement("h3");
  title.textContent = item.name;
  const description = document.createElement("p");
  description.className = "tool-description";
  description.textContent = item.description;

  const tags = document.createElement("div");
  tags.className = "tag-list";
  for (const value of item.tags || []) {
    const tag = document.createElement("span");
    tag.textContent = value;
    tags.append(tag);
  }

  const detail = document.createElement("div");
  detail.className = isReference ? "reference-note" : "processing-note";
  detail.textContent = isReference
    ? text(item.basis) || "공개 정보 기반"
    : text(item.processing) || "처리 방식 확인 필요";

  const risk = document.createElement("p");
  risk.className = "risk-note";
  risk.textContent = text(item.riskNote);
  risk.hidden = !risk.textContent;

  const actions = document.createElement("div");
  actions.className = "tool-actions";
  const openLink = document.createElement("a");
  openLink.className = "open-tool";
  openLink.href = item.url;
  openLink.target = "_blank";
  openLink.rel = "noopener noreferrer";
  openLink.textContent = isReference ? "자료 보기" : "도구 열기";
  actions.append(openLink);

  card.append(head, category, title, description, tags, risk, detail, actions);
  return card;
}

function renderContent() {
  const items = currentItems();
  const query = state.query.toLocaleLowerCase("ko");
  const visible = items.filter(item => {
    const categoryMatches = state.category === "전체" || item.category === state.category;
    return categoryMatches && (!query || itemSearchText(item).includes(query));
  });
  elements.grid.replaceChildren(...visible.map(createContentCard));
  elements.empty.hidden = visible.length !== 0;

  if (visible.length === 0 && state.section === "references" && !query && state.category === "전체") {
    elements.emptyTitle.textContent = "등록된 공개 자료가 없습니다.";
    elements.emptyDescription.textContent = "공개 정보로 작성된 HTML 보고서와 분석 자료를 이곳에 추가할 수 있습니다.";
  } else {
    elements.emptyTitle.textContent = "검색 결과가 없습니다.";
    elements.emptyDescription.textContent = "다른 검색어나 카테고리를 선택해 주세요.";
  }
}

function renderCategories() {
  const categories = ["전체", ...new Set(currentItems().map(item => item.category))];
  elements.categories.replaceChildren(...categories.map(category => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = category;
    button.className = category === state.category ? "active" : "";
    button.setAttribute("aria-pressed", String(category === state.category));
    button.addEventListener("click", () => {
      state.category = category;
      renderCategories();
      renderContent();
    });
    return button;
  }));
}

function renderSection() {
  const settings = sectionSettings[state.section];
  const items = currentItems();
  elements.sectionKicker.textContent = settings.kicker;
  elements.sectionTitle.textContent = settings.title;
  elements.sectionDescription.textContent = settings.description;
  elements.count.textContent = String(items.length);
  elements.countLabel.textContent = settings.countLabel;
  elements.search.placeholder = settings.searchPlaceholder;
  elements.sectionNotice.hidden = state.section !== "references";
  for (const tab of elements.tabs) {
    const active = tab.dataset.section === state.section;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
  }
  renderCategories();
  renderContent();
}

function mapPublicItem(item) {
  return {
    ...item,
    url: isPublicMirror && item.publicUrl ? item.publicUrl : item.url,
    access: isPublicMirror && item.publicAccess ? item.publicAccess : item.access,
  };
}

function prepareItems(items) {
  return items
    .filter(item =>
      item.enabled !== false
      && (!isPublicMirror || item.access === "external-public" || Boolean(item.publicUrl))
    )
    .map(mapPublicItem)
    .sort((left, right) =>
      (Number(left.order ?? 9999) - Number(right.order ?? 9999))
      || text(left.name).localeCompare(text(right.name), "ko")
    );
}

async function initialize() {
  const toolsUrl = document.body.dataset.toolsUrl || "/api/tools";
  const versionedToolsUrl = new URL(toolsUrl, window.location.href);
  versionedToolsUrl.searchParams.set("v", assetVersion);
  const response = await fetch(versionedToolsUrl, { credentials: "same-origin", cache: "no-store" });
  if (response.status === 401) {
    window.location.assign("/login");
    return;
  }
  if (!response.ok) throw new Error(`포털 정보를 불러오지 못했습니다 (${response.status})`);
  const data = await response.json();
  state.tools = Array.isArray(data.tools) ? prepareItems(data.tools) : [];
  state.references = Array.isArray(data.references) ? prepareItems(data.references) : [];
  elements.title.textContent = text(data.portal?.title) || "업무 포털";
  elements.subtitle.textContent = text(data.portal?.subtitle);
  document.title = elements.title.textContent;
  elements.notice.textContent = text(
    isPublicMirror ? data.portal?.publicNotice : data.portal?.notice
  );
  elements.notice.hidden = !elements.notice.textContent;
  elements.sectionNotice.textContent = text(
    isPublicMirror
      ? data.portal?.publicReferenceNotice || data.portal?.referenceNotice
      : data.portal?.referenceNotice
  );
  if (elements.accessBadge && isPublicMirror) {
    elements.accessBadge.textContent = "외부 공개";
    elements.accessBadge.classList.remove("protected");
    elements.accessBadge.classList.add("public");
  }
  renderSection();
}

elements.search.addEventListener("input", event => {
  state.query = event.target.value.trim();
  renderContent();
});

for (const tab of elements.tabs) {
  tab.addEventListener("click", () => {
    state.section = tab.dataset.section;
    state.category = "전체";
    state.query = "";
    elements.search.value = "";
    renderSection();
  });
}

initialize().catch(error => {
  elements.grid.innerHTML = `<div class="load-error"><strong>포털 정보를 불러오지 못했습니다.</strong><span>${text(error.message)}</span></div>`;
});
