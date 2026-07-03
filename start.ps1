# 中译中 - 服务启动脚本
# 用法：
#   .\start.ps1              交互式选择
#   .\start.ps1 -All         启动全部（后端 + 前端App + 后台管理）
#   .\start.ps1 -Backend     仅启动后端
#   .\start.ps1 -App         仅启动前端 App
#   .\start.ps1 -Admin       仅启动后台管理
#   .\start.ps1 -Stop        停止所有相关进程

param(
    [switch]$All,
    [switch]$Backend,
    [switch]$App,
    [switch]$Admin,
    [switch]$Stop
)

$ErrorActionPreference = "SilentlyContinue"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# ============ 停止服务 ============
if ($Stop) {
    Write-Host ""
    Write-Host "[停止] 正在停止所有服务..." -ForegroundColor Yellow
    # 通过端口找到进程并停止
    $ports = @(8000, 5173, 5174, 5176)
    foreach ($port in $ports) {
        $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($conn) {
            $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Write-Host "  已停止端口 $port (PID $($proc.Id)) - $($proc.ProcessName)" -ForegroundColor Green
            }
        }
    }
    Write-Host "[完成]" -ForegroundColor Cyan
    Write-Host ""
    exit 0
}

# ============ 交互式选择 ============
if (-not ($All -or $Backend -or $App -or $Admin)) {
    Write-Host "`n========== 中译中服务启动 ==========" -ForegroundColor Cyan
    Write-Host "  1. 全部启动 (后端 + 前端App + 后台管理)"
    Write-Host "  2. 仅后端 API (http://localhost:8000)"
    Write-Host "  3. 仅前端 App (http://localhost:5173)"
    Write-Host "  4. 仅后台管理 (http://localhost:5174)"
    Write-Host "  5. 停止所有服务"
    Write-Host "  0. 退出"
    Write-Host "=====================================`n"
    $choice = Read-Host "请选择 [0-5]"
    switch ($choice) {
        "1" { $All = $true }
        "2" { $Backend = $true }
        "3" { $App = $true }
        "4" { $Admin = $true }
        "5" { & $PSCommandPath -Stop; exit 0 }
        "0" { exit 0 }
        default { Write-Host "无效选择" -ForegroundColor Red; exit 1 }
    }
}

# ============ 启动后端 ============
function Start-Backend {
    Write-Host "`n[后端] 启动 FastAPI (端口 8000)..." -ForegroundColor Cyan
    $backendDir = Join-Path $ProjectRoot "backend"
    if (-not (Test-Path (Join-Path $backendDir "main.py"))) {
        Write-Host "  [错误] 找不到 backend/main.py" -ForegroundColor Red
        return
    }
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '[后端] FastAPI 启动中...' -ForegroundColor Cyan; cd '$backendDir'; python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    Write-Host "  已在新窗口启动 -> http://localhost:8000" -ForegroundColor Green
    Write-Host "  API 文档: http://localhost:8000/docs" -ForegroundColor Gray
}

# ============ 启动前端 App ============
function Start-App {
    Write-Host "`n[前端 App] 启动 uni-app H5 (端口 5173)..." -ForegroundColor Cyan
    $appDir = Join-Path $ProjectRoot "app"
    if (-not (Test-Path (Join-Path $appDir "package.json"))) {
        Write-Host "  [错误] 找不到 app/package.json" -ForegroundColor Red
        return
    }
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '[前端 App] uni-app 启动中...' -ForegroundColor Cyan; cd '$appDir'; npm run dev:h5"
    Write-Host "  已在新窗口启动 -> http://localhost:5173" -ForegroundColor Green
}

# ============ 启动后台管理 ============
function Start-Admin {
    Write-Host ""
    Write-Host "[后台管理] 启动 Vite (端口 5174)..." -ForegroundColor Cyan
    $adminDir = Join-Path $ProjectRoot "admin-web"
    if (-not (Test-Path (Join-Path $adminDir "package.json"))) {
        Write-Host "  [错误] 找不到 admin-web/package.json" -ForegroundColor Red
        return
    }
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '[后台管理] Vite 启动中...' -ForegroundColor Cyan; cd '$adminDir'; npm run dev"
    Write-Host "  已在新窗口启动 -> http://localhost:5174" -ForegroundColor Green
    Write-Host "  默认账号: admin / admin123 (首次登录需改密)" -ForegroundColor Gray
}

# ============ 执行启动 ============
if ($All) {
    Start-Backend
    Start-Sleep -Seconds 2
    Start-App
    Start-Sleep -Seconds 1
    Start-Admin
}
if ($Backend) { Start-Backend }
if ($App) { Start-App }
if ($Admin) { Start-Admin }

Write-Host ""
Write-Host "========== 启动完成 ==========" -ForegroundColor Cyan
Write-Host "等待各服务初始化完成后，在浏览器打开对应地址。" -ForegroundColor Gray
Write-Host "停止服务: .\start.ps1 -Stop" -ForegroundColor Gray
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""
