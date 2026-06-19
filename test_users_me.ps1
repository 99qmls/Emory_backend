# =========================
# FastAPI /users/me 测试脚本
# Windows PowerShell
# =========================

# 配置：修改为你的后端地址和 token
$backendUrl = "http://127.0.0.1:7000/api/v1/users/me"
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1YzIyYzkxZS0wZjAyLTQ2ZTEtYTgxYy0xNzQyODgzMTg0YzYiLCJleHAiOjE3Nzg4MTY5NzV9.ggJ0oKQ48BPtBoNUeB8B94r5QJ8VTR7KE-5eYQqlfZM"

Write-Host "=== 测试 FastAPI /users/me 接口 ===" -ForegroundColor Cyan
Write-Host "后端地址: $backendUrl"
Write-Host "Token 前5位: $($token.Substring(0,5))"

# 发送 GET 请求
try {
    $response = curl -v --globoff -H "Authorization: Bearer $token" $backendUrl
} catch {
    Write-Host "❌ 请求失败：" $_.Exception.Message -ForegroundColor Red
    exit 1
}

# 输出 HTTP 状态码
$httpStatus = $response.StatusCode
Write-Host "`nHTTP 状态码: $httpStatus"

# 输出原始响应
Write-Host "`n=== 响应内容 ==="
$response.Content | Write-Host

# 尝试解析 JSON
try {
    $json = $response.Content | ConvertFrom-Json
    Write-Host "`n=== JSON 解析结果 ===" -ForegroundColor Green
    $json | Format-List
} catch {
    Write-Host "⚠️ 无法解析 JSON"
}