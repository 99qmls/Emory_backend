# tests/test_api/test_jwt.py
import sys
import os
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv  # 用于读取 .env 文件

# ---------------------------
# 临时添加项目根目录到 sys.path，保证可以导入 app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
# ---------------------------

from app.core.config import settings  # 导入你的 settings.py 中的 settings 对象

# ===================== 读取 .env =====================
# 确保 .env 在项目根目录
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))

# 从 .env 获取前端 token
FRONTEND_TOKEN = os.getenv("FRONTEND_TOKEN", "")

# ===================== 打印后端 key =====================
print("后端 SECRET_KEY 前5位:", settings.SECRET_KEY[:5])
print("JWT 签名算法:", settings.ALGORITHM)
print("当前 UTC 时间:", datetime.utcnow())

# ===================== 验证 token =====================
def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print("✅ Token 验证成功！Payload:", payload)
        # 检查是否过期
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            exp = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            if exp < now:
                print("⚠️ Token 已过期！")
            else:
                print(f"Token 还有效，过期时间: {exp}")
    except JWTError:
        print("❌ Token 验证失败，签发 key 与验证 key 不一致或 token 已过期")

# ===================== 主流程 =====================
if FRONTEND_TOKEN:
    print("\n== 验证前端 token ==")
    verify_token(FRONTEND_TOKEN)
else:
    print("\n⚠️ FRONTEND_TOKEN 为空，自动生成临时 token 测试")

# ===================== 临时生成 token 测试 =====================
print("\n== 临时生成 token 测试 ==")
payload = {
    "sub": "test-user-id",
    "exp": datetime.utcnow() + timedelta(minutes=30)
}
temp_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
print("生成 token:", temp_token)
verify_token(temp_token)