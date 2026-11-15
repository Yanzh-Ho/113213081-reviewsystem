from fastapi import Request, HTTPException

def chkLogin(role=None):
	def checker(request: Request):
		loginUser = request.session.get("user")        # 看號碼牌
		if role is None:
			return loginUser                            # 沒指定角色：只回傳有沒有登入
		if loginUser is None or loginUser["role"] != role:
			raise HTTPException(status_code=403, detail="沒有權限")   # 擋掉
		return loginUser                                # 通過，把登入者交出去
	return checker