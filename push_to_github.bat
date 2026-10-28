@echo off
chcp 65001 >nul
title رفع المشروع إلى GitHub و Vercel
cd /d "%~dp0"

echo ===================================================================
echo    🎓 رفع مشروع دليل الطالب الذكي إلى GitHub و Vercel
echo ===================================================================
echo.

:: 1. التحقق من وجود Git
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] تنبيه: برنامج Git غير مثبت على هذا الجهاز أو غير مضاف للـ PATH.
    echo.
    echo لا تقلق! يمكنك رفع الموقع والحصول على اللينك في ثوان بعدة طرق:
    echo  1. أسرع طريقة بدون برامج: اسحب المجلد إلى موقع Netlify Drop:
    echo     https://app.netlify.com/drop
    echo  2. عبر المتصفح في GitHub: أنشئ مستودعاً جديداً ثم اضغط "Upload files".
    echo  3. أو حمّل Git من: https://git-scm.com/download/win
    echo.
    echo اضغط أي زر لفتح دليل الرفع أو إغلاق هذه النافذة...
    pause >nul
    exit /b
)

:: 2. التحقق من تهيئة المستودع المحلي
if not exist ".git" (
    echo [*] تهيئة مستودع Git محلي لأول مرة...
    git init
    git branch -M main
)

:: 3. التحقق من الرابط البعيد origin
git remote get-url origin >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [*] لم يتم ربط هذا المجلد بمستودع GitHub بعد.
    echo يرجى إنشاء مستودع جديد على GitHub (Public) ثم لصق رابطه هنا.
    echo مثال: https://github.com/your-username/student-guide.git
    echo.
    set /p REPO_URL=">> الصق رابط المستودع هنا ثم اضغط Enter: "
    if defined REPO_URL (
        git remote add origin %REPO_URL%
    ) else (
        echo [!] لم يتم إدخال رابط. تم إلغاء العملية.
        pause
        exit /b
    )
)

:: 4. إضافة الملفات وعمل Commit والرفع
echo.
echo [*] جاري تجهيز الملفات وتجهيز الرفع...
git add .
git commit -m "Update: Smart Student Guide Web Edition"
echo.
echo [*] جاري الرفع إلى GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ===================================================================
    echo    ✅ تم الرفع بنجاح إلى GitHub!
    echo    سيتولى Vercel أو GitHub Pages إنشاء وتحديث اللينك أونلاين فوراً.
    echo ===================================================================
) else (
    echo.
    echo [!] حدث خطأ أثناء الرفع. تأكد من صحة الرابط ومن تسجيل دخولك في Git.
)

echo.
pause
