# Merge Conflict Exercise - Theory Breakout

**Duration:** 15 minutes  
**Format:** Group discussion (no coding)  
**Objective:** Reason about intelligent merge conflict resolution strategies

---

## Scenario Setup

Two developers worked on the same Python API file simultaneously:

**Branch A (Authentication):** Added login validation and JWT tokens  
**Branch B (Database):** Added database integration and user persistence

You need to merge both branches intelligently, preserving the best of both features.

---

## Branch A: Authentication Features

```python
from flask import Flask, request, jsonify
import jwt
import bcrypt
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # Input validation added
    if not data.get('username') or len(data.get('username', '')) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    
    if not data.get('password') or len(data.get('password', '')) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    
    # Secure password hashing
    password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
    return jsonify({
        "id": 1, 
        "username": data['username'],
        "message": "User created successfully"
    })

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Validate credentials (simplified for demo)
    if username and password:
        # Generate JWT token
        token = jwt.encode({
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'])
        
        return jsonify({"token": token, "message": "Login successful"})
    
    return jsonify({"error": "Invalid credentials"}), 401
```

---

## Branch B: Database Features

```python
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

# Database setup
engine = create_engine('sqlite:///users.db')
Base = declarative_base()
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)

Base.metadata.create_all(engine)

@app.route('/users', methods=['GET'])
def get_users():
    session = Session()
    users = session.query(User).all()
    result = [{"id": u.id, "username": u.username} for u in users]
    session.close()
    return jsonify({"users": result})

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    session = Session()
    
    user = User(
        username=data.get('username'),
        password=data.get('password')  # This needs the secure hashing from Branch A!
    )
    
    session.add(user)
    session.commit()
    
    result = {"id": user.id, "username": user.username}
    session.close()
    return jsonify(result)
```

---

## Discussion Challenge (15 minutes)

### Step 1: Analyze Both Branches (3 minutes)
**What does each branch accomplish?**

**Branch A (Authentication):**
- Input validation for user creation
- Secure password hashing with bcrypt
- JWT token generation for login
- Proper error handling

**Branch B (Database):**
- SQLAlchemy ORM for data persistence  
- User model with database schema
- Get users endpoint
- Session management

### Step 2: Plan an Integration Strategy (3 minutes)
Discuss how you would combine these features in principle. Identify risks, ordering, and validation points.

Target outcomes:
- ✅ Use database persistence from Branch B
- ✅ Include input validation from Branch A
- ✅ Use secure password hashing from Branch A
- ✅ Have JWT authentication from Branch A
- ✅ Keep all endpoints working

### Step 3: Outline an Approach (7 minutes)
Whiteboard or outline the sequence of steps you would take to perform the merge (branches to create, tests to run, order of resolving conflicts, checkpoints for validation). No coding required.

### Step 4: What Would You Test? (2 minutes)
Walk through what you would test after resolving conflicts:
- Does user creation validate input AND save to database?
- Does password hashing work with database storage?
- Are all imports included?
- Do all endpoints still work?

---

## Discussion Questions (Team sharing)

1. **What was your strategy for combining the features?**
2. **What conflicts would you expect and how would you resolve them?**
3. **What would you test to make sure your merge works?**
4. **How is an intelligent merge different from just "picking one side"?**

---

---

## Real-World Application

This mirrors actual development scenarios:
- **Feature teams** often work on overlapping code
- **Good merges** preserve everyone's work
- **Smart resolution** is better than random conflict picking
- **Testing** your merge prevents broken deployments

The skills you practice here prevent the "it worked on my machine" problems that break production systems.







---

## 📝 Merge Conflict Exercise – Suggested Walkthrough

### Step 1: Analyze Both Branches

* **Branch A (Authentication):** Strengthens security: input validation, bcrypt password hashing, JWT tokens, and error handling.
* **Branch B (Database):** Adds persistence layer: SQLAlchemy ORM, user model, session handling, and an extra `GET /users` endpoint.

✅ Together they form a secure, persistent authentication system.

---

### Step 2: Plan Integration Strategy

* Start from Branch B (since it has database foundation).
* Merge in Branch A’s **validation, hashing, and JWT login logic**.
* Update `create_user` in Branch B to:

  * Perform **input validation** (Branch A).
  * Hash the password before saving (Branch A).
  * Save hashed password into DB (Branch B).
* Ensure `login` endpoint checks database credentials (currently Branch A just trusts input).
* Keep Branch B’s `get_users` intact.

---

### Step 3: Outline Merge Approach

1. **Create a feature branch for the merge** (avoid directly merging into `main`).

   ```bash
   git checkout -b merge/auth-db
   ```
2. **Merge Branch B into base** (to establish DB schema).
3. **Merge Branch A into the new branch**, expect conflicts around `create_user`.
4. **Resolve conflicts:**

   * Keep Branch A’s validation and bcrypt hashing.
   * Keep Branch B’s DB persistence, modify it to store `password_hash`.
5. **Refactor login** to pull user from DB and validate bcrypt hash.
6. **Run tests/checkpoints:**

   * `POST /users` creates validated + hashed + persisted users.
   * `GET /users` lists users (without exposing passwords).
   * `POST /login` issues JWT after password check.
7. **Commit the merge resolution** and run integration tests.

---

### Step 4: What to Test After Merge

* **User creation flow:** Invalid username/password blocked; valid user stored with bcrypt hash.
* **Database integrity:** Password column stores hashes, not plaintext.
* **Authentication flow:** Login verifies against bcrypt hash from DB and returns JWT.
* **Endpoints health:** `/users [POST]`, `/users [GET]`, `/login` all work without errors.
* **Security regression:** No plaintext passwords in logs, no missing validation.

---

## Discussion Questions (for team sharing)

1. **Strategy:** Combine DB persistence with security features. Don’t drop one side.
2. **Conflicts:** Mainly in `create_user` function, imports, and overlapping route definitions.
3. **Testing:** Cover validation, persistence, login, token generation.
4. **Smart Merge vs “Pick One”:** Intelligent merging = weaving both contributions. Picking one side would either lose persistence or security.

---

✅ **Real-World Takeaway:** An intelligent merge means preserving the **best of both branches** (security + persistence), not just resolving syntax conflicts. Testing ensures the merged code is reliable in production.

---
