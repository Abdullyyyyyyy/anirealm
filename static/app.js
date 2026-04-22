async function submitJournal() {
  const anime_title = document.getElementById("anime_title").value.trim();
  const episode = parseInt(document.getElementById("episode").value, 10);
  const rating = parseInt(document.getElementById("rating").value, 10);
  const reflection_text = document.getElementById("reflection_text").value.trim();
  const true_label = document.getElementById("true_label").value;

  const resultBox = document.getElementById("result");
  resultBox.className = "message-box";
  resultBox.textContent = "Analysing your reflection... please wait.";

  try {
    const res = await fetch("/api/journal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ anime_title, episode, rating, reflection_text, true_label })
    });

    const data = await res.json();

    if (!res.ok) {
      resultBox.className = "message-box error";
      resultBox.textContent = data.error || "Something went wrong.";
      return;
    }

    resultBox.className = "message-box success";
    resultBox.textContent = "Entry saved successfully!";

    const predictionCard = document.getElementById("predictionCard");
    predictionCard.style.display = "block";

    function sentimentBadge(label) {
      const cls = label.toLowerCase();
      return `<span class="badge ${cls}">${label}</span>`;
    }

    document.getElementById("comparisonResult").innerHTML = `
      <div class="entry-card">
        <h3>VADER</h3>
        <p><strong>Label:</strong> ${sentimentBadge(data.vader.label)}</p>
        <p><strong>Score:</strong> ${data.vader.score}</p>
        <p style="font-size:0.8rem; color:#888; margin-top:8px;">
          Lexicon-based rule model
        </p>
      </div>
      <div class="entry-card">
        <h3>TextBlob</h3>
        <p><strong>Label:</strong> ${sentimentBadge(data.textblob.label)}</p>
        <p><strong>Score:</strong> ${data.textblob.score}</p>
        <p style="font-size:0.8rem; color:#888; margin-top:8px;">
          Polarity-based NLP model
        </p>
      </div>
      <div class="entry-card">
        <h3>DistilBERT</h3>
        <p><strong>Label:</strong> ${sentimentBadge(data.transformer.label)}</p>
        <p><strong>Score:</strong> ${data.transformer.score}</p>
        <p style="font-size:0.8rem; color:#888; margin-top:8px;">
          Transformer deep learning model
        </p>
      </div>
    `;

    const allAgree = (
      data.vader.label === data.textblob.label &&
      data.textblob.label === data.transformer.label
    );

    document.getElementById("pointsEarned").innerHTML = `
      <div class="message-box success">
        +${data.points_earned} points earned!
        Total: <strong>${data.total_points} pts</strong> —
        Trust level: <strong>${data.trust_level}</strong>
        ${allAgree ? " 🎉 Bonus: all models agreed!" : ""}
      </div>
    `;

    document.getElementById("anime_title").value = "";
    document.getElementById("episode").value = 1;
    document.getElementById("rating").value = 5;
    document.getElementById("reflection_text").value = "";
    document.getElementById("true_label").value = "";

  } catch (error) {
    resultBox.className = "message-box error";
    resultBox.textContent = "Failed to connect to the server.";
  }
}

document.getElementById("submitBtn").addEventListener("click", submitJournal);