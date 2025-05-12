from flask import Flask, request
import requests
import tomllib
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# --- Загрузка конфигурации ---
try:
    with open("conf.toml", "rb") as f:
        conf = tomllib.load(f)
    logging.info("Конфигурация успешно загружена.")
except Exception as e:
    logging.error(f"Не удалось загрузить conf.toml: {e}")
    raise

# Настройки Telegram
bot_token = conf["telegram"]["bot_token"]
CHAT_ID = conf["telegram"]["chat_id"]
MESSAGE_THREAD_ID = conf["telegram"].get("message_thread_id")
API_URL = f"https://api.telegram.org/bot{bot_token}/sendMessage"

# Список событий
ENABLED_EVENTS = conf.get("events", {})

# Список символов для экранирования Markdown
ESCAPE_CHARS = conf.get("markdown", {}).get("escape_chars", [])

def escape_markdown(text: str) -> str:
    """Экранируем спецсимволы согласно ESCAPE_CHARS."""
    if not isinstance(text, str):
        text = str(text)
    for ch in ESCAPE_CHARS:
        text = text.replace(ch, f"\\{ch}")
    return text

def send_message_to_telegram(message: str):
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    if MESSAGE_THREAD_ID:
        payload["message_thread_id"] = MESSAGE_THREAD_ID

    try:
        resp = requests.post(API_URL, json=payload)
        resp.raise_for_status()
        logging.info("Сообщение успешно отправлено.")
    except requests.RequestException as e:
        logging.error(f"Ошибка при отправке в Telegram: {e}")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    logging.info(f"Входящий вебхук: {data}")

    event_type = data.get("type")
    # Если событие в конфиге отключено — игнорируем
    if not ENABLED_EVENTS.get(event_type, False):
        logging.info(f"Событие {event_type} отключено в конфиге, пропускаем.")
        return "Ignored", 200

    operator = escape_markdown(data.get("operator", "неизвестный"))
    event_data = data.get("event_data", {})
    repo        = event_data.get("repository", {})
    repo_name   = escape_markdown(repo.get("repo_full_name", "неизвестный"))
    resources   = event_data.get("resources", [])

    if not resources:
        logging.warning("Нет ресурсов для обработки.")
        return "No resources", 200

    messages = []

    # 1) PUSH_ARTIFACT
    if event_type == "PUSH_ARTIFACT":
        for r in resources:
            tag = escape_markdown(r.get("tag", "—"))
            url = r.get("resource_url", "—")
            msg = (
                "📦 *Новый пуш в Harbor*\n"
                f"*Репозиторий:* {repo_name}\n"
                f"*Тег:* {tag}\n"
                f"*URL:* `{url}`\n"
                f"*Автор пуша:* {operator}"
            )
            messages.append(msg)

    # 2) PULL_ARTIFACT
    elif event_type == "PULL_ARTIFACT":
        for r in resources:
            tag = escape_markdown(r.get("tag", "—"))
            url = r.get("resource_url", "—")
            msg = (
                "📥 *Pull артефакта в Harbor*\n"
                f"*Репозиторий:* {repo_name}\n"
                f"*Тег:* {tag}\n"
                f"*URL:* `{url}`\n"
                f"*Пользователь:* {operator}"
            )
            messages.append(msg)

    # 3) DELETE_ARTIFACT
    elif event_type == "DELETE_ARTIFACT":
        for r in resources:
            tag = escape_markdown(r.get("tag", "—"))
            url = r.get("resource_url", "—")
            msg = (
                "🗑️ *Удаление артефакта в Harbor*\n"
                f"*Репозиторий:* {repo_name}\n"
                f"*Тег:* {tag}\n"
                f"*URL:* `{url}`\n"
                f"*Пользователь:* {operator}"
            )
            messages.append(msg)

    # 4) SCANNING_STOPPED
    elif event_type == "SCANNING_STOPPED":
        for r in resources:
            tag     = escape_markdown(r.get("tag", "—"))
            url     = r.get("resource_url", "—")
            overview = r.get("scan_overview", {})
            detail  = next(iter(overview.values()), {})
            status  = escape_markdown(detail.get("scan_status", "—"))
            duration = detail.get("duration", 0)
            msg = (
                "🔍 *Сканирование остановлено*\n"
                f"*Репозиторий:* {repo_name}\n"
                f"*Тег:* {tag}\n"
                f"*URL:* `{url}`\n"
                f"*Статус скана:* {status}\n"
                f"*Продолжительность:* {duration}s\n"
                f"*Пользователь:* {operator}"
            )
            messages.append(msg)

    # 5) SCANNING_COMPLETED
    elif event_type == "SCANNING_COMPLETED":
        for r in resources:
            tag      = escape_markdown(r.get("tag", "—"))
            url      = r.get("resource_url", "—")
            overview = r.get("scan_overview", {})
            detail   = next(iter(overview.values()), {})
            status   = escape_markdown(detail.get("scan_status", "—"))
            duration = detail.get("duration", 0)
            severity = escape_markdown(detail.get("severity", "—"))
            summary  = detail.get("summary", {}) or {}
            total    = summary.get("total", 0)
            fixable  = summary.get("fixable", 0)
            counts   = summary.get("summary", {})

            # Формируем разбивку по уровням критичности
            counts_lines = ""
            for lvl, cnt in counts.items():
                lvl_esc = escape_markdown(lvl)
                counts_lines += f"*{lvl_esc}:* {cnt}\n"

            scanner = detail.get("scanner", {})
            sc_name = escape_markdown(scanner.get("name", "—"))
            sc_ver  = escape_markdown(scanner.get("version", "—"))

            msg = (
                "🔍 *Сканирование завершено*\n"
                f"*Репозиторий:* {repo_name}\n"
                f"*Тег:* {tag}\n"
                f"*URL:* `{url}`\n"
                f"*Статус скана:* {status}\n"
                f"*Продолжительность:* {duration}s\n"
                f"*Критичность (макс):* {severity}\n"
                f"*Всего уязвимостей:* {total}\n"
                f"*Исправимо:* {fixable}\n"
                f"{counts_lines}"
                f"*Сканер:* {sc_name} {sc_ver}\n"
                f"*Пользователь:* {operator}"
            )
            messages.append(msg)

    # Отправляем все сообщения
    for m in messages:
        logging.info(f"Отправка в Telegram:\n{m}")
        send_message_to_telegram(m)

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
