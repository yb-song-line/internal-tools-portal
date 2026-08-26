const state = { tools: [], category: "전체", query: "" };
const isPublicMirror = window.location.hostname === "yb-song-line.github.io";
const elements = {
  title: document.getElementById("portalTitle"),
  subtitle: document.getElementById("portalSubtitle"),
  notice: document.getElementById("portalNotice"),
  count: document.getElementById("toolCount"),
  search: document.getElementById("searchInput"),
  categories: document.getElementById("categoryFilter"),
  grid: document.getElementById("toolGrid"),
  empty: document.getElementById("emptyState"),
};

function text(value) {
  return String(value ?? "").trim();
}

function toolSearchText(tool) {
  return [tool.name, tool.description, tool.category, ...(tool.tags || [])].map(text).join(" ").toLocaleLowerCase("ko");
}

function accessLabel(access) {
  if (access === "enterprise-protected") return { label: "사내 Git 인증", className: "protected" };
  if (access === "portal-protected") return { label: "포털 내 보호", className: "protected" };
  return { label: "외부 공개 URL", className: "public" };
}

function createToolCard(tool) {
  const card = document.createElement("article");
  card.className = `tool-card${tool.featured ? " featured" : ""}`;

  const head = document.createElement("div");
  head.className = "tool-card-head";
  const icon = document.createElement("span");
  icon.className = "tool-icon";
  icon.textContent = text(tool.icon) || "↗";
  const access = accessLabel(tool.access);
  const badge = document.createElement("span");
  badge.className = `access-badge ${access.className}`;
  badge.textContent = access.label;
  head.append(icon, badge);

  const category = document.createElement("p");
  category.className = "tool-category";
  category.textContent = tool.category;
  const title = document.createElement("h2");
  title.textContent = tool.name;
  const description = document.createElement("p");
  description.className = "tool-description";
  description.textContent = tool.description;

  const tags = document.createElement("div");
  tags.className = "tag-list";
  for (const item of tool.tags || []) {
    const tag = document.createElement("span");
    tag.textContent = item;
    tags.append(tag);
  }

  const processing = document.createElement("div");
  processing.className = "processing-note";
  processing.textContent = text(tool.processing) || "처리 방식 확인 필요";

  const risk = document.createElement("p");
  risk.className = "risk-note";
  risk.textContent = text(tool.riskNote);
  risk.hidden = !risk.textContent;

  const actions = document.createElement("div");
  actions.className = "tool-actions";
  const openLink = document.createElement("a");
  openLink.className = "open-tool";
  openLink.href = tool.url;
  openLink.target = "_blank";
  openLink.rel = "noopener noreferrer";
  openLink.textContent = "도구 열기";
  actions.append(openLink);
  if (tool.sourceUrl) {
    const sourceLink = document.createElement("a");
    sourceLink.className = "source-link";
    sourceLink.href = tool.sourceUrl;
    sourceLink.target = "_blank";
    sourceLink.rel = "noopener noreferrer";
    sourceLink.textContent = "Git";
    actions.append(sourceLink);
  }

  card.append(head, category, title, description, tags, risk, processing, actions);
  return card;
}

function renderTools() {
  const query = state.query.toLocaleLowerCase("ko");
  const visible = state.tools.filter(tool => {
    const categoryMatches = state.category === "전체" || tool.category === state.category;
    return categoryMatches && (!query || toolSearchText(tool).includes(query));
  });
  elements.grid.replaceChildren(...visible.map(createToolCard));
  elements.empty.hidden = visible.length !== 0;
}

function renderCategories() {
  const categories = ["전체", ...new Set(state.tools.map(tool => tool.category))];
  elements.categories.replaceChildren(...categories.map(category => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = category;
    button.className = category === state.category ? "active" : "";
    button.setAttribute("aria-pressed", String(category === state.category));
    button.addEventListener("click", () => {
      state.category = category;
      renderCategories();
      renderTools();
    });
    return button;
  }));
}

async function initialize() {
  const toolsUrl = document.body.dataset.toolsUrl || "/api/tools";
  const response = await fetch(toolsUrl, { credentials: "same-origin" });
  if (response.status === 401) {
    window.location.assign("/login");
    return;
  }
  if (!response.ok) throw new Error(`도구 목록을 불러오지 못했습니다 (${response.status})`);
  const data = await response.json();
  state.tools = Array.isArray(data.tools) ? data.tools.map(tool => ({
    ...tool,
    url: isPublicMirror && tool.publicUrl ? tool.publicUrl : tool.url,
    sourceUrl: isPublicMirror ? (tool.publicSourceUrl || "") : tool.sourceUrl,
    access: isPublicMirror && tool.publicAccess ? tool.publicAccess : tool.access,
  })) : [];
  elements.title.textContent = text(data.portal?.title) || "업무 도구 포털";
  elements.subtitle.textContent = text(data.portal?.subtitle);
  elements.notice.textContent = text(data.portal?.notice);
  elements.notice.hidden = !elements.notice.textContent;
  elements.count.textContent = String(state.tools.length);
  renderCategories();
  renderTools();
}

elements.search.addEventListener("input", event => {
  state.query = event.target.value.trim();
  renderTools();
});

initialize().catch(error => {
  elements.grid.innerHTML = `<div class="load-error"><strong>도구 목록을 불러오지 못했습니다.</strong><span>${text(error.message)}</span></div>`;
});
