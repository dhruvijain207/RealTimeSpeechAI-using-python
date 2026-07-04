from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
import json
import sys


HOST = "127.0.0.1"
PORT = 8000

LANGUAGES = {
    "en": {"name": "English", "speech": "en-IN"},
    "hi": {"name": "Hindi", "speech": "hi-IN"},
    "gu": {"name": "Gujarati", "speech": "gu-IN"},
    "mr": {"name": "Marathi", "speech": "mr-IN"},
}


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Speech Translator</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #15202b;
      --muted: #667085;
      --line: #d8dee8;
      --panel: #ffffff;
      --bg: #f5f7fb;
      --accent: #0f766e;
      --accent-dark: #115e59;
      --soft: #e7f4f1;
      --warn: #b42318;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        linear-gradient(135deg, rgba(15, 118, 110, .10), transparent 32%),
        linear-gradient(315deg, rgba(180, 83, 9, .10), transparent 36%),
        var(--bg);
    }

    main {
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0;
    }

    .shell {
      display: grid;
      grid-template-columns: 370px 1fr;
      gap: 18px;
      align-items: start;
    }

    .panel {
      background: rgba(255, 255, 255, .92);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 18px 45px rgba(16, 24, 40, .08);
    }

    .control-panel {
      padding: 22px;
      position: sticky;
      top: 20px;
    }

    h1 {
      margin: 0 0 8px;
      font-size: clamp(30px, 5vw, 54px);
      line-height: 1;
      letter-spacing: 0;
    }

    .intro {
      color: var(--muted);
      margin: 0 0 22px;
      line-height: 1.55;
      font-size: 15px;
    }

    label {
      display: block;
      font-weight: 700;
      margin: 18px 0 8px;
      font-size: 14px;
    }

    select, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      outline: none;
    }

    select {
      min-height: 44px;
      padding: 0 12px;
    }

    textarea {
      min-height: 132px;
      resize: vertical;
      padding: 12px;
      line-height:1.5;
    }

    select:focus, textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(15, 118, 110, .14);
    }

    .actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 16px;
    }

    button {
      border: 0;
      border-radius:7px;
      min-height:44px;
      padding: 0 14px;
      font: inerit;
      font-weight: 800;
      cursor: pointer;
      transition: transform .15s ease, background .15s ease, border-color .15s ease;
    }

    button:active { transform: translateY(1px); }

    .primary {
      background: var(--accent);
      color: #fff;
    }

    .primary:hover { background: var(--accent-dark); }

    .secondary {
      background: #fff;
      color: var(--ink);
      border: 1px solid var(--line);
    }

    .secondary:hover { border-color: var(--accent); }

    .status {
      min-height: 22px;
      margin-top: 14px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }

    .status.error { color: var(--warn); }

    .results {
      padding: 22px;
    }

    .tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
    }

    .tab {
      background: #fff;
      border: 1px solid var(--line);
      color: var(--ink);
      min-height: 40px;
    }

    .tab.active {
      background: var(--soft);
      border-color: var(--accent);
      color: var(--accent-dark);
    }

    .translation-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .translation-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      min-height: 210px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .translation-card.hidden { display: none; }

    .translation-card h2 {
      margin: 0;
      font-size: 15px;
      letter-spacing: 0;
    }

    .translated-text {
      margin: 0;
      font-size: 24px;
      line-height: 1.35;
      overflow-wrap: anywhere;
      white-space: pre-wrap;
    }

    .placeholder {
      color: var(--muted);
      font-size: 15px;
    }

    @media (max-width: 860px) {
      main { width: min(100% - 22px, 680px); padding: 18px 0; }
      .shell { grid-template-columns: 1fr; }
      .control-panel { position: static; }
      .translation-grid { grid-template-columns: 1fr; }
      .translated-text { font-size: 21px; }
    }
  </style>
</head>
<body>
  <main>
    <h1>Speech Translator</h1>
    <p class="intro">Speak in English, Hindi, Gujarati, or Marathi. The app recognizes your words and translates them into the other three languages.</p>

    <div class="shell">
      <section class="panel control-panel" aria-label="Speech controls">
        <label for="sourceLanguage">Speaking language</label>
        <select id="sourceLanguage"></select>

        <label for="recognizedText">Recognized text</label>
        <textarea id="recognizedText" placeholder="Press Start Speaking, then talk..."></textarea>

        <div class="actions">
          <button class="primary" id="startButton" type="button">Start Speaking</button>
          <button class="secondary" id="translateButton" type="button">Translate</button>
        </div>

        <div id="status" class="status" role="status"></div>
      </section>

      <section class="panel results" aria-label="Translations">
        <div id="tabs" class="tabs"></div>
        <div id="translationGrid" class="translation-grid"></div>
      </section>
    </div>
  </main>

  <script>
    const languages = {
      en: { name: "English", speech: "en-IN" },
      hi: { name: "Hindi", speech: "hi-IN" },
      gu: { name: "Gujarati", speech: "gu-IN" },
      mr: { name: "Marathi", speech: "mr-IN" }
    };

    const sourceLanguage = document.querySelector("#sourceLanguage");
    const recognizedText = document.querySelector("#recognizedText");
    const startButton = document.querySelector("#startButton");
    const translateButton = document.querySelector("#translateButton");
    const statusBox = document.querySelector("#status");
    const tabs = document.querySelector("#tabs");
    const translationGrid = document.querySelector("#translationGrid");

    let activeTarget = "all";
    let latestTranslations = {};

    Object.entries(languages).forEach(([code, language]) => {
      const option = document.createElement("option");
      option.value = code;
      option.textContent = language.name;
      sourceLanguage.appendChild(option);
    });

    function targetLanguages() {
      return Object.keys(languages).filter(code => code !== sourceLanguage.value);
    }

    function setStatus(message, isError = false) {
      statusBox.textContent = message;
      statusBox.classList.toggle("error", isError);
    }

    function renderTabs() {
      tabs.innerHTML = "";
      const buttons = [{ code: "all", name: "All" }, ...targetLanguages().map(code => ({ code, name: languages[code].name }))];
      if (!buttons.some(button => button.code === activeTarget)) activeTarget = "all";

      buttons.forEach(({ code, name }) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `tab${activeTarget === code ? " active" : ""}`;
        button.textContent = name;
        button.addEventListener("click", () => {
          activeTarget = code;
          renderTabs();
          renderTranslations();
        });
        tabs.appendChild(button);
      });
    }

    function renderTranslations() {
      translationGrid.innerHTML = "";
      targetLanguages().forEach(code => {
        const card = document.createElement("article");
        card.className = `translation-card${activeTarget !== "all" && activeTarget !== code ? " hidden" : ""}`;

        const title = document.createElement("h2");
        title.textContent = languages[code].name;

        const text = document.createElement("p");
        text.className = latestTranslations[code] ? "translated-text" : "translated-text placeholder";
        text.textContent = latestTranslations[code] || "Translation will appear here.";

        card.append(title, text);
        translationGrid.appendChild(card);
      });
    }

    async function translateText() {
      const text = recognizedText.value.trim();
      if (!text) {
        setStatus("Please speak or type some text first.", true);
        return;
      }

      setStatus("Translating...");
      translateButton.disabled = true;

      try {
        const response = await fetch("/translate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text,
            source: sourceLanguage.value,
            targets: targetLanguages()
          })
        });

        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "Translation failed.");

        latestTranslations = payload.translations;
        renderTranslations();
        setStatus("Done.");
      } catch (error) {
        setStatus(error.message, true);
      } finally {
        translateButton.disabled = false;
      }
    }

    function startSpeech() {
      const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!Recognition) {
        setStatus("Speech recognition works best in Chrome or Edge. You can type text manually and press Translate.", true);
        return;
      }

      const recognition = new Recognition();
      recognition.lang = languages[sourceLanguage.value].speech;
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      startButton.disabled = true;
      setStatus("Listening...");

      recognition.onresult = event => {
        recognizedText.value = event.results[0][0].transcript;
        setStatus("Speech recognized. Translating...");
        translateText();
      };

      recognition.onerror = event => {
        setStatus(`Speech recognition error: ${event.error}`, true);
      };

      recognition.onend = () => {
        startButton.disabled = false;
      };

      recognition.start();
    }

    sourceLanguage.addEventListener("change", () => {
      latestTranslations = {};
      activeTarget = "all";
      renderTabs();
      renderTranslations();
      setStatus("");
    });

    startButton.addEventListener("click", startSpeech);
    translateButton.addEventListener("click", translateText);

    renderTabs();
    renderTranslations();
  </script>
</body>
</html>
"""


def translate_text(text, source, target):
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl={quote(source)}&tl={quote(target)}&dt=t&q={quote(text)}"
    )
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urlopen(request, timeout=12) as response:
        data = json.loads(response.read().decode("utf-8"))

    return "".join(part[0] for part in data[0] if part and part[0])


class SpeechTranslatorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path not in ("/", "/index.html"):
            self.send_json({"error": "Not found"}, status=404)
            return

        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/translate":
            self.send_json({"error": "Not found"}, status=404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            text = str(payload.get("text", "")).strip()
            source = str(payload.get("source", "")).strip()
            targets = payload.get("targets", [])

            if not text:
                self.send_json({"error": "Text is required."}, status=400)
                return
            if source not in LANGUAGES:
                self.send_json({"error": "Unsupported source language."}, status=400)
                return
            if not isinstance(targets, list) or any(target not in LANGUAGES for target in targets):
                self.send_json({"error": "Unsupported target language."}, status=400)
                return

            translations = {
                target: translate_text(text, source, target)
                for target in targets
                if target != source
            }
            self.send_json({"translations": translations})
        except (HTTPError, URLError, TimeoutError) as error:
            self.send_json(
                {"error": f"Could not reach the translation service: {error}"},
                status=502,
            )
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON."}, status=400)
        except Exception as error:
            self.send_json({"error": f"Unexpected error: {error}"}, status=500)

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def main():
    global PORT
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])

    server = ThreadingHTTPServer((HOST, PORT), SpeechTranslatorHandler)
    print(f"Speech Translator running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server.")
    server.serve_forever()


if __name__ == "__main__":
    main()
