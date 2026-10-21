# BizAdvisor — AI Business Advisory Agent

An enterprise-grade, full-stack **Business Advisory Agent** and decision-support platform designed to evaluate restaurant and hospitality business ventures. BizAdvisor integrates **Google ADK multi-agent orchestration**, a **Random Forest machine learning model**, **SHAP explainability**, live **Google Places competitor intelligence**, an assumption-driven **financial simulator**, and interactive **What-If scenario analysis** with a modern **React 19** frontend and a secured **FastAPI / MySQL** backend.

---

## 1. Key Features

* **Conversational Business Advisory:** Interactive AI chat experience that extracts business concepts (location, cuisine, cost for two, dining type) and provides structured feasibility reports.
* **Google ADK Multi-Agent Orchestration:** Specialized agents (Coordinator, Location, Performance, Competition, and Opportunity) orchestrated via Google Agent Development Kit (ADK) with flexible LLM providers (Groq / Gemini / OpenAI compatible).
* **Machine Learning Performance Prediction:** Pre-trained Random Forest classifier estimating restaurant performance category and success probability based on historical market trends.
* **SHAP Explainability:** TreeExplainer-driven feature attribution showing top positive and negative contributors behind each performance prediction.
* **Google Places Competitor Discovery:** Live nearby competitor discovery capturing business names, ratings, review counts, price levels, and coordinates with deterministic fallback logic.
* **Location Intelligence:** Geospatial context evaluating historical restaurant density, median spend, cuisine diversity, and online ordering adoption.
* **Deterministic Financial Simulator:** Transparent revenue, variable expense, itemized fixed costs, operating profit (EBITDA proxy), margin, and contribution-margin break-even analysis with editable assumption sliders.
* **What-If Scenario Simulator:** Dynamic comparative scenario modeling allowing entrepreneurs to simulate changes in cost for two, table booking, or online ordering before committing capital.
* **Enterprise Security & Authentication:** User registration and login powered by Argon2id password hashing, signed JWT bearer tokens with strict configuration validation, IP rate-limiting on sensitive auth routes (`slowapi`), and strict CORS controls.
* **User-Scoped Conversation Persistence:** Persistent conversation and message history stored in MySQL with foreign key cascading and strict ownership enforcement preventing cross-user data leakage.

---

## 2. Technology Stack

### Frontend
* **Framework:** React 19 (Single Page Application)
* **Build Tool:** Vite
* **Styling:** Tailwind CSS / Vanilla CSS with glassmorphism, responsive grid layouts, and dark/light modes
* **Icons:** Lucide React
* **HTTP Client:** Native Fetch / Custom API Service with bearer token authorization

### Backend & API
* **Web Framework:** FastAPI (ASGI)
* **Server:** Uvicorn
* **Data Validation:** Pydantic v2
* **Authentication:** PyJWT (HS256 tokens) & Argon2id (`argon2-cffi`)
* **Rate Limiting:** SlowAPI (Redis / In-memory token bucket)
* **Agent Framework:** Google ADK (`google-adk`), Google GenAI (`google-genai`), and LiteLLM (`litellm`)

### Database & Persistence
* **Relational Database:** MySQL 8.0+
* **ORM:** SQLAlchemy 2.0+
* **Driver:** PyMySQL

### Machine Learning & Data Science
* **Classifier:** Scikit-Learn (Random Forest Classifier) & XGBoost
* **Explainability:** SHAP (TreeExplainer)
* **Data Processing:** Pandas, NumPy, Scipy, Joblib
* **Spatial & Geometry:** GeoPandas, Shapely, OSMnx

---

## 3. Project Architecture & Directory Structure

```text
Business_Analysis_Agent/
├── .env.example                     # Environment configuration template
├── README.md                        # Project documentation
├── requirements.txt                 # Backend Python dependencies
├── server.py                        # FastAPI main application & API routes
│
├── data/
│   ├── processed/
│   │   └── zomato_train_engineered.csv  # Runtime feature store for location context
│   └── backups/                     # Safety backups of database dumps (git-ignored)
│
├── models/
│   ├── zomato_performance_model.pkl # Trained Random Forest classifier
│   └── zomato_preprocessor.pkl      # Feature encoding and scaling pipeline
│
├── notebooks/                       # Provenance: Offline exploration & training
│   ├── 01_zomato_exploration.ipynb
│   ├── 02_zomato_cleaning.ipynb
│   ├── 03_zomato_eda.ipynb
│   ├── 04_zomato_feature_engineering.ipynb
│   ├── 05_zomato_model_training.ipynb
│   └── 06_google_places_competition.ipynb
│
├── scripts/                         # Maintenance & migration utilities
│   ├── backup_database.py           # Database backup utility script
│   ├── migrate_add_users.py         # Migration adding user authentication schema
│   └── migrate_sqlite_to_mysql.py   # Historical SQLite to MySQL migration script
│
├── src/                             # Core backend application modules
│   ├── auth.py                      # Argon2id hashing, JWT validation, auth dependencies
│   ├── database.py                  # SQLAlchemy engine, session maker, and ORM models
│   ├── agent/                       # Google ADK multi-agent system
│   │   ├── coordinator_agent.py     # Master coordinator orchestrating workflow
│   │   ├── competition_agent.py     # Competitor discovery agent
│   │   ├── location_agent.py        # Location analysis agent
│   │   ├── opportunity_agent.py     # Opportunity synthesis agent
│   │   ├── performance_agent.py     # ML prediction and explainability agent
│   │   ├── adk_runner.py            # ADK execution runtime bridge
│   │   └── llm_config.py            # LiteLLM / Gemini model configuration
│   ├── analysis/
│   │   ├── location_context.py      # Runtime location statistics lookup
│   │   ├── opportunity.py           # Opportunity scoring logic
│   │   └── what_if.py               # Scenario simulation engine
│   ├── finance/
│   │   └── simulator.py             # Deterministic financial modeling & break-even engine
│   ├── ml/
│   │   ├── predictor.py             # Model inference wrapper
│   │   └── explainer.py             # SHAP explanation generator
│   └── places/
│       └── competition.py           # Google Places API integration & fallback
│
├── tests/                           # Automated regression & integration test suite
│   ├── test_financial_accuracy.py   # 11 tests for financial accuracy and break-even
│   ├── test_security.py             # 14 tests for auth, JWT, rate-limiting, and isolation
│   ├── test_mysql_integration.py    # 4 tests for database CRUD and cascading
│   └── test_mysql_regression.py     # 4 tests for session lifecycles and recovery
│
└── frontend/                        # React 19 + Vite frontend application
    ├── index.html                   # HTML entry point
    ├── package.json                 # Node dependencies and scripts
    ├── vite.config.js               # Vite bundler configuration
    └── src/
        ├── App.jsx                  # Root React application component
        ├── components/
        │   ├── Analysis/            # FinancialCard, PerformanceCard, CompetitorCard, etc.
        │   ├── Auth/                # AuthModal (Login & Registration)
        │   ├── Chat/                # ChatMessage, ChatInput, AnalysisProgress
        │   ├── Map/                 # Competitor modal and location views
        │   ├── Scenario/            # What-If scenario comparison modal
        │   └── Sidebar/             # Conversation history sidebar
        └── services/
            └── api.js               # Centralized frontend API client
```

---

## 4. Prerequisites for Development

* **Operating System:** Windows 10/11 (or Linux/macOS with equivalent shell commands)
* **Python:** Python 3.11, 3.12, or 3.13 (64-bit)
* **Node.js:** Node.js v18.0+ or v20.0+ and `npm`
* **Database:** MySQL Server 8.0+ running locally or accessible remotely
* **External API Keys (Optional but Recommended):**
  * Google Maps / Places API key (for live competitor discovery).
  * Groq API key or Google Gemini API key (for Google ADK conversational reasoning).

---

## 5. Installation & Setup

### Step 1: Clone the Repository
```powershell
git clone https://github.com/your-username/Business_Analysis_Agent.git
cd Business_Analysis_Agent
```

### Step 2: Configure Python Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment in PowerShell
.\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install backend dependencies
pip install -r requirements.txt
```

### Step 3: Install Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

---

## 6. Environment Configuration

1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Generate a cryptographically secure 256-bit JWT secret key in PowerShell:
   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
3. Open `.env` in your editor and configure the variables:

| Variable | Description | Required? | Example / Default |
| :--- | :--- | :--- | :--- |
| `JWT_SECRET_KEY` | Secret key for signing authentication tokens (min 32 chars) | **Yes** | *Generated 64-char hex string* |
| `JWT_ALGORITHM` | JWT signing algorithm | **Yes** | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifespan in minutes | **Yes** | `60` |
| `MYSQL_HOST` | MySQL database host address | **Yes** | `localhost` |
| `MYSQL_PORT` | MySQL database port | **Yes** | `3306` |
| `MYSQL_USER` | MySQL database user | **Yes** | `root` |
| `MYSQL_PASSWORD` | MySQL database password | **Yes** | *Your local MySQL password* |
| `MYSQL_DATABASE` | MySQL database name | **Yes** | `bizadvisor_db` |
| `CORS_ALLOWED_ORIGINS` | Permitted origins for frontend CORS | **Yes** | `http://localhost:5173,http://127.0.0.1:5173` |
| `GOOGLE_MAPS_API_KEY` | Google Places API key for competitor lookup | Optional | *(Uses deterministic fallback if omitted)* |
| `PRIMARY_LLM_PROVIDER` | Primary LLM provider | Optional | `groq` |
| `PRIMARY_LLM_MODEL` | Primary LLM model name | Optional | `openai/gpt-oss-120b` |
| `PRIMARY_LLM_API_KEY` | API key for primary LLM | Optional | *Your API Key* |
| `PRIMARY_LLM_BASE_URL` | Base URL for LLM API | Optional | `https://api.groq.com/openai/v1` |

> [!WARNING]
> Never commit your `.env` file or hardcode credentials into source code. `.env` is ignored by `.gitignore`.

---

## 7. Database Setup & Initialization

1. Ensure MySQL server is running. Create the database:
   ```sql
   CREATE DATABASE IF NOT EXISTS bizadvisor_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. **Automatic Schema Creation:** When `server.py` starts, SQLAlchemy automatically creates the required tables (`users`, `conversations`, `messages`) if they do not already exist.
3. **Database Migration Script (for existing databases):**
   If you have an existing database from an earlier version, run the migration script:
   ```powershell
   python scripts/migrate_add_users.py
   ```
   > [!NOTE]
   > Always back up your database before running migrations. A backup utility is provided in `scripts/backup_database.py`.

---

## 8. Running the Application

Open **two separate PowerShell terminal windows**:

### Terminal 1: Backend API (FastAPI)
```powershell
# From the project root
.\.venv\Scripts\Activate.ps1
uvicorn server:app --reload --host 127.0.0.1 --port 8000
```
* Backend API runs at: `http://127.0.0.1:8000`
* Interactive API Documentation (Swagger): `http://127.0.0.1:8000/docs`

### Terminal 2: Frontend Dashboard (React / Vite)
```powershell
# From the project root
cd frontend
npm run dev
```
* Frontend Dashboard runs at: `http://localhost:5173`

---

## 9. API Reference

All protected endpoints require an `Authorization: Bearer <token>` header obtained from `/api/auth/login`.

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | No | Register a new user with username, email, and password. |
| `POST` | `/api/auth/login` | No | Authenticate user; returns JWT token. Rate-limited to 5 req/min. |
| `GET` | `/api/auth/me` | **Yes** | Retrieve currently authenticated user's profile. |
| `GET` | `/api/health` | No | Health check returning service and database status. |
| `POST` | `/api/analyze` | Optional | Execute full business analysis for location, cuisine, cost, and parameters. |
| `POST` | `/api/chat` | Optional | Multi-turn chat message endpoint with session context persistence. |
| `POST` | `/api/scenario` | Optional | Run What-If scenario simulation comparing baseline against modified parameters. |
| `POST` | `/api/financial/simulate` | Optional | Recalculate deterministic financial metrics on demand. |
| `GET` | `/api/history` | **Yes** | List all past conversation sessions owned by the authenticated user. |
| `GET` | `/api/history/{session_id}` | **Yes** | Fetch message history and structured analysis for a session. |
| `DELETE`| `/api/history/{session_id}` | **Yes** | Delete conversation and cascading messages owned by the user. |

---

## 10. Machine Learning & Model Artifacts

* **Trained Classifier:** [`models/zomato_performance_model.pkl`](models/zomato_performance_model.pkl) is a trained Random Forest model predicting business viability tiers based on historical Zomato restaurant performance metrics in Bengaluru.
* **Preprocessor:** [`models/zomato_preprocessor.pkl`](models/zomato_preprocessor.pkl) handles feature scaling, one-hot encoding, and categorical imputation.
* **Runtime Location Store:** [`data/processed/zomato_train_engineered.csv`](data/processed/zomato_train_engineered.csv) is loaded at runtime by `src/analysis/location_context.py` to calculate historical location density, median price, online order adoption, and cuisine diversity.
* **Explainability:** SHAP values are dynamically generated by `src/ml/explainer.py` to explain feature impact (e.g., impact of cost-for-two, table booking availability, cuisine popularity).
* **Research Provenance:** The 6 Jupyter notebooks in `notebooks/` document data cleaning, feature engineering, exploratory data analysis, model training, and Places API prototyping.

---

## 11. Financial Simulation Engine

The financial engine ([`src/finance/simulator.py`](src/finance/simulator.py)) uses standard management accounting principles:

### Core Formulas:
1. **Average Spend per Customer (Estimate):**
   $$\text{Average Spend} = \frac{\text{Cost for Two}}{2}$$
   *(Modeled as an assumption-based estimate, not a guaranteed customer spend)*
2. **Monthly Projected Revenue:**
   $$\text{Monthly Revenue} = \text{Daily Customers} \times \text{Operating Days per Month} \times \text{Average Spend}$$
3. **Variable Operating Costs:**
   $$\text{Variable Costs} = \text{Monthly Revenue} \times \left(\frac{\text{Variable Cost Percentage}}{100}\right)$$
4. **Fixed Operating Costs:**
   $$\text{Fixed Operating Costs} = \text{Rent} + \text{Staff Costs} + \text{Utilities} + \text{Marketing} + \text{Other Fixed Costs}$$
5. **Total Monthly Operating Expenses:**
   $$\text{Total Operating Expenses} = \text{Variable Costs} + \text{Fixed Operating Costs}$$
6. **Estimated Operating Profit (EBITDA Proxy):**
   $$\text{Operating Profit} = \text{Monthly Revenue} - \text{Total Operating Expenses}$$
7. **Contribution Margin & Break-Even Analysis:**
   $$\text{Contribution Margin Ratio} = 1 - \left(\frac{\text{Variable Cost Percentage}}{100}\right)$$
   $$\text{Break-Even Customers per Day} = \frac{\text{Fixed Operating Costs}}{\text{Average Spend} \times \text{Contribution Margin Ratio} \times \text{Operating Days}}$$
   $$\text{Break-Even Target (Whole Number)} = \lceil \text{Break-Even Customers per Day} \rceil$$

### Financial Disclaimers & Exclusions:
* **Operating Profit vs. Net Profit:** Projections represent operating profit before corporate taxes, GST, interest on financing, depreciation on kitchen assets, and owner equity distributions.
* **Third-Party Commissions:** Food delivery platform aggregator commissions (15%–25%) and payment gateway charges are not included in base assumptions and must be factored into Variable Costs by the user.

---

## 12. Running Automated Tests

The repository contains an automated regression and security test suite:

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run all 33 regression, security, and financial tests
pytest -v tests/

# Run focused financial accuracy tests only
pytest -v tests/test_financial_accuracy.py

# Run security and authentication tests only
pytest -v tests/test_security.py

# Run database integration tests only
pytest -v tests/test_mysql_integration.py
```

### Frontend Production Build Verification:
```powershell
cd frontend
npm run build
```

---

## 13. Limitations & Considerations

1. **Geographic Coverage:** The pre-trained Random Forest model and location feature store are grounded in historical restaurant market data from Bengaluru, Karnataka. While the multi-agent system and Google Places competitor analysis function globally, historical performance inferences are strongest in urban Indian dining markets.
2. **Assumption Sensitivity:** Financial projections rely on user-configurable inputs (daily footfall, average order size, rent, staff costs). Real-world outcomes depend heavily on operational execution, food quality, seasonality, and local regulations.
3. **External API Dependence:** Live competitor discovery requires a valid Google Places API key; in its absence, the engine automatically falls back to deterministic historical benchmarks.
4. **Single-Node Deployment:** In-memory rate limiting (`slowapi`) and local SQLite sessions are suitable for single-node instances. Production multi-instance deployments should configure a distributed Redis backend.

---

## 14. GitHub Security & Contribution Checklist

Before pushing to a public or shared GitHub repository:
- [x] Verify `.env` is listed in `.gitignore` and not tracked by Git (`git status`).
- [x] Verify no hardcoded passwords, tokens, or API keys exist in source files.
- [x] Verify database dump files or user export files in `data/` are excluded.
- [x] Run `pytest -v tests/` to confirm all 33 automated tests pass.
- [x] Run `npm run build` in `frontend/` to ensure the React bundle compiles without errors.