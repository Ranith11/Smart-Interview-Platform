import os

# 1. Update CORS in friend backend/app/main.py
main_py = r"C:\Users\kondu\Downloads\Friend-Smart-Interview\Smart-Interview-Platform-main\backend\app\main.py"
with open(main_py, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    'allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"]',
    'allow_origins=["*"]'
)
with open(main_py, "w", encoding="utf-8") as f:
    f.write(text)
print("Updated CORS to allow all origins in friend backend/app/main.py")

# 2. Inspect and update vite.config.js in friend frontend
vite_js = r"C:\Users\kondu\Downloads\Friend-Smart-Interview\Smart-Interview-Platform-main\frontend\vite.config.js"
with open(vite_js, "r", encoding="utf-8") as f:
    vtext = f.read()
print("Original friend vite.config.js:")
print(vtext)

# We want proxy to point to http://localhost:8001 and port 5175
# Let's see what vite.config.js looks like
vtext = vtext.replace("http://localhost:8000", "http://localhost:8001")
if "port: 5175" not in vtext:
    vtext = vtext.replace("server: {", "server: {\n    port: 5175,")
with open(vite_js, "w", encoding="utf-8") as f:
    f.write(vtext)
print("\nUpdated friend vite.config.js:")
print(vtext)
