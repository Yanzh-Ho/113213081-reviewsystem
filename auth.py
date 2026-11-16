from fastapi import Request, HTTPException

def chkLogin(role=None):
	def checker(request: Request):
		loginUser = request.session.get("user")        
		if role is None:
			return loginUser                           
		if loginUser is None or loginUser["role"] != role:
			raise HTTPException(status_code=403, detail="沒有權限")   
		return loginUser                               
	return checker