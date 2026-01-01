# ⚡ Быстрый старт - Деплой на Vercel

## 1️⃣ Подготовка репозитория

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## 2️⃣ Деплой на Vercel

1. Идите на [vercel.com](https://vercel.com) → Войдите через GitHub
2. **Add New Project** → Выберите репозиторий
3. Vercel автоматически определит Next.js ✅

## 3️⃣ Переменные окружения

В **Settings → Environment Variables** добавьте:

```
NEXT_PUBLIC_BOT_TOKEN=ваш_токен_бота
NEXT_PUBLIC_BOT_USERNAME=ваш_бот_username
NEXT_PUBLIC_API_URL=https://ваш-проект.vercel.app
API_ID=ваш_api_id
API_HASH=ваш_api_hash
ADMIN_IDS=ваш_admin_id
```

## 4️⃣ Важно!

После первого деплоя:
1. Скопируйте URL (например: `https://your-app.vercel.app`)
2. Обновите `NEXT_PUBLIC_API_URL` на этот URL
3. Нажмите **Redeploy**

## ✅ Готово!

Ваше приложение доступно по адресу: `https://your-app.vercel.app`

---

📖 Подробная инструкция: `VERCEL_DEPLOY.md`
✅ Чеклист: `DEPLOY_CHECKLIST.md`

