
#  Tafuta Roomie – Core

A robust **RESTful backend API** built with **Django** and **Django Rest Framework (DRF)** for the **Tafuta Roomie** mobile application.  
This backend powers authentication, intelligent roommate matching, room listings, real-time messaging, and identity verification.

---

## 🚀 Features

- 🔐 **Authentication** – Secure user registration & login using JWT (JSON Web Tokens)
- 👤 **User Profiles** – Lifestyle preferences (smoking, pets, sleep schedule, etc.)
- ❤️ **Matching Engine** – Weighted compatibility algorithm for roommate matching
- 🏠 **Room Listings** – Create & browse room ads with multiple image uploads
- 💬 **Messaging System** – Private conversations between users
- ✅ **Identity Verification** – Admin-approved ID verification (Blue Tick system)
- 📄 **API Documentation** – Swagger UI & Redoc (auto-generated)
- 🐳 **Dockerized** – Fully containerized for easy setup & deployment

---

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Framework:** Django 5.x, Django Rest Framework
- **Database:** PostgreSQL 15
- **Authentication:** djangorestframework-simplejwt
- **Documentation:** drf-spectacular (Swagger / Redoc)
- **Image Processing:** Pillow
- **Infrastructure:** Docker & Docker Compose

---

## 📋 Prerequisites

Ensure you have the following installed:

- Docker Desktop
- Git

---

## ⚡️ Quick Start

### 1️⃣ Clone the Repository
```bash
git clone <your-repo-url>
cd roommate_backend
````

---

### 2️⃣ Create Environment Variables (Optional but Recommended)

Create a `.env` file in the root directory:

```env
DB_NAME=roommate_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

---

### 3️⃣ Build & Run with Docker

```bash
docker-compose up -d --build
```

---

### 4️⃣ Run Database Migrations

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

---

### 5️⃣ Create Admin (Superuser)

```bash
docker-compose exec web python manage.py createsuperuser
```

---

## 🌐 Access the Application

* **API Root:** [http://localhost:8000/api/](http://localhost:8000/api/)
* **Admin Panel:** [http://localhost:8000/admin/](http://localhost:8000/admin/)
* **Swagger Docs:** [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
* **Redoc Docs:** [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)

---

## 📖 API Documentation

Interactive documentation is available once the server is running:

* **Swagger UI:**
  [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
* **Redoc:**
  [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)

---

## 🔑 Key API Endpoints

| Method | Endpoint                    | Description                                 |
| ------ | --------------------------- | ------------------------------------------- |
| POST   | `/api/register/`            | Register a new user                         |
| POST   | `/api/login/`               | Login & receive JWT tokens                  |
| GET    | `/api/matches/`             | Get ranked roommate matches                 |
| GET    | `/api/listings/`            | Browse room listings                        |
| POST   | `/api/listings/`            | Create a room listing (multipart/form-data) |
| POST   | `/api/conversations/start/` | Start a chat                                |
| POST   | `/api/verifications/`       | Upload ID for verification                  |

---

## 🛡️ Identity Verification Workflow

1. **User:** Uploads ID via `/api/verifications/`
2. **Admin:** Logs into `/admin`
3. Navigate to **User Verifications**
4. Review uploaded ID
5. Select user(s) → **“✅ Approve selected verifications”**
6. User profile is updated with `is_verified = True` (Blue Tick)

---

## 📂 Project Structure

```bash
roommate_backend/
├── core/                   # Main application logic
│   ├── models.py           # Database models
│   ├── views.py            # API views
│   ├── serializers.py      # DRF serializers
│   ├── admin.py            # Admin configuration
│   └── urls.py             # API routes
├── roommate_project/
│   ├── settings.py         # Project settings
│   └── urls.py             # Root URL configuration
├── media/                  # Uploaded media files
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── manage.py
```

---

## 🔧 Useful Docker Commands

| Command                                            | Description        |
| -------------------------------------------------- | ------------------ |
| `docker-compose up -d`                             | Start services     |
| `docker-compose down`                              | Stop services      |
| `docker-compose logs -f web`                       | View backend logs  |
| `docker-compose exec web python manage.py migrate` | Run migrations     |
| `docker-compose exec web pip install <package>`    | Install dependency |

> ⚠️ Remember to add new packages to `requirements.txt`

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch

   ```bash
   git checkout -b feature/YourFeature
   ```
3. Commit your changes

   ```bash
   git commit -m "Add YourFeature"
   ```
4. Push to the branch

   ```bash
   git push origin feature/YourFeature
   ```
5. Open a Pull Request

---

## ❤️ Credits

Built with passion by **DEHUKS**

---
