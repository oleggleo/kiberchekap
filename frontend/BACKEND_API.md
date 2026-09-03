# Контракт бэкенда для лендинга КиберЧекап

Лендинг (форма заявки + квиз) шлёт **2 запроса**. Любой бэкенд — ваш или заказчика —
должен реализовать эти два эндпоинта, чтобы принимать заявки.

Адрес бэкенда задаётся в **одном месте** — блок `0_config` на странице Тильды:

```html
<script>
  window.APP_CONFIG = { apiUrl: "https://api.вашдомен.ru" };
</script>
```

Все запросы уходят на `apiUrl` + путь. Если `apiUrl: ""` — запросы идут на тот же домен, где стоит сайт.

---

## 1. Создание заявки

```
POST  {apiUrl}/leads
Content-Type: application/json
```

Тело запроса:
```json
{
  "name":    "Иван Иванов",
  "phone":   "+7 912 345 67 89",
  "email":   "ivan@company.ru",
  "inn":     "7700000000",
  "segment": "Интернет-магазины"
}
```

Ожидаемый ответ — **HTTP 200** и JSON с идентификатором заявки:
```json
{ "lead_id": 123 }
```

- Если ответ `200 OK` и есть `lead_id` → открывается модалка-квиз, `lead_id` запоминается.
- Если ответ НЕ `2xx` (например 400/500) → пользователю показывается `alert` об ошибке.
- Если сервер недоступен / CORS заблокирован (сетевая ошибка) → форма всё равно
  показывает «Заявка принята» и открывает квиз (но заявка на сервер не попадёт).

## 2. Дозапись результата квиза

После прохождения квиза, **только если был получен `lead_id`**:

```
PATCH  {apiUrl}/leads/{lead_id}
Content-Type: application/json
```

Тело:
```json
{ "cyber_problem": "Несанкционированный вывод денежных средств" }
```

Ответ не обязателен (ошибки игнорируются, только пишутся в консоль).

---

## Обязательные требования к серверу

### HTTPS
Сайт на Тильде работает по `https://`. Бэкенд тоже **обязан** быть на `https://`.
Запрос с HTTPS-страницы на `http://` браузер блокирует (mixed content).
`http://IP:порт` с Тильды работать НЕ будет.

### CORS
Запросы кросс-доменные (домен Тильды → ваш сервер). Сервер должен отдавать:

```
Access-Control-Allow-Origin: https://<домен-сайта>     (или *)
Access-Control-Allow-Methods: POST, PATCH, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

и корректно отвечать на preflight-запрос `OPTIONS` (статус 200/204).

---

## Готовый пример: Nginx (HTTPS + CORS + проксирование на ваш :8000)

```nginx
server {
    listen 443 ssl;
    server_name api.вашдомен.ru;

    ssl_certificate     /etc/letsencrypt/live/api.вашдомен.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.вашдомен.ru/privkey.pem;

    location / {
        # --- CORS ---
        add_header Access-Control-Allow-Origin  $http_origin always;
        add_header Access-Control-Allow-Methods 'POST, PATCH, OPTIONS' always;
        add_header Access-Control-Allow-Headers 'Content-Type' always;
        if ($request_method = OPTIONS) { return 204; }

        # --- проксирование на бэкенд ---
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

SSL-сертификат — бесплатно через `certbot --nginx -d api.вашдомен.ru`.

После этого в блоке `0_config` ставится `apiUrl: "https://api.вашдомен.ru"` — и заявки идут на ваш сервер.
Заказчик при передаче просто меняет этот адрес на свой.
