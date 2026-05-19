# ============================================
# Capacitor 一键打包脚本
# 用法: .\build-apk.ps1 -AppName "我的应用" -AppId "com.example.myapp"
# ============================================

param(
    [string]$AppName = "MyApp",
    [string]$AppId = "com.example.myapp",
    [string]$WebDir = "www"
)

Write-Host "`n=== Capacitor 一键打包脚本 ===" -ForegroundColor Cyan

# 1. 初始化 npm
Write-Host "`n[1/7] 初始化 npm 项目..." -ForegroundColor Yellow
if (!(Test-Path "package.json")) {
    npm init -y | Out-Null
    Write-Host "  ✓ package.json 已创建" -ForegroundColor Green
} else {
    Write-Host "  ✓ package.json 已存在" -ForegroundColor Green
}

# 2. 安装 Capacitor 依赖
Write-Host "`n[2/7] 安装 Capacitor 依赖..." -ForegroundColor Yellow
npm install @capacitor/core @capacitor/cli @capacitor/android --save-dev
Write-Host "  ✓ 依赖安装完成" -ForegroundColor Green

# 3. 初始化 Capacitor
Write-Host "`n[3/7] 初始化 Capacitor 项目..." -ForegroundColor Yellow
npx cap init $AppName $AppId --web-dir $WebDir
Write-Host "  ✓ Capacitor 初始化完成" -ForegroundColor Green

# 4. 准备网页文件
Write-Host "`n[4/7] 准备网页文件..." -ForegroundColor Yellow
if (!(Test-Path $WebDir)) {
    New-Item -ItemType Directory -Path $WebDir | Out-Null
    Write-Host "  ✓ 创建 $WebDir 目录" -ForegroundColor Green
}

# 复制当前目录的 HTML/CSS/JS/图片到 www
$files = Get-ChildItem -File | Where-Object { 
    $_.Extension -match '\.(html|css|js|png|jpg|jpeg|gif|svg|ico|webp)$' -and 
    $_.Name -ne 'package.json' -and 
    $_.Name -ne 'package-lock.json' -and
    $_.Name -ne 'capacitor.config.json' -and
    $_.Name -ne 'build-apk.ps1'
}

foreach ($file in $files) {
    Copy-Item $file.FullName -Destination "$WebDir\" -Force
    Write-Host "  ✓ 复制 $($file.Name)" -ForegroundColor Green
}

# 5. 添加 Android 平台
Write-Host "`n[5/7] 添加 Android 平台..." -ForegroundColor Yellow
if (Test-Path "android") {
    Write-Host "  ⚠ android 目录已存在，跳过" -ForegroundColor Yellow
} else {
    npx cap add android
    Write-Host "  ✓ Android 平台添加完成" -ForegroundColor Green
}

# 6. 配置国内镜像
Write-Host "`n[6/7] 配置 Gradle 国内镜像..." -ForegroundColor Yellow
$buildGradle = "android\build.gradle"
if (Test-Path $buildGradle) {
    $content = Get-Content $buildGradle -Raw
    
    # 检查是否已配置镜像
    if ($content -notmatch "maven.aliyun.com") {
        $content = $content -replace '(buildscript\s*\{[\s\S]*?repositories\s*\{)', '$1' + "`n        maven { url 'https://maven.aliyun.com/repository/central' }`n        maven { url 'https://maven.aliyun.com/repository/public' }`n        maven { url 'https://maven.aliyun.com/repository/google' }"
        $content = $content -replace '(allprojects\s*\{[\s\S]*?repositories\s*\{)', '$1' + "`n        maven { url 'https://maven.aliyun.com/repository/central' }`n        maven { url 'https://maven.aliyun.com/repository/public' }`n        maven { url 'https://maven.aliyun.com/repository/google' }"
        $content | Set-Content $buildGradle -Encoding UTF8
        Write-Host "  ✓ 镜像配置完成" -ForegroundColor Green
    } else {
        Write-Host "  ✓ 镜像已配置" -ForegroundColor Green
    }
}

# 7. 同步项目
Write-Host "`n[7/7] 同步项目..." -ForegroundColor Yellow
npx cap sync
Write-Host "  ✓ 同步完成" -ForegroundColor Green

# 完成
Write-Host "`n=== 打包准备完成！===" -ForegroundColor Cyan
Write-Host "`n接下来：" -ForegroundColor White
Write-Host "1. 运行 npx cap open android 打开 Android Studio" -ForegroundColor White
Write-Host "2. 等待 Gradle 同步完成" -ForegroundColor White
Write-Host "3. 点击 Build -> Build APK 生成 APK" -ForegroundColor White
Write-Host "`nAPK 位置: android\app\build\outputs\apk\debug\app-debug.apk" -ForegroundColor Yellow
Write-Host "`n" -NoNewline
