# 🚀 Быстрый старт с Caddy

## Шаг 1: Скачайте Caddy
1. Перейдите на https://caddyserver.com/download
2. Выберите Windows и скачайте `caddy_windows_amd64.zip`
3. Распакуйте и переименуйте `caddy.exe` в папку проекта

## Шаг 2: Настройте домен в Caddyfile
Откройте `Caddyfile` и замените `yourdomain.com` на ваш домен:
```
example.com {
    reverse_proxy localhost:3000
}
```

## Шаг 3: Настройте DNS
В панели управления доменом добавьте A-запись:
- **Тип:** A
- **Имя:** @ (или оставьте пустым)
- **Значение:** IP-адрес вашего сервера
- **TTL:** 3600

## Шаг 4: Откройте порты в Firewall
```powershell
New-NetFirewallRule -DisplayName "Caddy HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Caddy HTTPS" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow
```

## Шаг 5: Запустите
1. Соберите приложение: `npm run build`
2. Запустите: `start-caddy.bat`

Готово! Ваш сайт будет доступен по адресу `https://yourdomain.com`

## ⚙️ Обновление настроек бота
После настройки домена обновите `scripts/settings.json`:
```json
{
  "site_url": "https://yourdomain.com",
  "api_url": "https://yourdomain.com"
}
```

