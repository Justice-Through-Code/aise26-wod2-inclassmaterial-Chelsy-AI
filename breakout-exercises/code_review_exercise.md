# Code Review Exercise - In-Class Breakout

**Duration:** 15 minutes  
**Format:** Individual work with team discussion  
**Objective:** Practice identifying security vulnerabilities and writing professional code review comments

---

## The Code to Review

You're reviewing this Python authentication code that has multiple security issues. Your job is to find them and provide professional feedback.

```python
# auth_system.py - Find the security issues
import requests
import sqlite3
import hashlib

API_KEY = "sk-live-1234567890abcdef"
DATABASE_URL = "postgresql://admin:password123@localhost/prod"
DEBUG_MODE = True

def authenticate_user(username, password):
    conn = sqlite3.connect("users.db")
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    
    result = conn.execute(query).fetchone()
    
    print(f"Login attempt: {username}:{password}")
    
    response = requests.post("https://api.auth.com/verify", 
                           data={"user": username, "key": API_KEY})
    
    return response.json()

def reset_password(user_id, new_password):
    conn = sqlite3.connect("users.db")
    query = f"UPDATE users SET password='{new_password}' WHERE id={user_id}"
    conn.execute(query)
    conn.commit()
    
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def admin_check(user_id):
    if user_id == 1 or user_id == "admin":
        return True
    return False
```

---

## Your Task (10 minutes individual work)

**Find and document at least 6 security issues** using this professional format:

```markdown
## Code Review Comments

**🔴 SECURITY: [Issue Type]**
**Line X:** [Specific problem description]
**Impact:** [What could go wrong if exploited]
**Suggestion:** 
```python
# Instead of this vulnerable code:
vulnerable_example()

# Use this secure approach:
secure_example()
```
**Priority:** Critical/High/Medium/Low
```

---

## Hints

- Look for hardcoded secrets and credentials
- Check for SQL injection risks in string-formatted queries
- Watch for logging of sensitive data
- Ensure passwords are hashed with modern algorithms
- Validate inputs and handle errors
- Avoid insecure external API usage without checking responses
- Beware of hidden backdoors and insecure defaults

---

## Team Discussion (5 minutes)

**Share with your breakout room:**
1. Which issues did you find?
2. Which ones did you miss?
3. How would you prioritize fixing them?
4. What was challenging about writing professional review comments?

**Discussion Questions:**
- What makes a code review comment helpful vs. just critical?
- How do you balance being thorough with being constructive?
- What would you want to see in a review of your own code?

---

---

## Real-World Application

These are the exact types of issues you'll encounter in professional code reviews:
- **Hardcoded secrets** appear in ~15% of repositories
- **SQL injection** remains a top security vulnerability
- **Weak password hashing** affects millions of users
- **Missing input validation** leads to data breaches

The review skills you practice here directly apply to protecting your team's production systems.




## Code Review Comments


**🔴 SECURITY: Hardcoded API key and database credentials**
**Line 5–6:** Sensitive values (`API_KEY`, `DATABASE_URL`) are hardcoded in the source code.
**Impact:** Anyone with access to the repo (including attackers) could steal these secrets and access production services or databases.
**Suggestion:**

```python
# Instead of hardcoding secrets:
API_KEY = "sk-live-1234567890abcdef"

# Use environment variables or a secure vault:
import os
API_KEY = os.getenv("AUTH_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
```

**Priority:** Critical

---

**🔴 SECURITY: SQL Injection vulnerability**
**Line 11:** The query uses string interpolation with user-controlled inputs (`username`, `password`).
**Impact:** Attackers could inject malicious SQL (e.g., `' OR '1'='1`) to bypass authentication or exfiltrate data.
**Suggestion:**

```python
# Instead of unsafe string formatting:
query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"

# Use parameterized queries:
query = "SELECT * FROM users WHERE username=? AND password=?"
result = conn.execute(query, (username, password)).fetchone()
```

**Priority:** Critical

---

**🔴 SECURITY: Logging sensitive data**
**Line 14:** `print(f"Login attempt: {username}:{password}")` logs plaintext credentials.
**Impact:** Credentials could leak to console logs, monitoring systems, or error reports, enabling credential theft.
**Suggestion:**

```python
# Do not log plaintext credentials:
print(f"Login attempt for user: {username}")
```

**Priority:** High

---

**🔴 SECURITY: Weak password hashing (MD5)**
**Line 30:** Passwords are hashed using `hashlib.md5`, which is broken and easily brute-forced.
**Impact:** If the database is compromised, attackers can crack hashes within minutes.
**Suggestion:**

```python
# Instead of MD5:
import hashlib
hashlib.md5(password.encode()).hexdigest()

# Use bcrypt or Argon2:
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

**Priority:** Critical

---

**🔴 SECURITY: Insecure password reset**
**Line 24:** The `reset_password` function updates passwords in plaintext and allows direct injection via `user_id` and `new_password`.
**Impact:** Attackers could overwrite arbitrary users’ passwords or escalate privileges.
**Suggestion:**

```python
# Instead of string formatting with unvalidated input:
query = f"UPDATE users SET password='{new_password}' WHERE id={user_id}"

# Use parameterized queries and hash new passwords:
query = "UPDATE users SET password=? WHERE id=?"
conn.execute(query, (hash_password(new_password), user_id))
```

**Priority:** Critical

---

**🔴 SECURITY: Hardcoded backdoor in admin check**
**Line 34:** `if user_id == 1 or user_id == "admin":` grants admin access by ID or username string.
**Impact:** An attacker could simply log in with the username `"admin"` to gain full admin privileges.
**Suggestion:**

```python
# Instead of hardcoded admin bypass:
if user_id == 1 or user_id == "admin":
    return True

# Check against a properly stored user role in the database:
query = "SELECT role FROM users WHERE id=?"
role = conn.execute(query, (user_id,)).fetchone()
return role == "admin"
```

**Priority:** Critical

---

## Overall Review Comment

This authentication module contains multiple severe security issues, including **hardcoded secrets, SQL injection, plaintext logging, weak password hashing, insecure password resets, and a hardcoded admin backdoor**. These vulnerabilities make the system trivial to exploit and unsafe for production. I strongly recommend refactoring to use **secure credential management, parameterized queries, strong password hashing (bcrypt/Argon2), secure logging practices, and role-based access control**. Addressing these issues should be treated as **urgent** before deployment.

---
