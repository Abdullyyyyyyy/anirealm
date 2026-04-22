function sentimentBadge(label) {
  const cls = label ? label.toLowerCase() : "neutral";
  return `<span class="badge ${cls}">${label || "N/A"}</span>`;
}

function starRating(rating) {
  return "★".repeat(rating) + "☆".repeat(5 - rating);
}


async function refreshHistory() {
  const history = document.getElementById("history");
  if (!history) return;

  const searchTitle = document.getElementById("searchTitle")?.value.trim() || "";
  const filterSentiment = document.getElementById("filterSentiment")?.value || "";

  let url = "/api/journal";
  const params = new URLSearchParams();
  if (searchTitle) params.append("anime_title", searchTitle);
  if (filterSentiment) params.append("vader_label", filterSentiment);
  if (params.toString()) url += "?" + params.toString();

  try {
    const res = await fetch(url);
    const data = await res.json();

    history.innerHTML = "";

    if (data.length === 0) {
      history.innerHTML = `
        <div style="text-align:center; padding:40px; color:#888;">
          <div style="font-size:3rem; margin-bottom:12px;">📓</div>
          <p>No journal entries found. <a href="/journal" style="color:#764ba2; font-weight:700;">Write your first entry!</a></p>
        </div>`;
      return;
    }

    data.forEach(entry => {
      const card = document.createElement("div");
      card.className = "entry-card";
      card.innerHTML = `
        <h3>${entry.anime_title}</h3>
        <p style="color:#888; font-size:0.85rem; margin-bottom:12px;">
          ${new Date(entry.created_at).toLocaleDateString("en-GB", {
            day: "numeric", month: "short", year: "numeric"
          })}
        </p>
        <p><strong>Episode:</strong> ${entry.episode} &nbsp;
           <strong>Rating:</strong> <span style="color:#f6a623;">${starRating(entry.rating)}</span></p>
        <p style="margin: 10px 0; font-style:italic; color:#555;">"${entry.reflection_text}"</p>
        <div style="display:flex; flex-wrap:wrap; gap:8px; margin:12px 0;">
          <span><strong>VADER:</strong> ${sentimentBadge(entry.vader_label)}</span>
          <span><strong>TextBlob:</strong> ${sentimentBadge(entry.textblob_label)}</span>
          <span><strong>BERT:</strong> ${sentimentBadge(entry.transformer_label)}</span>
        </div>
        ${entry.true_label ? `<p><strong>True Label:</strong> ${sentimentBadge(entry.true_label)}</p>` : ""}
        <button class="danger" onclick="deleteJournal(${entry.id})"
          style="margin-top:12px; font-size:0.85rem; padding:8px 16px;">
          Delete
        </button>
      `;
      history.appendChild(card);
    });

  } catch (error) {
    history.innerHTML = "<p style='color:red;'>Failed to load journal history.</p>";
  }
}


async function deleteJournal(id) {
  if (!confirm("Are you sure you want to delete this entry?")) return;

  try {
    await fetch(`/api/journal/${id}`, { method: "DELETE" });
    refreshHistory();
    loadComparison();
  } catch (error) {
    alert("Failed to delete entry.");
  }
}


async function loadComparison() {
  const list = document.getElementById("comparisonList");
  if (!list) return;

  try {
    const res = await fetch("/api/journal");
    const data = await res.json();

    if (data.length === 0) {
      list.innerHTML = `
        <div style="text-align:center; padding:40px; color:#888;">
          <div style="font-size:3rem; margin-bottom:12px;">🤖</div>
          <p>No entries yet. <a href="/journal" style="color:#764ba2; font-weight:700;">Submit a journal entry</a> to see model comparisons.</p>
        </div>`;
      return;
    }

    list.innerHTML = `
      <table class="comparison-table">
        <thead>
          <tr>
            <th>Anime</th>
            <th>Reflection</th>
            <th>VADER</th>
            <th>TextBlob</th>
            <th>DistilBERT</th>
            <th>Agreement</th>
          </tr>
        </thead>
        <tbody id="comparisonBody"></tbody>
      </table>
    `;

    const tbody = document.getElementById("comparisonBody");

    data.forEach(entry => {
      const allAgree = (
        entry.vader_label === entry.textblob_label &&
        entry.textblob_label === entry.transformer_label
      );

      const row = document.createElement("tr");
      row.innerHTML = `
        <td><strong>${entry.anime_title}</strong><br>
          <span style="color:#888; font-size:0.8rem;">Ep ${entry.episode}</span>
        </td>
        <td style="max-width:200px; font-style:italic; color:#555; font-size:0.85rem;">
          "${entry.reflection_text.slice(0, 80)}${entry.reflection_text.length > 80 ? "..." : ""}"
        </td>
        <td>${sentimentBadge(entry.vader_label)}</td>
        <td>${sentimentBadge(entry.textblob_label)}</td>
        <td>${sentimentBadge(entry.transformer_label)}</td>
        <td>
          ${allAgree
            ? `<span style="color:#1a7a4a; font-weight:700;">✓ Yes</span>`
            : `<span style="color:#c0392b; font-weight:700;">✗ No</span>`
          }
        </td>
      `;
      tbody.appendChild(row);
    });

  } catch (error) {
    list.innerHTML = "<p style='color:red;'>Failed to load comparison data.</p>";
  }
}


async function loadEvaluation() {
  const result = document.getElementById("evaluationResult");
  if (!result) return;

  try {
    const res = await fetch("/api/evaluation");
    const data = await res.json();

    if (data.message) {
      result.innerHTML = `
        <div class="card" style="text-align:center; padding:40px;">
          <div style="font-size:3rem; margin-bottom:12px;">📊</div>
          <p style="color:#888;">${data.message}</p>
          <a href="/journal" style="color:#764ba2; font-weight:700;">
            Submit entries with a true label to generate metrics.
          </a>
        </div>`;
      return;
    }

    function metricCard(modelName, metrics, icon) {
      return `
        <div class="card">
          <h2>${icon} ${modelName}</h2>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-number">${(metrics.accuracy * 100).toFixed(1)}%</div>
              <div class="stat-label">Accuracy</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">${(metrics.precision * 100).toFixed(1)}%</div>
              <div class="stat-label">Precision</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">${(metrics.recall * 100).toFixed(1)}%</div>
              <div class="stat-label">Recall</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">${(metrics.f1_score * 100).toFixed(1)}%</div>
              <div class="stat-label">F1-Score</div>
            </div>
          </div>
        </div>`;
    }

    result.innerHTML = `
      <div class="card" style="background:#f8f0ff; border:none;">
        <p style="color:#764ba2; font-weight:700; text-align:center;">
          Based on ${data.total_labelled_entries} labelled entries
        </p>
      </div>
      ${metricCard("VADER", data.vader, "📏")}
      ${metricCard("TextBlob", data.textblob, "📝")}
      ${metricCard("DistilBERT", data.transformer, "🧠")}
    `;

  } catch (error) {
    result.innerHTML = "<p style='color:red;'>Failed to load evaluation metrics.</p>";
  }
}


if (document.getElementById("refreshBtn")) {
  document.getElementById("refreshBtn").addEventListener("click", refreshHistory);
}
if (document.getElementById("filterBtn")) {
  document.getElementById("filterBtn").addEventListener("click", refreshHistory);
}
if (document.getElementById("loadEvaluationBtn")) {
  document.getElementById("loadEvaluationBtn").addEventListener("click", loadEvaluation);
}

refreshHistory();
loadComparison(); 