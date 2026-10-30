/* JOBHUNT AI - client-side logic */
"use strict";

const state = { userId: null, config: null, users: [] };

/* ---------- helpers ---------- */
async function api(path, options = {}) {
    const opts = { method: options.method || "GET", headers: {} };
    if (options.body !== undefined) {
        if (options.formData) {
            opts.body = options.body;
        } else {
            opts.headers["Content-Type"] = "application/json";
            opts.body = JSON.stringify(options.body);
        }
    }
    if (options.headers) Object.assign(opts.headers, options.headers);
    const res = await fetch(path, opts);
    let data = null;
    try { data = await res.json(); } catch (_) { /* non-JSON */ }
    if (!res.ok) {
        const detail = (data && data.detail) || ("HTTP " + res.status);
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return data;
}

function notice(msg, type = "info", ms = 8000) {
    const box = document.getElementById("noticeBox");
    box.innerHTML = `<div class="notice ${type}">${escapeHtml(msg)}</div>`;
    clearTimeout(notice._t);
    if (ms) notice._t = setTimeout(() => { box.innerHTML = ""; }, ms);
}

function escapeHtml(str) {
    return String(str ?? "").replace(/[&<>"']/g, (c) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
}

function fmtSalary(min, max, currency) {
    if (min == null && max == null) return "—";
    const cur = currency || "PHP";
    const sym = cur === "PHP" ? "₱" : (cur === "USD" ? "$" : cur + " ");
    const p = (v) => v == null ? "" : sym + Number(v).toLocaleString("en-US");
    if (min != null && max != null) return `${p(min)}–${p(max)}`;
    return p(min ?? max) + (min != null ? "+" : "");
}

function fmtDate(v) {
    if (!v) return "—";
    const d = new Date(v);
    return isNaN(d) ? String(v).slice(0, 10) : d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function scoreBadge(score) {
    if (score == null) return '<span class="badge muted">unscored</span>';
    const cls = score >= 75 ? "success" : score >= 60 ? "warning" : "danger";
    return `<span class="badge ${cls}">${Math.round(score)}%</span>`;
}

function statusBadge(status) {
    const map = {
        discovered: "info", answers_generated: "info", ready_for_review: "warning",
        submitted: "success", rejected: "danger", interviewing: "warning", offer: "success",
    };
    return `<span class="badge ${map[status] || "muted"}">${escapeHtml(status || "—")}</span>`;
}

async function requireUser() {
    if (state.userId) return state.userId;
    const users = await api("/api/users/");
    if (users.total > 0) {
        state.userId = users.items[0].id;
        state.users = users.items;
        return state.userId;
    }
    throw new Error("Create a profile first (Profile tab).");
}

/* ---------- tabs ---------- */
function showTab(tab) {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.toggle("active", p.id === "tab-" + tab));
}

/* ---------- config / AI banner ---------- */
async function loadConfig() {
    state.config = await api("/api/config");
    const ai = state.config.ai || {};
    const banner = document.getElementById("aiBanner");
    if (!ai.enabled) {
        banner.classList.remove("hidden");
        banner.innerHTML =
            '<strong>⚠ AI is running in "local fallback" mode.</strong> ' +
            "No <code>OPENROUTER_API_KEY</code> is configured yet, so answers use truthful offline templates. " +
            'Add a free key (see <code>API_KEYS.md</code>) and restart to enable AI-generated answers &amp; resume parsing. ' +
            "<a href='https://openrouter.ai/keys' target='_blank' rel='noopener'>Get a free key →</a>";
    } else {
        banner.classList.add("hidden");
    }
    document.getElementById("aiFooterBadge").textContent =
        ai.enabled ? `✨ ${ai.model}` : "✨ local fallback (add free OpenRouter key) ";

    // Populate search sources multi-select
    const sel = document.getElementById("searchSources");
    sel.innerHTML = "";
    (state.config.enabled_sources || ["indeed", "jobstreet", "kalibrr"]).forEach((s) => {
        const opt = document.createElement("option");
        opt.value = s;
        opt.text = s[0].toUpperCase() + s.slice(1);
        opt.selected = true;
        sel.appendChild(opt);
    });

    // Seed the settings form from global config
    const s = state.config;
    document.getElementById("sCountry").value = s.country || "Philippines";
    document.getElementById("sMinSalary").value = s.minimum_salary || 25000;
    document.getElementById("sDailyTarget").value = s.daily_target || 50;
    document.getElementById("sSources").value = (s.enabled_sources || []).join(",");
    document.getElementById("sRemote").checked = !!s.allow_remote;
    document.getElementById("sFresh").checked = !!s.allow_fresh_graduate;
    document.getElementById("sExcluded").value = (s.excluded_categories || []).join(",");
}
/* ---------- Dashboard ---------- */
async function loadStats() {
    try {
        const st = await api("/api/stats");
        const grid = document.getElementById("statsGrid");
        const apps = st.applications || {};
        const byStatus = apps.by_status || {};
        const cards = [
            { label: "Jobs Found", value: st.jobs.total, icon: "🔎" },
            { label: "Active Jobs", value: st.jobs.active, icon: "✅" },
            { label: "Filtered Out", value: st.jobs.filtered, icon: "🚫" },
            { label: "Strong Matches (≥75%)", value: apps.strong_matches || 0, icon: "💪" },
            { label: "Applications", value: apps.total || 0, icon: "📧" },
            { label: "Submitted", value: byStatus.submitted || 0, icon: "🚀" },
            { label: "Interviews", value: (byStatus.interviewing || 0) + (byStatus.offer || 0), icon: "🎯" },
            { label: "Resumes", value: st.resumes || 0, icon: "📄" },
        ];
        grid.innerHTML = cards.map((c) => `
            <div class="stat-card">
                <div class="stat-icon">${c.icon}</div>
                <div class="stat-value">${c.value}</div>
                <div class="stat-label">${c.label}</div>
            </div>`).join("");

        // Recent searches
        const rs = document.getElementById("recentSearches");
        if ((st.recent_searches || []).length === 0) {
            rs.innerHTML = '<p class="muted">No searches yet.</p>';
        } else {
            rs.innerHTML = "<ul class='mini-list'>" + st.recent_searches.slice(0, 5).map((r) => `
                <li><strong>${escapeHtml(r.query || "—")}</strong>
                    <span class="muted">${(r.sources || []).join(", ")} · found ${r.found}</span>
                    ${statusBadge(r.status)}</li>`).join("") + "</ul>";
        }

        // Recent jobs
        const rj = document.getElementById("recentJobs");
        if ((st.recent_jobs || []).length === 0) {
            rj.innerHTML = '<p class="muted">No jobs yet. Run a search in the Jobs tab.</p>';
        } else {
            rj.innerHTML = "<ul class='mini-list'>" + st.recent_jobs.slice(0, 5).map((j) => `
                <li><strong>${escapeHtml(j.title)}</strong> @ ${escapeHtml(j.company)}
                <span class="muted">${fmtSalary(j.salary_min, j.salary_max)} · ${escapeHtml(j.location || "Remote")}</span>
                ${j.is_filtered_out ? '<span class="badge danger">filtered</span>' : ""}</li>`).join("") + "</ul>";
        }
    } catch (e) {
        notice("Could not load stats: " + e.message, "error");
    }
}

/* ---------- Profile ---------- */
async function loadUsers() {
    const data = await api("/api/users/");
    state.users = data.items || [];
    const sel = document.getElementById("userSelect");
    sel.innerHTML = '<option value="">-- choose a profile --</option>' +
        state.users.map((u) => `<option value="${u.id}">${escapeHtml(u.name)} (${escapeHtml(u.email)})</option>`).join("");
    if (!state.userId && state.users.length > 0) state.userId = state.users[0].id;
    refreshProfileDetails();
}

async function refreshProfileDetails() {
    const box = document.getElementById("profileDetails");
    if (!state.userId) { box.classList.add("hidden"); return; }
    try {
        const u = await api(`/api/users/${state.userId}`);
        box.classList.remove("hidden");
        box.innerHTML = `
            <h3>Active profile</h3>
            <p><strong>${escapeHtml(u.name)}</strong> · ${escapeHtml(u.email)}
            ${u.phone ? "· " + escapeHtml(u.phone) : ""}
            ${u.location ? "· " + escapeHtml(u.location) : ""}
            · ${u.is_fresh_graduate ? "<span class='badge info'>Fresh graduate</span>" : "<span class='badge success'>Experienced</span>"}</p>`;
    } catch (e) {
        box.classList.add("hidden");
    }
}

async function createProfile(e) {
    e.preventDefault();
    const body = {
        name: document.getElementById("pName").value.trim(),
        email: document.getElementById("pEmail").value.trim(),
        phone: document.getElementById("pPhone").value.trim() || null,
        location: document.getElementById("pLocation").value.trim() || null,
        is_fresh_graduate: document.getElementById("pFresh").checked,
    };
    try {
        const user = await api("/api/users/", { method: "POST", body });
        state.userId = user.id;
        document.getElementById("profileForm").reset();
        notice("Profile created! Now upload your resume.", "success");
        await loadUsers();
        await loadStats();
    } catch (err) {
        notice(err.message, "error");
    }
/* ---------- Resume ---------- */
async function loadResumes() {
    if (!state.userId) { document.getElementById("resumeList").innerHTML = '<p class="muted">No profile selected.</p>'; return; }
    try {
        const data = await api(`/api/resumes/user/${state.userId}`);
        const list = document.getElementById("resumeList");
        if (data.total === 0) {
            list.innerHTML = '<p class="muted">No resumes uploaded yet.</p>';
            return;
        }
        list.innerHTML = "<ul class='mini-list'>" + data.items.map((r) => {
            const ver = r.is_verified === "verified" ? '<span class="badge success">verified</span>'
                : r.is_verified === "rejected" ? '<span class="badge danger">rejected</span>'
                : '<span class="badge warning">pending</span>';
            return `<li>
                <strong>${escapeHtml(r.filename)}</strong> ${ver}
                <span class="actions">
                    <button class="btn tiny" data-resume-extract="${r.id}">Extract</button>
                    <button class="btn tiny secondary" data-resume-view="${r.id}">View</button>
                    <button class="btn tiny success" data-resume-verify="${r.id}:verified">Verify</button>
                    <button class="btn tiny danger" data-resume-verify="${r.id}:rejected">Reject</button>
                </span>
            </li>`;
        }).join("") + "</ul>";
        document.querySelectorAll("[data-resume-extract]").forEach((b) => b.addEventListener("click", () => extractResume(b.dataset.resumeExtract)));
        document.querySelectorAll("[data-resume-view]").forEach((b) => b.addEventListener("click", () => viewResume(b.dataset.resumeView)));
        document.querySelectorAll("[data-resume-verify]").forEach((b) => {
            const [id, v] = b.dataset.resumeVerify.split(":");
            b.addEventListener("click", () => verifyResume(id, v));
        });
    } catch (e) { notice(e.message, "error"); }
}

async function uploadResume(e) {
    e.preventDefault();
    const uid = await requireUser().catch(() => { notice("Create a profile first.", "error"); return null; });
    if (!uid) return;
    const fileInput = document.getElementById("resumeFile");
    if (!fileInput.files.length) { notice("Choose a file first.", "error"); return; }
    const fd = new FormData();
    fd.append("file", fileInput.files[0]);
    try {
        await api(`/api/resumes/upload/${uid}`, { method: "POST", body: fd, formData: true });
        notice("Resume uploaded. Now click Extract to pull details.", "success");
        fileInput.value = "";
        await loadResumes();
        await loadStats();
    } catch (err) { notice("Upload failed: " + err.message, "error"); }
}

async function extractResume(id) {
    try {
        const res = await api(`/api/resumes/${id}/extract`, { method: "POST" });
        const box = document.getElementById("resumeDetail");
        box.classList.remove("hidden");
        box.innerHTML = `<h3>Extracted information</h3>
            ${sectionList("Education", res.education)}
            ${sectionList("Experience", res.experience)}
            ${sectionList("Skills", res.skills)}
            ${sectionList("Certifications", res.certifications)}
            ${sectionList("Projects", res.projects)}
            <p class="muted">Review the details above, then press Verify in the list.</p>`;
        notice("Resume extracted. Review and verify.", "success");
        await loadResumes();
    } catch (e) { notice("Extract failed: " + e.message, "error"); }
}

function sectionList(title, list) {
    const items = Array.isArray(list) ? list : [];
    if (items.length === 0) return "";
    return `<h4>${escapeHtml(title)}</h4><ul>${items.slice(0, 12).map((s) => `<li>${escapeHtml(s)}</li>`).join("")}</ul>`;
}

async function viewResume(id) {
    try {
        const r = await api(`/api/resumes/${id}`);
        const box = document.getElementById("resumeDetail");
        box.classList.remove("hidden");
        box.innerHTML = `<h3>${escapeHtml(r.filename)}</h3>
            <pre class="code-block">${escapeHtml((r.raw_text || "No extracted text.").slice(0, 4000))}</pre>`;
    } catch (e) { notice(e.message, "error"); }
}

async function verifyResume(id, verdict) {
    try {
        await api(`/api/resumes/${id}/verify`, {
            method: "POST",
            body: { is_verified: verdict, verification_notes: "Verified via dashboard" },
        });
        notice(`Resume marked ${verdict}.`, "success");
        await loadResumes();
    } catch (e) { notice(e.message, "error"); }
}
/* ---------- Settings ---------- */
async function loadSettings() {
    if (!state.userId) return;
    try {
        const s = await api(`/api/settings/${state.userId}`);
        document.getElementById("sCountry").value = s.target_countries || "Philippines";
        document.getElementById("sMinSalary").value = s.minimum_salary ?? 25000;
        document.getElementById("sDailyTarget").value = s.daily_application_target ?? 50;
        document.getElementById("sSources").value = s.enabled_sources || "indeed,jobstreet,kalibrr";
        document.getElementById("sRemote").checked = !!s.allow_remote;
        document.getElementById("sFresh").checked = !!s.allow_fresh_graduate;
        document.getElementById("sExcluded").value = s.excluded_job_categories || "";
    } catch (_) { /* server creates defaults; forms already seeded from config */ }
}

async function saveSettings(e) {
    e.preventDefault();
    const uid = await requireUser().catch(() => { notice("Create a profile first.", "error"); return null; });
    if (!uid) return;
    const body = {
        target_countries: document.getElementById("sCountry").value.trim(),
        minimum_salary: parseInt(document.getElementById("sMinSalary").value, 10),
        daily_application_target: parseInt(document.getElementById("sDailyTarget").value, 10),
        enabled_sources: document.getElementById("sSources").value.trim(),
        allow_remote: document.getElementById("sRemote").checked,
        allow_fresh_graduate: document.getElementById("sFresh").checked,
        excluded_job_categories: document.getElementById("sExcluded").value.trim(),
    };
    try {
        await api(`/api/settings/${uid}`, { method: "PUT", body });
        notice("Settings saved.", "success");
    } catch (err) { notice("Could not save settings: " + err.message, "error"); }
}

/* ---------- Jobs & Search ---------- */
async function loadJobs() {
    try {
        const data = await api("/api/search/jobs?limit=100");
        document.getElementById("jobCount").textContent = data.total;
        const body = document.getElementById("jobsBody");
        if (!data.items.length) {
            body.innerHTML = '<tr><td colspan="6" class="muted">No jobs found. Run a search above.</td></tr>';
            return;
        }
        body.innerHTML = data.items.map((j) => `
            <tr>
                <td><strong>${escapeHtml(j.title)}</strong>
                    <div class="muted small">${escapeHtml((j.description || "").slice(0, 80))}…</div></td>
                <td>${escapeHtml(j.company)}</td>
                <td>${escapeHtml(j.location || "Remote")} ${j.is_remote ? '<span class="badge success">remote</span>' : ""}</td>
                <td>${fmtSalary(j.salary_min, j.salary_max, j.salary_currency)}</td>
                <td>${escapeHtml(j.source || "—")}</td>
                <td class="actions">
                    <button class="btn tiny" data-score="${j.id}">Score &amp; Apply</button>
                    ${j.source_url ? `<a class="btn tiny secondary" href="${escapeHtml(j.source_url)}" target="_blank" rel="noopener">Open</a>` : ""}
                </td>
            </tr>`).join("");
        document.querySelectorAll("[data-score]").forEach((b) => b.addEventListener("click", () => scoreJob(b.dataset.score)));
    } catch (e) { notice("Could not load jobs: " + e.message, "error"); }
}

async function runSearch(e) {
    e.preventDefault();
    const uid = await requireUser().catch(() => { notice("Create a profile first.", "error"); return null; });
    if (!uid) return;
    const query = document.getElementById("searchQuery").value.trim();
    const sel = document.getElementById("searchSources");
    const sources = Array.from(sel.selectedOptions).map((o) => o.value);
    const statusEl = document.getElementById("searchStatus");
    statusEl.innerHTML = '<p class="notice info">🔍 Searching… this may take a few seconds.</p>';
    try {
        const params = new URLSearchParams({ user_id: uid, query, location: "Philippines" });
        sources.forEach((s) => params.append("sources", s));
        const res = await api("/api/search/jobs?" + params.toString(), { method: "POST" });
        notice(`Search complete: ${res.jobs_created} new, ${res.jobs_duplicates} duplicates, ${res.jobs_filtered} filtered out.`, "success", 10000);
        statusEl.innerHTML = "";
        await loadStats();
        await loadJobs();
    } catch (err) {
        statusEl.innerHTML = `<div class="notice error">Search failed: ${escapeHtml(err.message)}</div>`;
    }
}

async function scoreJob(jobId) {
    const uid = await requireUser().catch(() => { notice("Create a profile first.", "error"); return null; });
    if (!uid) return;
    try {
        const res = await api(`/api/matching/score/${uid}/${jobId}`, { method: "POST" });
        notice(`Matched! Score: ${res.score}% (${res.decision}) — ${res.explanation}`, "success", 10000);
        await loadApps();
        await loadStats();
    } catch (e) { notice("Scoring failed: " + e.message, "error"); }
}
/* ---------- Applications ---------- */
async function loadApps() {
    if (!state.userId) return;
    try {
        const data = await api(`/api/applications/user/${state.userId}?limit=100`);
        document.getElementById("appCount").textContent = data.total;
        const body = document.getElementById("appsBody");
        if (!data.items.length) {
            body.innerHTML = '<tr><td colspan="4" class="muted">No applications yet. Score a job in the Jobs tab to start.</td></tr>';
            return;
        }
        body.innerHTML = data.items.map((a) => `
            <tr>
                <td><strong>${escapeHtml(a.job_title)}</strong><div class="muted small">${escapeHtml(a.company)}</div>
                    <div class="muted small">${a.matching_explanation ? "🤝 " + escapeHtml(a.matching_explanation) : ""}</div></td>
                <td>${scoreBadge(a.compatibility_score)}</td>
                <td>${statusBadge(a.status)}</td>
                <td class="actions">
                    <button class="btn tiny" data-answers="${a.id}">Answers</button>
                    <button class="btn tiny" data-genanswers="${a.id}">Generate</button>
                    <button class="btn tiny warning" data-prepare="${a.id}">Prepare</button>
                    <button class="btn tiny success" data-submit="${a.id}" ${a.status === "submitted" ? "disabled" : ""}>Mark Submitted</button>
                    <select class="tiny-select" data-status="${a.id}">
                        <option value="">Set status…</option>
                        <option>discovered</option><option>answers_generated</option>
                        <option>ready_for_review</option><option>submitted</option>
                        <option>interviewing</option><option>offer</option><option>rejected</option>
                    </select>
                </td>
            </tr>`).join("");
        document.querySelectorAll("[data-genanswers]").forEach((b) => b.addEventListener("click", () => generateAnswers(b.dataset.genanswers)));
        document.querySelectorAll("[data-prepare]").forEach((b) => b.addEventListener("click", () => prepareApp(b.dataset.prepare)));
        document.querySelectorAll("[data-submit]").forEach((b) => b.addEventListener("click", () => submitApp(b.dataset.submit)));
        document.querySelectorAll("[data-status]").forEach((s) => s.addEventListener("change", () => updateStatus(s.dataset.status, s.value)));
        document.querySelectorAll("[data-answers]").forEach((b) => b.addEventListener("click", () => showAnswers(b.dataset.answers)));
    } catch (e) { notice(e.message, "error"); }
}

async function generateAnswers(appId) {
    try {
        const res = await api(`/api/applications/${appId}/generate-answers`, { method: "POST" });
        notice(res.ai_enabled ? "AI answers generated." : res.hint + " These are offline fallback answers.", res.ai_enabled ? "success" : "warning", 12000);
        await loadApps();
        renderAnswers(res.answers);
    } catch (e) { notice("Generation failed: " + e.message, "error"); }
}

async function prepareApp(appId) {
    try {
        const res = await api(`/api/applications/${appId}/prepare`, { method: "POST" });
        if (res.status === "ready_for_review") {
            notice("Application prepared! Review it in the browser, then mark as submitted after you manually click Submit.", "success", 15000);
        } else {
            notice("Prepare result: " + (res.message || res.status), "warning", 15000);
        }
        await loadApps();
    } catch (e) { notice("Prepare failed: " + e.message, "error"); }
}

async function submitApp(appId) {
    try {
        await api(`/api/applications/${appId}/submit`, { method: "POST" });
        notice("Marked as submitted. Good luck! 🎉", "success");
        await loadApps();
        await loadStats();
    } catch (e) { notice(e.message, "error"); }
}

async function updateStatus(appId, status) {
    if (!status) return;
    try {
        await api(`/api/applications/${appId}`, { method: "PATCH", body: { status } });
        notice(`Application status set to "${status}".`, "success");
        await loadApps();
        await loadStats();
    } catch (e) { notice(e.message, "error"); }
}

async function showAnswers(appId) {
    try {
        const a = await api(`/api/applications/${appId}`);
        if (!a.generated_answers) { notice("No answers generated yet. Click Generate.", "warning"); return; }
        renderAnswers(JSON.parse(a.generated_answers));
    } catch (e) { notice(e.message, "error"); }
}

function renderAnswers(answers) {
    const card = document.getElementById("answersCard");
    const box = document.getElementById("answersContent");
    card.classList.remove("hidden");
    if (!answers || !Object.keys(answers).length) {
        box.innerHTML = '<p class="muted">No answers.</p>';
        return;
    }
    box.innerHTML = Object.entries(answers).map(([q, a]) => `
        <div class="answer-item">
            <p class="q"><strong>Q:</strong> ${escapeHtml(q)}</p>
            <p class="a"><strong>A:</strong> ${escapeHtml(a)}</p>
        </div>`).join("");
}
/* ---------- boot & event wiring ---------- */
document.addEventListener("DOMContentLoaded", async () => {
    // Tab switching
    document.getElementById("navTabs").addEventListener("click", (e) => {
        const btn = e.target.closest(".tab-btn");
        if (btn) showTab(btn.dataset.tab);
    });
    document.querySelectorAll("[data-goto]").forEach((btn) => btn.addEventListener("click", () => showTab(btn.dataset.goto)));

    // Forms
    document.getElementById("profileForm").addEventListener("submit", createProfile);
    document.getElementById("btnUseUser").addEventListener("click", () => {
        const sel = document.getElementById("userSelect");
        if (sel.value) {
            state.userId = sel.value;
            notice("Active profile changed.", "info");
            refreshProfileDetails();
            loadSettings(); loadResumes(); loadJobs(); loadApps();
        }
    });
    document.getElementById("resumeForm").addEventListener("submit", uploadResume);
    document.getElementById("settingsForm").addEventListener("submit", saveSettings);
    document.getElementById("searchForm").addEventListener("submit", runSearch);

    // Reload tab content when opened
    document.querySelectorAll(".tab-btn").forEach((btn) => btn.addEventListener("click", () => {
        const t = btn.dataset.tab;
        if (t === "dashboard") loadStats();
        if (t === "jobs") loadJobs();
        if (t === "applications") loadApps();
        if (t === "resume") loadResumes();
        if (t === "settings") loadSettings();
    }));

    try {
        await loadConfig();
    } catch (e) { notice("Could not load config: " + e.message, "error"); }
    await loadUsers().catch(() => {});
    await loadStats().catch(() => {});
    if (state.userId) { loadSettings(); loadResumes(); loadJobs(); loadApps(); }
});
}