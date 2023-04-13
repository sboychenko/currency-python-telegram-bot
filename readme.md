# RUB -> BYN -> USD telegram bot
Получает инфу со страниц МИР и БНБ-Банк и по команде + расписанию
шлет готовый курс в указанный чат


## Развернуть в облаке
https://fly.io/app/welcome
Нужно привязать карту, есть возможность хостить докер образа for free

Инициализация
```
flyctl launch
flyctl secrets set BOT_TOKEN=token
flyctl secrets set ADMIN_CHAT_ID=111
flyctl secrets set REDIS_HOST=localhost
flyctl secrets set REDIS_PASS=pass
flyctl secrets list
```

Для деплоя
```
cd ./currency-bot

pip3 freeze > requirements.txt

flyctl scale count 1|0
flyctl deploy --local-only
fly apps restart currency-bot
```

## TODO
* ~~Убрать переменные бот токен + чат в env~~
* ~~Добавить графики~~
* ~~Добавить коннект к редис~~
* Добавить redis/бд для работы в многопользовательском режиме
* Настраивать расписание уведомлений через команду
* ...