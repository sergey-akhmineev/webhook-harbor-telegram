# Webhook harbor-telegram
Currently, the reaction is set up only for push events.

В данный момент настроена реакция только на push

## How to Use

If necessary, build the image first:
```shell
docker build -t webhook-harbor-telegram:0.1 .
```

### Step 1: Create a Bot in Telegram

1. Open Telegram and find the user BotFather.
2. Create a new bot by sending the command /newbot and follow the instructions.
3. Write down your bot token that you receive as a result.
4. Add the bot to a channel/group.

### Step 2: Configure the Webhook Container
1. Open conf.toml.
2. Fill in the necessary information for the container's operation. If message_thread_id is not needed, it should be commented out.
3. The chat ID can be obtained by copying the link to a message in the format - https://t.me/c/123xxxx567/17/16
   - Here's the breakdown of the link: https://t.me/c/{chat_id}/{message_thread_id}/{message_id}
4. To use chat_id in the API, you need to prepend -100, resulting in -100123xxxx567.


### Step 3: Set Up the Webhook in Harbor
1. Log in to Harbor.
2. Go to the repository settings.
3. Set up a new Webhook by specifying the URL of your server, which will receive notifications (e.g., http://your-server-ip:5000/webhook).
4. Make sure you have selected the necessary event, which is push.

## Как использовать

### Шаг 1: Создайте бота в Telegram

Если необходимо, предварительно соберите образ
```shell
docker build -t webhook-harbor-telegram:0.1 .
```


1. Откройте Telegram и найдите пользователя BotFather.
2. Создайте нового бота, отправив команду /newbot и следуя инструкциям.
3. Запишите ваш токен бота, который вы получите в результате.
4. Добавьте бота в канал\группу

### Шаг 2: Настройка контейнера webhook

1. Откройте conf.toml.
2. Заполните данные для работы контейнера, если message_thread_id вам не нужен его необходимо закомментировать.
3. Чат id можно скопировал ссылку на сообщение по типу - https://t.me/c/123xxxx567/17/16
   - Вот расшифровка ссылки https://t.me/c/{chat_id}/{message_thread_id}/{message_id}
4. Для использования chat_id в API надо добавить -100, получите -100123xxxx567

### Шаг 3: Настройка вебхука в Harbor

1. Зайдите в Harbor.
2. Перейдите в настройки репозитория.
3. Настройте новый Webhook, указав URL вашего сервера, который будет принимать уведомления (например, http://your-server-ip:5000/webhook).
4. Убедитесь, что вы выбрали необходимое событие, push.