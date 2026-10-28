#!/bin/bash
cd "$(dirname "$0")"

echo "==================================================================="
echo "   🎓 رفع مشروع دليل الطالب الذكي إلى GitHub و Vercel"
echo "==================================================================="

if ! command -v git &> /dev/null; then
    echo "[!] Git غير مثبت. يرجى تثبيته أو رفع الملفات يدوياً عبر المتصفح."
    exit 1
fi

if [ ! -d ".git" ]; then
    echo "[*] تهيئة Git لأول مرة..."
    git init
    git branch -M main
fi

if ! git remote get-url origin &> /dev/null; then
    echo ""
    read -p ">> الصق رابط مستودع GitHub (مثال: https://github.com/user/repo.git): " REPO_URL
    if [ -n "$REPO_URL" ]; then
        git remote add origin "$REPO_URL"
    else
        echo "[!] لم يتم إدخال رابط."
        exit 1
    fi
fi

git add .
git commit -m "Update: Smart Student Guide Web Edition"
git push -u origin main
