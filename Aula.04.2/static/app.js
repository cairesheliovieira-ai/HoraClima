"use strict";
/**
 * StoreMaster v2 — Frontend SPA
 * ================================
 * Arquitetura em módulos: API, Store, Auth, Router, Dashboard,
 * Products, Sales, Modals, Toast, Confetti.
 *
 * Tecnologias:
 *   - Vanilla JS (ES2020+)
 *   - Chart.js 4 (CDN) — gráficos de linha e rosca
 *   - Fetch API — chamadas REST ao backend Flask
 *   - LocalStorage — persistência da sessão JWT
 */

// ═══════════════════════════════════════════════════════
// UTILS
// ═══════════════════════════════════════════════════════

/** Formata número como moeda BRL */
const fmt = (n) => Number(n).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

/** Formata data ISO para dd/mm/yy hh:mm */
const fmtDate = (s) => {
  const d = new Date(s);
  return isNaN(d) ? s : d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
};

/** Retorna YYYY-MM-DD dos últimos N dias */
const lastNDays = (n) => {
  const days = [];
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    days.push(d.toISOString().split("T")[0]);
  }
  return days;
};

/** Rótulo curto para datas (ex.: "Qui 27/03") */
const dayLabel = (iso) => {
  const d = new Date(iso + "T12:00:00");
  return d.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "2-digit" });
};

/** Seleciona elemento por ID */
const $ = (id) => document.getElementById(id);

/** Cria elemento HTML */
const el = (tag, cls, html) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
};

/** Anima contador numérico de 0 até value */
function animateCount(elem, end, isCurrency = false) {
  const duration = 900;
  const start = performance.now();
  const from = 0;
  function tick(now) {
    const p = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1 - p, 3);
    const cur = from + (end - from) * ease;
    elem.textContent = isCurrency ? fmt(cur) : Math.round(cur).toLocaleString("pt-BR");
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ═══════════════════════════════════════════════════════
// STORE (estado global)
// ═══════════════════════════════════════════════════════

const Store = {
  token:      localStorage.getItem("sm_token"),
  user:       localStorage.getItem("sm_user"),
  role:       localStorage.getItem("sm_role"),
  userId:     localStorage.getItem("sm_uid"),
  products:   [],
  categories: [],
  sales:      [],
  viewMode:   "grid",        // "grid" | "list"
  activeCat:  "all",
  searchQ:    "",
};

// ═══════════════════════════════════════════════════════
// API
// ═══════════════════════════════════════════════════════

const API = {
  _h: () => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${Store.token}`,
  }),

  async _fetch(url, opts = {}) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (res.status === 401) { Auth.logout(); return null; }
    if (!res.ok) throw new Error(data.error || `Erro ${res.status}`);
    return data;
  },

  login:        (u, p)      => fetch("/api/login", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({username:u,password:p}) }).then(r => r.json().then(d => ({ok:r.ok,...d}))),
  getCategories:()          => API._fetch("/api/categories",              { headers: API._h() }),
  getProducts:  ()          => API._fetch("/api/products",                { headers: API._h() }),
  createProduct:(b)         => API._fetch("/api/products",                { method:"POST", headers:API._h(), body:JSON.stringify(b) }),
  updateProduct:(id,b)      => API._fetch(`/api/products/${id}`,          { method:"PUT",  headers:API._h(), body:JSON.stringify(b) }),
  deleteProduct:(id)        => API._fetch(`/api/products/${id}`,          { method:"DELETE", headers:API._h() }),
  getSales:     ()          => API._fetch("/api/sales",                   { headers: API._h() }),
  createSale:   (pid,qty)   => API._fetch("/api/sales",                   { method:"POST", headers:API._h(), body:JSON.stringify({product_id:pid,quantity:qty}) }),
  getDashboard: ()          => API._fetch("/api/dashboard",               { headers: API._h() }),
};

// ═══════════════════════════════════════════════════════
// TOAST
// ═══════════════════════════════════════════════════════

function toast(msg, type = "info") {
  const c = $("toast-container");
  const t = el("div", `toast toast-${type}`, msg);
  c.appendChild(t);
  setTimeout(() => {
    t.style.animation = "toast-out .3s ease forwards";
    t.addEventListener("animationend", () => t.remove(), { once: true });
  }, 3000);
}

// ═══════════════════════════════════════════════════════
// CONFETTI
// ═══════════════════════════════════════════════════════

function confetti() {
  const colors = ["#4F8FFF","#8B5CF6","#22D3EE","#10B981","#FBBF24","#FB7185"];
  const layer = $("confetti-layer");
  for (let i = 0; i < 60; i++) {
    const p = document.createElement("div");
    p.className = "confetti-piece";
    p.style.cssText = `
      left:${Math.random()*100}vw;
      width:${Math.random()*10+4}px;
      height:${Math.random()*10+4}px;
      background:${colors[Math.floor(Math.random()*colors.length)]};
      animation-delay:${Math.random()*0.6}s;
      animation-duration:${Math.random()*0.8+1}s;
      border-radius:${Math.random()>0.5?"50%":"3px"};
    `;
    layer.appendChild(p);
    setTimeout(() => p.remove(), 2000);
  }
}

// ═══════════════════════════════════════════════════════
// MODALS
// ═══════════════════════════════════════════════════════

const Modals = {
  open: (id) => $(id)?.classList.remove("hidden"),
  close: (id) => $(id)?.classList.add("hidden"),
  init() {
    document.querySelectorAll(".mx,[data-close]").forEach(btn => {
      btn.addEventListener("click", () => Modals.close(btn.dataset.close));
    });
    document.querySelectorAll(".mbk").forEach(bk => {
      bk.addEventListener("click", e => { if (e.target === bk) Modals.close(bk.id); });
    });
  }
};

// ═══════════════════════════════════════════════════════
// AUTH
// ═══════════════════════════════════════════════════════

const Auth = {
  save(data) {
    Store.token  = data.token;
    Store.user   = data.user;
    Store.role   = data.role;
    Store.userId = data.user_id;
    ["sm_token","sm_user","sm_role","sm_uid"].forEach((k,i)=>
      localStorage.setItem(k, [data.token,data.user,data.role,data.user_id][i]));
    this.applyUser();
    $("login-screen").classList.add("gone");
    $("app").hidden = false;
    Router.go("dashboard");
  },
  applyUser() {
    $("sb-name").textContent  = Store.user  || "—";
    $("sb-role").textContent  = Store.role  || "—";
    $("sb-avatar").textContent= (Store.user||"A")[0].toUpperCase();
  },
  logout() {
    ["sm_token","sm_user","sm_role","sm_uid"].forEach(k => localStorage.removeItem(k));
    Object.assign(Store, {token:null,user:null,role:null,userId:null});
    $("app").hidden = true;
    $("login-screen").classList.remove("gone");
    $("login-form").reset();
    $("login-error").classList.add("hidden");
  },
  init() {
    $("login-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errEl = $("login-error");
      const btnTxt = $("login-btn-text");
      const sp = $("login-spinner");
      const btn = $("login-btn");
      errEl.classList.add("hidden");
      btn.disabled = true; btnTxt.textContent = "Autenticando…"; sp.classList.remove("hidden");
      const u = $("login-username").value.trim();
      const p = $("login-password").value;
      try {
        const r = await API.login(u, p);
        if (!r.ok) throw new Error(r.error || "Credenciais inválidas.");
        Auth.save(r);
      } catch(err) {
        errEl.textContent = err.message;
        errEl.classList.remove("hidden");
      } finally {
        btn.disabled = false; btnTxt.textContent = "Entrar no sistema"; sp.classList.add("hidden");
      }
    });
    $("btn-logout").addEventListener("click", Auth.logout);
  }
};

// ═══════════════════════════════════════════════════════
// ROUTER
// ═══════════════════════════════════════════════════════

const pageTitles = {
  dashboard: ["Dashboard", "Visão geral da loja"],
  products:  ["Produtos",  "Catálogo e estoque"],
  sales:     ["Vendas",    "Histórico de transações"],
};
const pageActions = {
  products: { label: "＋ Produto", fn: () => Products.openNew() },
  sales:    { label: "⚡ Nova Venda", fn: () => Sales.openNew() },
};

const Router = {
  current: null,
  go(page) {
    this.current = page;
    // Nav highlight
    document.querySelectorAll(".sb-item").forEach(b =>
      b.classList.toggle("active", b.dataset.page === page));
    // Page switch
    document.querySelectorAll(".page").forEach(s =>
      s.classList.toggle("active", s.id === `page-${page}`));
    // Header
    const [title, sub] = pageTitles[page] || [page, ""];
    $("header-title").textContent = title;
    $("header-sub").textContent   = sub;
    // Action button
    const act = pageActions[page];
    const abtn = $("btn-header-action");
    if (act) { abtn.textContent = act.label; abtn.onclick = act.fn; abtn.classList.remove("hidden"); }
    else abtn.classList.add("hidden");
    // Load data
    if (page === "dashboard") Dashboard.load();
    if (page === "products")  Products.load();
    if (page === "sales")     Sales.load();
  },
  init() {
    document.querySelectorAll(".sb-item,.link-btn").forEach(btn => {
      btn.addEventListener("click", () => btn.dataset.page && Router.go(btn.dataset.page));
    });
  }
};

// ═══════════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════════

let chartWeekly = null, chartCat = null;

const Dashboard = {
  async load() {
    try {
      const d = await API.getDashboard();
      if (!d) return;
      // KPIs
      animateCount($("val-revenue"),  d.total_revenue, true);
      animateCount($("val-profit"),   d.total_profit,  true);
      animateCount($("val-sales"),    d.total_sales,   false);
      animateCount($("val-products"), d.total_products,false);
      // Charts
      this.renderWeekly(d.weekly_sales);
      this.renderCategories(d.category_revenue);
      // Lists
      this.renderRecent(d.recent_sales);
      this.renderLowStock(d.low_stock);
    } catch(err) { toast("Erro no dashboard: " + err.message, "error"); }
  },

  renderWeekly(data) {
    const days = lastNDays(7);
    const map  = {};
    data.forEach(r => map[r.date] = r.revenue);
    const revenues = days.map(d => map[d] || 0);
    const labels   = days.map(dayLabel);

    const canvas = $("chart-weekly");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (chartWeekly) chartWeekly.destroy();

    const grad = ctx.createLinearGradient(0, 0, 0, 200);
    grad.addColorStop(0, "rgba(79,143,255,0.35)");
    grad.addColorStop(1, "rgba(79,143,255,0)");

    chartWeekly = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Receita",
          data: revenues,
          borderColor: "#4F8FFF",
          backgroundColor: grad,
          borderWidth: 2.5,
          pointBackgroundColor: "#4F8FFF",
          pointBorderColor: "#0F1A35",
          pointBorderWidth: 2,
          pointRadius: 5,
          tension: 0.4,
          fill: true,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => fmt(c.raw) }, backgroundColor: "#132040", titleColor: "#E2E8F0", bodyColor: "#94A3B8", borderColor: "#1e3060", borderWidth: 1 }
        },
        scales: {
          x: { grid: { color: "rgba(255,255,255,.04)" }, ticks: { color: "#475569", font: { size: 11 } } },
          y: { grid: { color: "rgba(255,255,255,.04)" }, ticks: { color: "#475569", font: { size: 11 }, callback: v => "R$" + (v >= 1000 ? (v/1000).toFixed(1)+"k" : v) } }
        }
      }
    });
  },

  renderCategories(data) {
    const canvas = $("chart-categories");
    const empty  = $("chart-cat-empty");
    if (!canvas) return;
    if (!data || !data.length) {
      canvas.classList.add("hidden"); empty.classList.remove("hidden"); return;
    }
    canvas.classList.remove("hidden"); empty.classList.add("hidden");
    if (chartCat) chartCat.destroy();
    chartCat = new Chart(canvas.getContext("2d"), {
      type: "doughnut",
      data: {
        labels: data.map(r => r.name),
        datasets: [{ data: data.map(r => r.revenue), backgroundColor: data.map(r => r.color), borderWidth: 0, borderRadius: 4, spacing: 3 }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: "70%",
        plugins: {
          legend: { position: "bottom", labels: { color: "#94A3B8", padding: 10, usePointStyle: true, font: { size: 11 } } },
          tooltip: { callbacks: { label: c => fmt(c.raw) }, backgroundColor: "#132040", titleColor: "#E2E8F0", bodyColor: "#94A3B8", borderColor: "#1e3060", borderWidth: 1 }
        }
      }
    });
  },

  renderRecent(items) {
    const c = $("recent-list");
    if (!c) return;
    if (!items?.length) {
      c.innerHTML = `<div class="empty-state"><span class="empty-ico">🧾</span><p>Nenhuma venda ainda.</p></div>`;
      return;
    }
    c.innerHTML = items.map(s => `
      <div class="recent-item">
        <span class="ri-dot"></span>
        <div class="ri-info">
          <div class="ri-name">${s.product_name}</div>
          <div class="ri-meta">${s.quantity} un. · ${s.seller} · ${fmtDate(s.sold_at)}</div>
        </div>
        <span class="ri-total">${fmt(s.total)}</span>
      </div>`).join("");
  },

  renderLowStock(items) {
    const c = $("low-stock-list");
    if (!c) return;
    if (!items?.length) {
      c.innerHTML = `<div class="empty-state"><span class="empty-ico">✅</span><p>Estoque OK em todos os produtos.</p></div>`;
      return;
    }
    c.innerHTML = items.map(p => {
      const pct = Math.round((p.stock / (p.min_stock || 1)) * 100);
      return `
        <div class="ls-item">
          <span class="ls-icon">${p.icon || "📦"}</span>
          <div class="ls-info">
            <div class="ls-name">${p.name}</div>
            <div class="ls-bar"><div class="ls-fill" style="width:${Math.min(pct,100)}%"></div></div>
          </div>
          <span class="ls-badge">${p.stock} un.</span>
        </div>`;
    }).join("");
  }
};

// ═══════════════════════════════════════════════════════
// PRODUCTS
// ═══════════════════════════════════════════════════════

let _deleteId = null, _deleteConfirmFn = null;

const Products = {
  async load() {
    try {
      [Store.products, Store.categories] = await Promise.all([API.getProducts(), API.getCategories()]);
      if (!Store.products || !Store.categories) return;
      this.renderCatTabs();
      this.render();
    } catch(err) { toast("Erro ao carregar produtos: " + err.message, "error"); }
  },

  filtered() {
    return Store.products.filter(p => {
      const matchCat = Store.activeCat === "all" || String(p.category_id) === String(Store.activeCat);
      const matchQ   = !Store.searchQ || p.name.toLowerCase().includes(Store.searchQ.toLowerCase());
      return matchCat && matchQ;
    });
  },

  render() {
    const container = $("products-container");
    const products  = this.filtered();
    if (!products.length) {
      container.innerHTML = `<div class="empty-state"><span class="empty-ico">📦</span><p>Nenhum produto encontrado.</p></div>`;
      return;
    }
    if (Store.viewMode === "grid") this.renderGrid(products);
    else this.renderList(products);
  },

  renderGrid(products) {
    const wrap = el("div", "products-grid");
    products.forEach((p, i) => {
      const pct      = p.min_stock > 0 ? Math.min((p.stock / (p.min_stock * 4)) * 100, 100) : 100;
      const stkClass = p.stock === 0 ? "stk-crit" : p.stock < p.min_stock ? "stk-warn" : "stk-ok";
      const barColor = p.stock === 0 ? "#FB7185" : p.stock < p.min_stock ? "#FBBF24" : "#10B981";
      const catColor = p.category_color || "#4F8FFF";
      const card = el("div", "pcard");
      card.style.animationDelay = `${i * 0.04}s`;
      card.dataset.id = p.id;
      card.innerHTML = `
        <div class="pcard-top">
          <div class="pcard-icon" style="background:${catColor}22;color:${catColor}">${p.category_icon || "📦"}</div>
          <div class="pcard-actions">
            <button class="iact" onclick="Products.openEdit(${p.id})" title="Editar">✏️</button>
            <button class="iact iact-del" onclick="Products.confirmDelete(${p.id},'${p.name.replace(/'/g,"\\'")}')" title="Excluir">🗑️</button>
          </div>
        </div>
        <h3 class="pcard-name">${p.name}</h3>
        <span class="cat-badge" style="background:${catColor}22;color:${catColor}">${p.category_icon||""} ${p.category_name||"Geral"}</span>
        <div class="pcard-price-row">
          <span class="pcard-price">${fmt(p.price)}</span>
          <span class="margin-badge">${p.margin_pct ?? 0}% lucro</span>
        </div>
        <div class="stock-bar-wrap"><div class="stock-fill" style="width:${pct}%;background:${barColor}"></div></div>
        <div class="pcard-stock-row">
          <span class="stk-num ${stkClass}">${p.stock} un.</span>
          <span class="stk-min">mín: ${p.min_stock}</span>
        </div>
        <button class="btn-quick-sell" onclick="Sales.openNew(${p.id})">⚡ Venda Rápida</button>
      `;
      wrap.appendChild(card);
    });
    const container = $("products-container");
    container.innerHTML = "";
    container.appendChild(wrap);
  },

  renderList(products) {
    const wrap = el("div", "products-list-wrap");
    wrap.innerHTML = `
      <div class="table-card">
        <div class="tbl-scroll">
          <table class="dtable">
            <thead><tr>
              <th>#</th><th>Nome</th><th>Categoria</th>
              <th>Preço</th><th>Custo</th><th>Margem</th>
              <th>Estoque</th><th>Ações</th>
            </tr></thead>
            <tbody>${products.map((p,i) => {
              const stkClass = p.stock === 0 ? "text-rose" : p.stock < p.min_stock ? "text-amber" : "text-green";
              const catColor = p.category_color || "#4F8FFF";
              return `<tr style="animation-delay:${i*0.03}s">
                <td><strong>#${p.id}</strong></td>
                <td>${p.name}</td>
                <td><span class="badge" style="background:${catColor}22;color:${catColor}">${p.category_icon||""} ${p.category_name||"—"}</span></td>
                <td>${fmt(p.price)}</td>
                <td>${fmt(p.cost)}</td>
                <td><span class="badge b-green">${p.margin_pct ?? 0}%</span></td>
                <td class="${stkClass}"><strong>${p.stock}</strong> / ${p.min_stock}</td>
                <td>
                  <button class="iact" onclick="Products.openEdit(${p.id})" title="Editar">✏️</button>
                  <button class="iact iact-del" onclick="Products.confirmDelete(${p.id},'${p.name.replace(/'/g,"\\'")}')" title="Excluir">🗑️</button>
                </td>
              </tr>`;
            }).join("")}</tbody>
          </table>
        </div>
      </div>`;
    const container = $("products-container");
    container.innerHTML = "";
    container.appendChild(wrap);
  },

  renderCatTabs() {
    const tabs = $("cat-tabs");
    tabs.innerHTML = `<button class="cat-tab${Store.activeCat==="all"?" active":""}" data-cat="all">Todos</button>`;
    Store.categories.forEach(c => {
      const t = el("button", `cat-tab${Store.activeCat===String(c.id)?" active":""}`, `${c.icon} ${c.name}`);
      t.dataset.cat = c.id;
      t.addEventListener("click", () => {
        Store.activeCat = t.dataset.cat;
        tabs.querySelectorAll(".cat-tab").forEach(x => x.classList.toggle("active", x.dataset.cat === Store.activeCat));
        Products.render();
      });
      tabs.appendChild(t);
    });
    tabs.querySelector("[data-cat='all']").addEventListener("click", () => {
      Store.activeCat = "all";
      tabs.querySelectorAll(".cat-tab").forEach(x => x.classList.toggle("active", x.dataset.cat === "all"));
      Products.render();
    });
  },

  populateCatSelect(selectedId) {
    const sel = $("pf-cat");
    sel.innerHTML = Store.categories.map(c =>
      `<option value="${c.id}" ${String(c.id)===String(selectedId)?"selected":""}>${c.icon} ${c.name}</option>`
    ).join("");
  },

  openNew() {
    $("mp-title").textContent = "Novo Produto";
    $("product-form").reset();
    $("pf-id").value = "";
    this.populateCatSelect(null);
    $("pf-margin").classList.add("hidden");
    $("pf-error").classList.add("hidden");
    Modals.open("modal-product");
  },

  openEdit(id) {
    const p = Store.products.find(x => x.id === id);
    if (!p) return;
    $("mp-title").textContent  = "Editar Produto";
    $("pf-id").value           = p.id;
    $("pf-name").value         = p.name;
    $("pf-price").value        = p.price;
    $("pf-cost").value         = p.cost;
    $("pf-stock").value        = p.stock;
    $("pf-minstk").value       = p.min_stock;
    this.populateCatSelect(p.category_id);
    Products.updateMarginPreview();
    $("pf-error").classList.add("hidden");
    Modals.open("modal-product");
  },

  updateMarginPreview() {
    const price = parseFloat($("pf-price").value) || 0;
    const cost  = parseFloat($("pf-cost").value)  || 0;
    if (price > 0) {
      const pct = ((price - cost) / price * 100).toFixed(1);
      $("pf-margin-val").textContent = `${pct}% (${fmt(price - cost)})`;
      $("pf-margin").classList.remove("hidden");
    } else {
      $("pf-margin").classList.add("hidden");
    }
  },

  async save(e) {
    e.preventDefault();
    const errEl = $("pf-error");
    const btn   = $("btn-save-product");
    errEl.classList.add("hidden");
    const id    = $("pf-id").value;
    const name  = $("pf-name").value.trim();
    const price = parseFloat($("pf-price").value);
    const cost  = parseFloat($("pf-cost").value)  || 0;
    const stock = parseInt($("pf-stock").value)   || 0;
    const min_s = parseInt($("pf-minstk").value)  || 5;
    const cat   = $("pf-cat").value;
    if (!name || isNaN(price) || price < 0) {
      errEl.textContent = "Informe nome e preço válidos.";
      errEl.classList.remove("hidden"); return;
    }
    btn.disabled = true; btn.textContent = "Salvando…";
    try {
      const body = { name, price, cost, stock, min_stock: min_s, category_id: cat };
      if (id) await API.updateProduct(Number(id), body);
      else    await API.createProduct(body);
      toast(id ? "Produto atualizado! ✅" : "Produto criado! ✅", "success");
      Modals.close("modal-product");
      await Products.load();
    } catch(err) {
      errEl.textContent = err.message; errEl.classList.remove("hidden");
    } finally { btn.disabled = false; btn.textContent = "Salvar"; }
  },

  confirmDelete(id, name) {
    _deleteId = id;
    $("confirm-msg").textContent = `Excluir permanentemente "${name}"? Esta ação não pode ser desfeita.`;
    _deleteConfirmFn = async () => {
      const btn = $("btn-confirm-ok");
      btn.disabled = true; btn.textContent = "Excluindo…";
      try {
        await API.deleteProduct(id);
        toast("Produto excluído.", "success");
        Modals.close("modal-confirm");
        await Products.load();
      } catch(err) { toast("Erro: " + err.message, "error"); }
      finally { btn.disabled = false; btn.textContent = "Excluir"; }
    };
    Modals.open("modal-confirm");
  },

  init() {
    $("product-form").addEventListener("submit", Products.save.bind(Products));
    $("btn-new-product").addEventListener("click", () => Products.openNew());
    $("btn-header-action").addEventListener("click", () => {
      if (Router.current === "products") Products.openNew();
      if (Router.current === "sales") Sales.openNew();
    });
    $("product-search").addEventListener("input", e => {
      Store.searchQ = e.target.value;
      Products.render();
    });
    $("btn-grid").addEventListener("click", () => {
      Store.viewMode = "grid";
      $("btn-grid").classList.add("active");
      $("btn-list").classList.remove("active");
      Products.render();
    });
    $("btn-list").addEventListener("click", () => {
      Store.viewMode = "list";
      $("btn-list").classList.add("active");
      $("btn-grid").classList.remove("active");
      Products.render();
    });
    [$("pf-price"), $("pf-cost")].forEach(inp =>
      inp.addEventListener("input", Products.updateMarginPreview));
  }
};

// ═══════════════════════════════════════════════════════
// SALES
// ═══════════════════════════════════════════════════════

const Sales = {
  async load() {
    try {
      [Store.sales, Store.products] = await Promise.all([API.getSales(), Store.products.length ? Promise.resolve(Store.products) : API.getProducts()]);
      if (!Store.sales) return;
      this.renderSummary();
      this.renderTable();
    } catch(err) { toast("Erro ao carregar vendas: " + err.message, "error"); }
  },

  renderSummary() {
    const today = new Date().toISOString().split("T")[0];
    const todaySales = Store.sales.filter(s => s.sold_at && s.sold_at.startsWith(today));
    $("stat-today").textContent     = todaySales.length;
    $("stat-rev-today").textContent = fmt(todaySales.reduce((a,s) => a + s.total, 0));
    $("stat-total").textContent     = fmt(Store.sales.reduce((a,s) => a + s.total, 0));
  },

  renderTable() {
    const tbody = $("sales-tbody");
    if (!Store.sales.length) {
      tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><span class="empty-ico">🧾</span><p>Nenhuma venda registrada.</p></div></td></tr>`;
      return;
    }
    tbody.innerHTML = Store.sales.map((s, i) => `
      <tr style="animation-delay:${i*0.02}s">
        <td><strong>#${s.id}</strong></td>
        <td>${s.product_name}</td>
        <td>${s.quantity}</td>
        <td>${fmt(s.unit_price)}</td>
        <td><span class="badge b-blue">${fmt(s.total)}</span></td>
        <td class="text-green">${fmt(s.profit ?? 0)}</td>
        <td>${s.seller_name}</td>
        <td>${fmtDate(s.sold_at)}</td>
      </tr>`).join("");
  },

  async openNew(preselectedId = null) {
    if (!Store.products.length) Store.products = await API.getProducts() || [];
    if (!Store.categories.length) Store.categories = await API.getCategories() || [];
    const available = Store.products.filter(p => p.stock > 0);
    const sel = $("sf-product");
    sel.innerHTML = available.length
      ? available.map(p => `<option value="${p.id}" data-price="${p.price}" data-cost="${p.cost}" data-stock="${p.stock}">${p.category_icon||""} ${p.name} — ${fmt(p.price)} (${p.stock} un.)</option>`).join("")
      : `<option disabled>Nenhum produto com estoque</option>`;
    if (!available.length) { toast("Sem produtos com estoque disponível.", "error"); return; }
    if (preselectedId) {
      const opt = sel.querySelector(`option[value="${preselectedId}"]`);
      if (opt) sel.value = preselectedId;
    }
    $("sale-form").reset();
    $("sf-qty").value = 1;
    $("sf-error").classList.add("hidden");
    Sales.updatePreview();
    Modals.open("modal-sale");
  },

  updatePreview() {
    const sel   = $("sf-product");
    const opt   = sel.options[sel.selectedIndex];
    const qty   = parseInt($("sf-qty").value) || 0;
    const prev  = $("sf-preview");
    if (!opt || !opt.value) { prev.classList.add("hidden"); return; }
    const price = parseFloat(opt.dataset.price) || 0;
    const cost  = parseFloat(opt.dataset.cost)  || 0;
    const stock = parseInt(opt.dataset.stock)   || 0;
    const total = price * qty;
    const profit= (price - cost) * qty;
    prev.classList.remove("hidden");
    $("sp-unit").textContent   = fmt(price);
    $("sp-stock").textContent  = stock + " un.";
    $("sp-total").textContent  = fmt(total);
    $("sp-profit").textContent = fmt(profit);
  },

  async saveSale(e) {
    e.preventDefault();
    const errEl = $("sf-error");
    const btn   = $("btn-save-sale");
    errEl.classList.add("hidden");
    const pid = parseInt($("sf-product").value);
    const qty = parseInt($("sf-qty").value);
    if (!pid || qty < 1) {
      errEl.textContent = "Selecione um produto e informe quantidade >= 1.";
      errEl.classList.remove("hidden"); return;
    }
    btn.disabled = true; btn.textContent = "Registrando…";
    try {
      const sale = await API.createSale(pid, qty);
      confetti();
      toast(`Venda registrada! ${fmt(sale.total)} 🎉`, "success");
      Modals.close("modal-sale");
      await Sales.load();
      if (Router.current === "dashboard") await Dashboard.load();
    } catch(err) {
      errEl.textContent = err.message; errEl.classList.remove("hidden");
    } finally { btn.disabled = false; btn.textContent = "Confirmar Venda"; }
  },

  init() {
    $("sale-form").addEventListener("submit", Sales.saveSale.bind(Sales));
    $("btn-new-sale").addEventListener("click", () => Sales.openNew());
    $("sf-product").addEventListener("change", Sales.updatePreview);
    $("sf-qty").addEventListener("input", Sales.updatePreview);
  }
};

// ═══════════════════════════════════════════════════════
// CLOCK
// ═══════════════════════════════════════════════════════

function startClock() {
  const tick = () => {
    const now = new Date();
    const el  = $("header-time");
    if (el) el.textContent = now.toLocaleTimeString("pt-BR");
  };
  tick();
  setInterval(tick, 1000);
}

// ═══════════════════════════════════════════════════════
// TYPING ANIMATION (login)
// ═══════════════════════════════════════════════════════

function startTyping() {
  const texts = ["Gerencie sua loja com inteligência.", "Controle de estoque em tempo real.", "Relatórios, vendas e muito mais."];
  let ti = 0, ci = 0, deleting = false;
  const el = $("login-tagline");
  if (!el) return;
  function tick() {
    const txt = texts[ti];
    if (!deleting) {
      el.textContent = txt.slice(0, ++ci) + "▌";
      if (ci === txt.length) { deleting = true; setTimeout(tick, 1800); return; }
    } else {
      el.textContent = txt.slice(0, --ci) + "▌";
      if (ci === 0) { deleting = false; ti = (ti + 1) % texts.length; }
    }
    setTimeout(tick, deleting ? 40 : 60);
  }
  tick();
}

// ═══════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
  Modals.init();
  Auth.init();
  Router.init();
  Products.init();
  Sales.init();
  startClock();
  startTyping();

  // Confirm delete
  $("btn-confirm-ok").addEventListener("click", () => _deleteConfirmFn && _deleteConfirmFn());

  // Sessão persistente
  if (Store.token && Store.user) {
    Auth.applyUser();
    $("login-screen").classList.add("gone");
    $("app").hidden = false;
    Router.go("dashboard");
  }
});
