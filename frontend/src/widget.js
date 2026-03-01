const DEFAULT_API_URL = `${globalThis.location?.protocol || "http:"}//${globalThis.location?.hostname || "127.0.0.1"}:8000`;
const DEFAULT_API_KEY = "test_api_key_123";

const runtimeConfig = globalThis.SUPPORTFLOW_CONFIG || {};
const ADMIN_MODE = new URLSearchParams(globalThis.location?.search || "").get("mode") === "admin";

let apiUrl = runtimeConfig.apiUrl || DEFAULT_API_URL;
let apiKey = runtimeConfig.apiKey || DEFAULT_API_KEY;

function createIdempotencyKey() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `idem-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function apiCandidates(primaryUrl) {
  const base = (primaryUrl || "").trim().replace(/\/$/, "");
  const candidates = [base];
  if (!base.includes("127.0.0.1")) candidates.push("http://127.0.0.1:8000");
  if (!base.includes("localhost")) candidates.push("http://localhost:8000");
  return Array.from(new Set(candidates)).filter(Boolean);
}

async function fetchAllTickets() {
  const response = await fetch(`${apiUrl}/tickets/`, {
    headers: { "X-API-Key": apiKey },
  });

  if (!response.ok) {
    throw new Error(`Tickets request failed: ${response.status}`);
  }

  return response.json();
}

async function fetchTicketById(ticketId) {
  const response = await fetch(`${apiUrl}/tickets/${ticketId}`, {
    headers: { "X-API-Key": apiKey },
  });
  if (!response.ok) {
    throw new Error(`Ticket detail request failed: ${response.status}`);
  }
  return response.json();
}

async function postAnalyzeWithFallback(message, idempotencyKey) {
  const candidates = apiCandidates(apiUrl);
  let lastError = null;

  for (const candidate of candidates) {
    try {
      const response = await fetch(`${candidate}/analyze/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": apiKey,
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Istek hatasi (${response.status}): ${detail}`);
      }

      apiUrl = candidate;
      return response.json();
    } catch (error) {
      lastError = error;
      const raw = String(error?.message || "");
      if (!raw.includes("Failed to fetch")) {
        throw error;
      }
    }
  }

  throw lastError || new Error("Failed to fetch");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderMetrics(tickets) {
  if (!tickets.length) {
    return `<div class="sf-muted">Henuz ticket yok.</div>`;
  }

  const total = tickets.length;
  const p1 = tickets.filter((t) => t.priority === 1).length;
  const p2 = tickets.filter((t) => t.priority === 2).length;
  const p3 = tickets.filter((t) => t.priority === 3).length;
  const p4 = tickets.filter((t) => t.priority === 4).length;

  return `
    <div class="sf-metrics">
      <div><span>Toplam</span><strong>${total}</strong></div>
      <div><span>P1</span><strong>${p1}</strong></div>
      <div><span>P2</span><strong>${p2}</strong></div>
      <div><span>P3</span><strong>${p3}</strong></div>
      <div><span>P4</span><strong>${p4}</strong></div>
    </div>
  `;
}

function renderTicketsTable(tickets) {
  if (!tickets.length) {
    return `<p class="sf-muted">Henuz gosterilecek ticket yok.</p>`;
  }

  const rows = tickets.slice(0, 100).map((ticket) => `
      <tr>
        <td>${ticket.id ?? "-"}</td>
        <td>${escapeHtml(ticket.category ?? "-")}</td>
        <td>${escapeHtml(ticket.urgency ?? "-")}</td>
        <td>${ticket.priority ?? "-"}</td>
        <td>${typeof ticket.confidence === "number" ? ticket.confidence.toFixed(3) : "-"}</td>
        <td>${escapeHtml((ticket.message || "").slice(0, 80))}</td>
      </tr>
    `).join("");

  return `
    <div class="sf-table-wrap">
      <table class="sf-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Category</th>
            <th>Urgency</th>
            <th>Priority</th>
            <th>Confidence</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function renderResult(state) {
  if (state.error) {
    return `<div class="sf-error">${state.error}</div>`;
  }

  if (!state.ticket) {
    return `<p class="sf-muted">Mesajinizi yazip gonderebilirsiniz.</p>`;
  }

  return `
    <div class="sf-success">Mesajiniz alindi. Destek ekibimiz en kisa surede donus yapacak.</div>
    ${state.warning ? `<div class="sf-muted" style="margin-top:8px;">${state.warning}</div>` : ""}
    ${ADMIN_MODE ? `
      <div class="sf-admin-card">
        <h3>Son Mesaj Sonucu</h3>
        <div class="sf-result-grid">
          <div><span>Status</span><strong>${state.ticket.status ?? "processed"}</strong></div>
          <div><span>Ticket ID</span><strong>${state.ticket.id}</strong></div>
          <div><span>Category</span><strong>${state.ticket.category ?? "-"}</strong></div>
          <div><span>Urgency</span><strong>${state.ticket.urgency ?? "-"}</strong></div>
          <div><span>Priority</span><strong>${state.ticket.priority ?? "-"}</strong></div>
          <div><span>Confidence</span><strong>${state.ticket.confidence?.toFixed?.(3) ?? "-"}</strong></div>
        </div>
      </div>
    ` : ""}
  `;
}

function adminPanelTemplate() {
  if (!ADMIN_MODE) return "";

  return `
    <div class="sf-grid-two">
      <div class="sf-field">
        <label for="sf-api-url">API URL</label>
        <input id="sf-api-url" class="sf-input" value="${apiUrl}" />
      </div>
      <div class="sf-field">
        <label for="sf-api-key">X-API-Key</label>
        <input id="sf-api-key" class="sf-input" value="${apiKey}" />
      </div>
    </div>
  `;
}

function adminSectionTemplate() {
  if (!ADMIN_MODE) return "";

  return `
    <section class="sf-admin-panel">
      <div class="sf-admin-header">
        <h2>Admin Panel</h2>
        <button id="sf-refresh" class="sf-secondary" type="button">Listeyi Yenile</button>
      </div>
      <div id="sf-admin-metrics"></div>
      <div id="sf-admin-list" style="margin-top:12px;"></div>
    </section>
  `;
}

export function mountWidget(root) {
  if (!root) return;

  const state = {
    loading: false,
    error: "",
    warning: "",
    ticket: null,
    tickets: [],
  };

  root.innerHTML = `
    <style>
      body {
        margin: 0;
        font-family: "Segoe UI", "Helvetica Neue", sans-serif;
        background: linear-gradient(140deg, #f4f7f8, #eef3ff);
      }
      .sf-wrap {
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 20px;
      }
      .sf-card {
        width: min(980px, 100%);
        background: #ffffff;
        border: 1px solid #dde5ee;
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 18px 50px rgba(12, 25, 44, 0.08);
      }
      .sf-title { margin: 0 0 8px; font-size: 22px; }
      .sf-sub { margin: 0 0 16px; color: #506275; font-size: 14px; }
      .sf-grid { display: grid; gap: 12px; }
      .sf-grid-two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
      .sf-field { display: grid; gap: 6px; }
      .sf-field label { font-size: 13px; color: #42586d; }
      .sf-input, .sf-textarea { border: 1px solid #c8d5e2; border-radius: 10px; padding: 10px 12px; font-size: 14px; }
      .sf-textarea { min-height: 130px; resize: vertical; }
      .sf-button { border: 0; border-radius: 10px; padding: 12px; background: #0f4475; color: #fff; font-size: 15px; font-weight: 700; cursor: pointer; }
      .sf-button:disabled { opacity: 0.6; cursor: not-allowed; }
      .sf-secondary { border: 1px solid #0f4475; border-radius: 8px; background: #fff; color: #0f4475; padding: 8px 12px; cursor: pointer; font-weight: 600; }
      .sf-result { margin-top: 16px; border: 1px solid #dce6f1; border-radius: 12px; padding: 14px; background: #f8fbff; }
      .sf-success { color: #0b5a2e; font-weight: 600; }
      .sf-error { color: #a02c2c; font-weight: 600; }
      .sf-muted { margin: 0; color: #5f7488; }
      .sf-admin-card { margin-top: 12px; border-top: 1px solid #d2dfec; padding-top: 12px; }
      .sf-admin-card h3 { margin: 0 0 10px; font-size: 14px; }
      .sf-result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
      .sf-result-grid span { display: block; font-size: 12px; color: #5d7184; }
      .sf-result-grid strong { font-size: 14px; }
      .sf-admin-panel { margin-top: 18px; border-top: 1px solid #e1e7ef; padding-top: 16px; }
      .sf-admin-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
      .sf-admin-header h2 { margin: 0; font-size: 18px; }
      .sf-metrics { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-top: 12px; }
      .sf-metrics > div { background: #f3f8ff; border: 1px solid #dbe7f5; border-radius: 10px; padding: 10px; }
      .sf-metrics span { display: block; font-size: 12px; color: #4a6177; }
      .sf-metrics strong { font-size: 16px; }
      .sf-table-wrap { overflow: auto; border: 1px solid #dce6f1; border-radius: 10px; }
      .sf-table { width: 100%; border-collapse: collapse; min-width: 760px; }
      .sf-table th, .sf-table td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #e6edf5; font-size: 13px; }
      .sf-table th { background: #f5f9ff; font-weight: 700; }
      @media (max-width: 900px) {
        .sf-grid-two, .sf-result-grid, .sf-metrics { grid-template-columns: 1fr; }
      }
    </style>

    <div class="sf-wrap">
      <div class="sf-card">
        <h1 class="sf-title">${ADMIN_MODE ? "SupportFlow Admin + Widget" : "Bize Mesaj Gonderin"}</h1>
        <p class="sf-sub">${ADMIN_MODE ? "Mesaj gonderebilir ve ticket listesini yonetebilirsiniz." : "Yazdiginiz sorun destek ekibine iletilecektir."}</p>

        <form id="sf-form" class="sf-grid" autocomplete="off">
          ${adminPanelTemplate()}

          <div class="sf-field">
            <label for="sf-message">Mesajiniz</label>
            <textarea id="sf-message" class="sf-textarea" required placeholder="Sorununuzu buraya yazin..."></textarea>
          </div>

          <button id="sf-submit" class="sf-button" type="submit">${ADMIN_MODE ? "Ticket Olustur" : "Gonder"}</button>
        </form>

        <div id="sf-result" class="sf-result"></div>
        ${adminSectionTemplate()}
      </div>
    </div>
  `;

  const form = root.querySelector("#sf-form");
  const resultNode = root.querySelector("#sf-result");
  const submitNode = root.querySelector("#sf-submit");
  const refreshNode = root.querySelector("#sf-refresh");
  const metricsNode = root.querySelector("#sf-admin-metrics");
  const listNode = root.querySelector("#sf-admin-list");

  async function refreshAdminData() {
    if (!ADMIN_MODE) return;
    try {
      const allTickets = await fetchAllTickets();
      // Backend already returns newest-first; keep that order in admin table.
      state.tickets = allTickets;
      metricsNode.innerHTML = renderMetrics(allTickets);
      listNode.innerHTML = renderTicketsTable(allTickets);
    } catch (error) {
      metricsNode.innerHTML = "";
      listNode.innerHTML = `<div class="sf-error">Liste alinamadi: ${escapeHtml(error.message || "hata")}</div>`;
    }
  }

  function syncView() {
    submitNode.disabled = state.loading;
    submitNode.textContent = state.loading ? (ADMIN_MODE ? "Olusturuluyor..." : "Gonderiliyor...") : (ADMIN_MODE ? "Ticket Olustur" : "Gonder");
    resultNode.innerHTML = renderResult(state);
  }

  syncView();
  refreshAdminData();

  if (refreshNode) {
    refreshNode.addEventListener("click", async () => {
      if (ADMIN_MODE) {
        apiUrl = root.querySelector("#sf-api-url").value.trim().replace(/\/$/, "");
        apiKey = root.querySelector("#sf-api-key").value.trim();
      }
      await refreshAdminData();
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = root.querySelector("#sf-message").value.trim();

    if (ADMIN_MODE) {
      apiUrl = root.querySelector("#sf-api-url").value.trim().replace(/\/$/, "");
      apiKey = root.querySelector("#sf-api-key").value.trim();
    }

    if (!apiUrl || !apiKey || !message) {
      state.error = "Mesaj gonderilemedi. Lutfen tum gerekli alanlari doldurun.";
      state.ticket = null;
      syncView();
      return;
    }

    state.loading = true;
    state.error = "";
    state.warning = "";
    syncView();

    try {
      const idempotencyKey = createIdempotencyKey();
      const analyzeData = await postAnalyzeWithFallback(message, idempotencyKey);
      state.ticket = {
        status: analyzeData.status,
        id: analyzeData.ticket_id,
        category: undefined,
        urgency: undefined,
        priority: undefined,
        confidence: undefined,
      };

      let ticket = null;
      try {
        ticket = await fetchTicketById(analyzeData.ticket_id);
      } catch (detailError) {
        if (ADMIN_MODE) {
          state.warning = `Detay alanlari getirilemedi: ${String(detailError?.message || detailError)}`;
        }
      }

      state.ticket = {
        status: analyzeData.status,
        id: analyzeData.ticket_id,
        category: ticket?.category,
        urgency: ticket?.urgency,
        priority: ticket?.priority,
        confidence: ticket?.confidence,
      };
      state.error = "";
      root.querySelector("#sf-message").value = "";

      if (ADMIN_MODE) {
        await refreshAdminData();
      }
    } catch (error) {
      state.ticket = null;
      const raw = String(error?.message || "");
      if (raw.includes("Failed to fetch")) {
        state.error = ADMIN_MODE
          ? `Sunucuya baglanilamadi (${apiUrl}). Backend/port erisimi kontrol et.`
          : "Mesajiniz su an iletilemedi. Lutfen birazdan tekrar deneyin.";
      } else {
        state.error = ADMIN_MODE
          ? (raw || "Beklenmeyen bir hata olustu.")
          : "Islem sirasinda bir sorun olustu. Lutfen tekrar deneyin.";
      }
    } finally {
      state.loading = false;
      syncView();
    }
  });
}
