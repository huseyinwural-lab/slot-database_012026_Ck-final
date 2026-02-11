# 🎰 Casino Platform (Multi-Tenant)

Production-ready, multi-tenant casino administration and player platform.

## 📁 Project Structure

```
/
├── backend/           # FastAPI (Port: 8001) - Core API & Logic
├── frontend/          # React CRA (Port: 3000) - Admin Panel (B2B)
├── frontend-player/   # React Vite (Port: 3001) - Player Lobby (B2C)
└── docker-compose.yml # Orchestration
```

## 🚀 How to Run (The Easy Way: Docker)

If you have Docker Desktop installed:

1.  **Open terminal in this folder.**
2.  **Run:**
    ```bash
    docker-compose up --build
    ```
3.  **Wait** for all services to start.
4.  **Access:**
    *   **Admin Panel:** http://localhost:3000
    *   **Player Lobby:** http://localhost:3001
    *   **API Docs:** http://localhost:8001/docs

*Note: Database (PostgreSQL) will start automatically within Docker.*

---

## 🛠 How to Run (The Developer Way: VS Code)

If you want to code and debug locally without Docker containers for apps:

### 1. Prerequisites
*   Node.js 18+
*   Python 3.11+
*   PostgreSQL (Installed locally or run `docker-compose up postgres -d`)

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

## 📖 User Manuals (Kullanım Kılavuzları)

Detaylı kullanım rehberleri için aşağıdaki dokümanlara göz atın:

*   👑 **[Platform Sahibi Kılavuzu](docs/manuals/PLATFORM_OWNER_GUIDE.md):** Kiracı yaratma, global ayarlar.
*   🏢 **[Kiracı Yönetim Kılavuzu](docs/manuals/TENANT_ADMIN_GUIDE.md):** Operasyon, finans, personel yönetimi.
*   🎰 **[Oyuncu Rehberi](docs/manuals/PLAYER_GUIDE.md):** Kayıt, para yatırma, oyun oynama.

pip install -r requirements.txt
# Dev/local seed (opsiyonel):
#   ENV=dev SEED_ON_STARTUP=true -> startup seeding
# Prod/staging'de seed kapalıdır.
uvicorn server:app --reload --port 8001
```

### 3. Admin Frontend Setup
```bash
cd frontend
yarn install
yarn start
```

### 4. Player Frontend Setup
```bash
cd frontend-player
yarn install
yarn dev --host
```

## 🔑 Initial Access (Staging/Prod)

- **Staging/Prod** ortamlarında seed kapalıdır.
- İlk platform owner hesabı için **BOOTSTRAP_OWNER_EMAIL / BOOTSTRAP_OWNER_PASSWORD** env’lerini verin (one-shot, AdminUser tablosu boşsa oluşturur).
- Tenant admin kullanıcıları owner tarafından oluşturulur (password artık zorunlu).

## 🛠 VS Code Configuration
This project includes `.vscode` folder with:
*   `launch.json`: Pre-configured debuggers for Backend & Chrome.
*   `extensions.json`: Recommended extensions.

Enjoy building! 🚀
