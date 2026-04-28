(() => {
  "use strict";

  const els = {
    card: document.getElementById("meme-card"),
    date: document.getElementById("today-date"),
    dayOfYear: document.getElementById("day-of-year"),
    jpName: document.getElementById("meme-jp-name"),
    enName: document.getElementById("meme-en-name"),
    image: document.getElementById("meme-image"),
    skeleton: document.getElementById("image-skeleton"),
    fallback: document.getElementById("image-fallback"),
    description: document.getElementById("meme-description"),
    year: document.getElementById("meme-year"),
    origin: document.getElementById("meme-origin"),
    rerollBtn: document.getElementById("reroll-btn"),
    shareBtn: document.getElementById("share-btn"),
    copyFeedback: document.getElementById("copy-feedback"),
    footerYear: document.getElementById("footer-year"),
  };

  const dateFmt = new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "short",
  });

  function dayOfYear(date) {
    const start = new Date(date.getFullYear(), 0, 0);
    const diff = date - start;
    const oneDay = 1000 * 60 * 60 * 24;
    return Math.floor(diff / oneDay);
  }

  function pickDailyIndex(memes, date) {
    // 日付（年×1000 + 通算日）でハッシュして決定論的に1つ選ぶ
    const seed = date.getFullYear() * 1000 + dayOfYear(date);
    return seed % memes.length;
  }

  function setBusy(isBusy) {
    els.card.setAttribute("aria-busy", isBusy ? "true" : "false");
  }

  function render(meme, date) {
    els.date.textContent = dateFmt.format(date);
    els.dayOfYear.textContent = `第${dayOfYear(date)}日`;
    els.jpName.textContent = meme.jpName;
    els.enName.textContent = meme.name;
    els.description.textContent = meme.description;
    els.year.textContent = meme.year ? `${meme.year}年ごろ` : "—";
    els.origin.textContent = meme.origin || "—";

    // 画像の差し替え
    els.image.classList.remove("is-loaded");
    els.skeleton.classList.remove("is-hidden");
    els.fallback.hidden = true;
    els.image.alt = `${meme.jpName}（${meme.name}）`;
    els.image.src = meme.image;
  }

  function attachImageHandlers() {
    els.image.addEventListener("load", () => {
      els.image.classList.add("is-loaded");
      els.skeleton.classList.add("is-hidden");
      els.fallback.hidden = true;
      setBusy(false);
    });
    els.image.addEventListener("error", () => {
      els.skeleton.classList.add("is-hidden");
      els.fallback.hidden = false;
      setBusy(false);
    });
  }

  async function loadMemes() {
    const res = await fetch("memes.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to load memes.json: ${res.status}`);
    return res.json();
  }

  function showCopyFeedback(message) {
    els.copyFeedback.textContent = message;
    if (showCopyFeedback._timer) clearTimeout(showCopyFeedback._timer);
    showCopyFeedback._timer = setTimeout(() => {
      els.copyFeedback.textContent = "";
    }, 2400);
  }

  async function copyShareText(meme, date) {
    const text =
      `🗓️ ${dateFmt.format(date)}の今日のミーム\n` +
      `『${meme.jpName}』(${meme.name})\n\n` +
      `${meme.description}`;
    try {
      await navigator.clipboard.writeText(text);
      showCopyFeedback("コピーしました！SNSに貼り付けてシェアできます。");
    } catch (e) {
      showCopyFeedback("コピーに失敗しました。手動で選択してください。");
    }
  }

  async function main() {
    els.footerYear.textContent = new Date().getFullYear();
    attachImageHandlers();

    let memes;
    try {
      memes = await loadMemes();
    } catch (err) {
      console.error(err);
      els.jpName.textContent = "ミームデータを読み込めませんでした";
      els.description.textContent =
        "memes.json の読み込みに失敗しました。ローカルで開く場合は静的サーバー経由で開いてください（例: python3 -m http.server）。";
      setBusy(false);
      return;
    }
    if (!Array.isArray(memes) || memes.length === 0) {
      els.jpName.textContent = "ミームが登録されていません";
      setBusy(false);
      return;
    }

    const today = new Date();
    let currentIndex = pickDailyIndex(memes, today);
    render(memes[currentIndex], today);

    els.rerollBtn.addEventListener("click", () => {
      // 今日とは別のミームに切り替え（インデックスを進める）
      currentIndex = (currentIndex + 1) % memes.length;
      setBusy(true);
      render(memes[currentIndex], today);
    });

    els.shareBtn.addEventListener("click", () => {
      copyShareText(memes[currentIndex], today);
    });
  }

  main();
})();
