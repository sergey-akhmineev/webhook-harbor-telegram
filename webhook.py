from flask import Flask, request
import requests
import tomllib
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)


def escape_markdown(text):
    """
    Экранирует специальные символы Markdown в тексте.
    """
    escape_chars = ['\\', '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

# Загрузка конфигурации из conf.toml
try:
    with open("conf.toml", "rb") as toml_file:
        conf_dict = tomllib.load(toml_file)
    logging.info("Конфигурация успешно загружена.")
except FileNotFoundError:
    logging.error("Файл конфигурации conf.toml не найден.")
    raise Exception("Файл конфигурации conf.toml не найден.")
except Exception as e:
    logging.error(f"Ошибка при загрузке конфигурации: {str(e)}")
    raise Exception(f"Ошибка при загрузке конфигурации: {str(e)}")

# Извлечение токена Telegram и Chat ID из конфигурации
TELEGRAM_API_URL = f'https://api.telegram.org/bot{conf_dict["telegram"]["bot_token"]}/sendMessage'
CHAT_ID = conf_dict["telegram"]["chat_id"]
# Используем None по умолчанию, если message_thread_id не указан
MESSAGE_THREAD_ID = conf_dict.get("telegram", {}).get("message_thread_id", None)


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    logging.info(f"Получены данные вебхука: {data}")

    if data and data.get('type') == 'PUSH_ARTIFACT':
        event_data = data.get('event_data', {})
        repository_info = event_data.get('repository', {})
        resources = event_data.get('resources', [])

        repo_full_name = repository_info.get('repo_full_name', 'неизвестный репозиторий')
        repo_full_name = escape_markdown(repo_full_name)  # Экранирование

        if not resources:
            logging.warning("Нет ресурсов для обработки.")
            return 'No resources to process', 200

        messages = []
        for resource in resources:
            tag = escape_markdown(resource.get('tag', 'неизвестный тег'))  # Экранирование тега
            resource_url = resource.get('resource_url', 'неизвестный URL')
            operator = escape_markdown(data.get('operator', 'неизвестный'))  # Экранирование оператора
            message = (
                f"📦 *Новый пуш в Harbor*\n"
                f"*Репозиторий:* {repo_full_name}\n"
                f"*Тег:* {tag}\n"
                f"*URL:* `{resource_url}`\n"
                f"*Автор пуша:* {operator}"
            )
            messages.append(message)

        # Отправка всех сообщений последовательно
        for msg in messages:
            logging.info(f"Отправка сообщения: {msg}")
            send_message_to_telegram(msg)
    else:
        logging.warning("Получены некорректные данные вебхука или отсутствует тип 'PUSH_ARTIFACT'.")

    return 'OK', 200


def send_message_to_telegram(message):
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown',  # Для форматирования сообщения
    }
    # Проверяем наличие message_thread_id независимо от его значения
    if MESSAGE_THREAD_ID is not None:
        payload['message_thread_id'] = MESSAGE_THREAD_ID

    try:
        response = requests.post(TELEGRAM_API_URL, json=payload)
        response.raise_for_status()  # Проверка на HTTP-ошибки
        logging.info("Сообщение успешно отправлено в Telegram.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при отправке сообщения: {str(e)}")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)