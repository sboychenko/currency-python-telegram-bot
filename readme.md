# RUB -> BYN -> USD telegram bot
Получает инфу со страниц МИР и БНБ-Банк и по команде + расписанию
шлет готовый курс в указанный чат


## Развернуть в облаке
https://fly.io/app/welcome
Нужно привязать карту, есть возможность хостить докер образа for free

```
flyctl launch
flyctl scale count 1|0
flyctl deploy --local-only
fly apps restart currency-bot
```

## TODO
* Убрать переменные бот токен + чат в env
* Добавить redis/бд для работы в многопользовательском режиме
* Настраивать расписание уведомлений через команду
* ...