PYTHON VERSION: 3.11.9

go to project folder:
	git pull origin dev or main
	then go to backend folder in project folder and:


### 1. Create virtual environment

**Windows**

```
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS**

```
python3 -m venv venv
source venv/bin/activate
```

---

### 2. Install dependencies

```
python -m pip install -r requirements.txt
```

---

### 3. Start the server

```
(local machine)
python -m uvicorn main:app --reload

(local network)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

### 4. Open API docs

```
http://127.0.0.1:8000/docs
```