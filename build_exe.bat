@echo off
chcp 65001 >nul
rem ============================================================
rem  InputCH 一键构建 exe（含讯飞级开源词库，统一置于 githubMIT/）
rem  双击本文件即可：装依赖 -> 下载开源词库 -> PyInstaller 打包
rem  需联网（首次下载词库）；之后 exe 完全离线可用。
rem  开源词库来源与署名见 githubMIT/LICENSE 与各子目录 README。
rem ============================================================
setlocal

cd /d "%~dp0"

echo [1/4] 安装依赖（pypinyin 可选，提升多音字准确度）...
pip install pypinyin pyinstaller >nul 2>&1

echo [2/4] 下载开源拼音词库（mozillazg，落入 githubMIT/）...
if not exist githubMIT\pinyin-data mkdir githubMIT\pinyin-data
if not exist githubMIT\phrase-pinyin-data mkdir githubMIT\phrase-pinyin-data
set CHARS_URL=https://raw.githubusercontent.com/mozillazg/pinyin-data/master/kMandarin.txt
set PHRASES_URL=https://raw.githubusercontent.com/mozillazg/phrase-pinyin-data/master/phrase.txt

curl -fsSL -o githubMIT\pinyin-data\kMandarin.txt "%CHARS_URL%" 2>nul
if errorlevel 1 (
  powershell -Command "Invoke-WebRequest -Uri '%CHARS_URL%' -OutFile 'githubMIT\pinyin-data\kMandarin.txt'" 2>nul
)
curl -fsSL -o githubMIT\phrase-pinyin-data\phrase.txt "%PHRASES_URL%" 2>nul
if errorlevel 1 (
  powershell -Command "Invoke-WebRequest -Uri '%PHRASES_URL%' -OutFile 'githubMIT\phrase-pinyin-data\phrase.txt'" 2>nul
)

if exist githubMIT\pinyin-data\kMandarin.txt (echo   单字库: githubMIT\pinyin-data\kMandarin.txt OK) else (echo   单字库下载失败（将仅用 THUOCL+内置表）)
if exist githubMIT\phrase-pinyin-data\phrase.txt (echo   词组库: githubMIT\phrase-pinyin-data\phrase.txt OK) else (echo   词组库下载失败（将仅用 THUOCL+内置表）)

echo [3/4] 清理旧缓存与旧构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist cache rmdir /s /q cache

echo [4/4] PyInstaller 打包（单文件 / 无控制台窗口）...
pyinstaller --onefile --windowed --name "InputCH" ^
  --add-data "githubMIT;githubMIT" ^
  --add-data "logo.png;." ^
  --add-data "common_words.txt;." ^
  app.py

echo.
echo 完成。exe 位于 dist\InputCH.exe
echo 首次双击会构建词库索引（几十秒），之后秒开。
pause
