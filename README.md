# AI Business Advisory Agent

An AI-powered business advisory system for food and restaurant business ideas using **Google ADK, Gemini, Machine Learning, historical Zomato data, and live Google Places data**.

The system uses a **multi-agent architecture** in which a Coordinator Agent delegates work to specialized agents for location analysis, performance prediction, competition analysis, and opportunity assessment.

For example:

> I want to open a premium Japanese restaurant in Koramangala, Bengaluru.

The system understands the request, determines which analysis is needed, delegates the task to the appropriate specialist agents, and presents the results as a user-friendly business report.

---

## Features

* Natural-language business idea analysis
* Multi-agent architecture using Google ADK
* Coordinator Agent for intent-based delegation
* Specialized Location Agent
* Specialized Performance Agent
* Specialized Competition Agent
* Specialized Opportunity Agent
* Historical location analysis using Zomato data
* Random Forest-based historical performance prediction
* Live competitor discovery using Google Places API
* Competitor rating and review analysis
* Competition strength scoring
* Business opportunity scoring
* Structured, data-backed business insights
* Protection against unsupported or hallucinated numerical results
* Conversation-aware responses and user-friendly explanations

---

## Multi-Agent Architecture

```text
                         USER
                           |
                           v
                 +------------------+
                 |   COORDINATOR    |
                 |      AGENT       |
                 +--------+---------+
                          |
          +---------------+----------------+
          |               |                |
          v               v                v
 +----------------+ +----------------+ +----------------+
 |    LOCATION    | |  PERFORMANCE   | |  COMPETITION   |
 |     AGENT      | |     AGENT      | |     AGENT      |
 +-------+--------+ +-------+--------+ +-------+--------+
         |                  |                  |
         v                  v                  v
 Historical Zomato     Random Forest      Google Places
 Location Context      Performance       Competitor Data
                       Prediction
          \                  |                  /
           \                 |                 /
            +---------------+----------------+
                            |
                            v
                  +-------------------+
                  |   OPPORTUNITY     |
                  |       AGENT       |
                  +---------+---------+
                            |
                            v
                    Opportunity Score
                    + Business Signals
                            |
                            v
                  +-------------------+
                  |    COORDINATOR    |
                  |  Final Synthesis  |
                  +---------+---------+
                            |
                            v
                           USER
```

### Agent Responsibilities

**Coordinator Agent**

* Understands the user's intent.
* Determines which specialist agents are required.
* Delegates only the relevant tasks for focused requests.
* Coordinates the analysis for complete business requests.
* Presents the final results in a clear, user-friendly format.
* Maintains the user's requested response language/style, such as Hinglish.

**Location Agent**

* Analyzes historical location-level information from the processed Zomato dataset.
* Reports restaurant density, median cost, online ordering rate, table-booking rate, cuisine diversity, and business-type diversity where available.

**Performance Agent**

* Uses the trained Random Forest model.
* Predicts historical business performance as Low, Medium, or High.
* Returns class probabilities.
* Does not treat model probabilities as guaranteed real-world success probabilities.

**Competition Agent**

* Uses Google Places API to discover nearby candidate businesses.
* Filters candidates using the project's supported business types.
* Calculates competitor counts, ratings, review statistics, and competition metrics.
* Returns the structured competition data used by the system.

**Opportunity Agent**

* Combines the historical performance probabilities and competition summary.
* Uses the project's deterministic opportunity-scoring logic.
* Returns opportunity score, historical performance signal, and competition strength signal.

---

## Intent-Based Delegation

The Coordinator does not need to call every agent for every request.

For example:

```text
User asks only about competitors
        |
        v
Competition Agent only
```

```text
User asks only about historical location
        |
        v
Location Agent only
```

```text
User asks only about expected performance
        |
        v
Performance Agent only
```

For a complete business analysis, the Coordinator gathers the required specialist results and then uses the Opportunity Agent after the required performance and competition data are available.

This keeps focused requests efficient and prevents unnecessary agent calls.

---

## How It Works

```text
USER
 |
 v
COORDINATOR AGENT
 |
 |-- Understand intent
 |-- Collect missing business information
 |-- Decide which specialist agents are required
 |
 +----> LOCATION AGENT
 |          |
 |          +--> Historical Zomato location context
 |
 +----> PERFORMANCE AGENT
 |          |
 |          +--> Random Forest prediction
 |
 +----> COMPETITION AGENT
 |          |
 |          +--> Google Places
 |          +--> Candidate filtering
 |          +--> Competition statistics
 |
 +----> OPPORTUNITY AGENT
            |
            +--> Performance + Competition signals
            +--> Opportunity score
 |
 v
COORDINATOR
 |
 v
FINAL BUSINESS REPORT
```

---

## Role of Gemini ADK

Google ADK provides the agent orchestration and conversational layer.

Gemini-powered agents are responsible for:

1. Understanding the user's business request.
2. Identifying the requested analysis.
3. Collecting missing business information when required.
4. Deciding which specialist agent should handle the request.
5. Calling specialist agents through ADK `AgentTool`.
6. Explaining structured analytical results in natural language.
7. Presenting the final business report.

The LLM is **not the source of truth for numerical analysis**.

Python-based analysis is the source of truth for:

* ML predictions
* Class probabilities
* Historical location metrics
* Competitor counts
* Ratings
* Review statistics
* Competition scores
* Opportunity scores

This separation keeps the analytical calculations deterministic and reduces the risk of the LLM inventing numerical results.

---

## Machine Learning

The project uses a **Random Forest classifier** trained on historical Zomato data.

The model predicts a historical business performance class:

```text
Low
Medium
High
```

The model also provides class probabilities.

Example:

```text
High:   15.84%
Medium: 50.48%
Low:    33.68%
```

These probabilities represent the model's estimated class probabilities based on historical patterns.

They should **not** be interpreted as guaranteed real-world business success probabilities.

### ML Pipeline

```text
Historical Zomato Dataset
          |
          v
     Data Cleaning
          |
          v
   Feature Engineering
          |
          v
     Train/Test Split
          |
          v
      Preprocessing
          |
          v
   Random Forest Model
          |
          v
    Performance Class
     Low / Medium / High
```

### Model Files

```text
models/
├── zomato_performance_model.pkl
└── zomato_preprocessor.pkl
```

**zomato_performance_model.pkl**

Contains the trained Random Forest model.

**zomato_preprocessor.pkl**

Contains the preprocessing pipeline used to transform input features before prediction.

---

## Model Performance

The baseline Random Forest model achieved approximately **87% test accuracy** on the current dataset.

XGBoost was also evaluated as an alternative model, but Random Forest performed better on the current dataset.

Model performance should be interpreted in the context of the historical dataset and evaluation setup rather than as a guarantee of future business performance.

---

## Historical Location Analysis

The Location Agent uses processed Zomato data to retrieve location-level historical characteristics.

The analysis can include:

* Historical restaurant count
* Median cost for two
* Online ordering rate
* Table-booking rate
* Cuisine diversity
* Business-type diversity

Example:

```text
Indiranagar, Bengaluru
        |
        v
Processed Zomato Data
        |
        v
Location-level Features
        |
        v
Historical Location Context
```

The system normalizes location names so that users can provide locations naturally, such as:

* Whitefield, Bengaluru
* Brookfield, Bengaluru
* Indiranagar, Bengaluru
* Koramangala, Bengaluru

If a requested location is not available in the historical dataset, the system reports that historical data was not found instead of inventing values.

---

## Automatic Location Resolution

For live Google Places operations, users do not need to provide latitude and longitude in normal usage.

For example:

> I want to open a bakery in Indiranagar, Bengaluru.

The system can resolve the location through Google Places:

```text
Indiranagar, Bengaluru
        |
        v
Google Places API
        |
        v
Latitude + Longitude
```

The resolved coordinates can then be used for nearby competition searches.

---

## Google Places Competition Analysis

The Competition Agent uses the Google Places API to discover nearby candidate businesses.

Retrieved information can include:

* Business name
* Rating
* Review count
* Address
* Business types
* Location
* Place ID
* Price level where available

The pipeline then applies Python-based relevance filtering.

```text
Google Places Candidates
          |
          v
  Relevance Filtering
          |
          v
Relevant Competitors
          |
          v
Competition Statistics
```

The filtering logic uses the project's supported Google Places business types. Competition categories should be interpreted according to the current implementation rather than assuming that every returned business is automatically a direct or indirect competitor.

---

## Competition Analysis

The system calculates competition statistics from relevant competitors.

Examples include:

* Number of competitors retrieved
* Average competitor rating
* Median competitor rating
* Average review count
* Median review count
* Highly rated competitor count
* Highly reviewed competitor count

A competition strength score is calculated by the Python analysis engine.

The current competition scoring logic uses project-defined thresholds and is an analytical indicator, not a guarantee of market difficulty.

---

## Opportunity Analysis

The Opportunity Agent combines:

1. Historical ML performance probabilities
2. Competition statistics

The deterministic Python scoring engine produces:

```text
Opportunity Score
Historical Performance Score
Competition Strength Score
```

Example:

```text
Opportunity Score: 33.76
Opportunity Class: Low

Historical Performance: 41.08
Competition Strength: 77.21
```

The Python analysis engine calculates these values.

The Opportunity Agent explains the returned results but does not independently invent or modify the numerical values.

### Opportunity Scoring Concept

The current implementation gives:

* Higher historical High/Medium performance probability → higher performance score.
* Stronger competition → greater competition penalty.
* The final opportunity score combines the performance and competition components.

The exact thresholds and formulas are defined in the project's Python analysis code.

---

## End-to-End Example

Suppose the user enters:

> I want to open a premium Japanese restaurant in Koramangala, Bengaluru.

The user may provide:

```text
Business type: Restaurant
Primary cuisine: Japanese
Cost for two: ₹1,800
Online ordering: Yes
Table booking: Yes
Cuisine count: 3
Restaurant type: Casual Dining
Location: Koramangala, Bengaluru
```

### Step 1 — Coordinator

The Coordinator understands that the user wants a complete business analysis and identifies the required specialist analyses.

### Step 2 — Location Agent

The Location Agent retrieves historical location-level information from the processed Zomato dataset.

### Step 3 — Performance Agent

The Performance Agent uses the business inputs and historical location features with the Random Forest model.

Example output:

```text
Prediction: High

High:   51.51%
Medium: 42.83%
Low:     5.67%
```

### Step 4 — Competition Agent

The Competition Agent searches Google Places for relevant businesses around the requested location.

It filters the retrieved candidates and calculates competition statistics.

Example:

```text
Competitors Retrieved: 16
Average Rating: 4.15
Median Rating: 4.30
Average Reviews: 5140.75
Median Reviews: 3104.5
Highly Rated Competitors: 8
Highly Reviewed Competitors: 11
```

### Step 5 — Opportunity Agent

The Opportunity Agent receives the structured performance probabilities and competition summary and applies the project's deterministic opportunity-scoring logic.

Example:

```text
Opportunity Score: 54.60
Opportunity Class: Moderate

Historical Performance: 78.34
Competition Strength: 81.01
```

### Step 6 — Coordinator Final Report

The Coordinator combines the returned results into a readable report containing:

* Business overview
* Location snapshot
* Historical performance
* Competition snapshot
* Business opportunity
* Key insights
* Considerations

The Coordinator preserves the numerical values returned by the analytical components rather than recalculating or inventing them.

---

## Project Architecture

```text
Business_Analysis_Agent/
│
├── data/
│   ├── raw/
│   │   └── zomato.csv
│   │
│   └── processed/
│       ├── zomato_cleaned.csv
│       ├── zomato_train_engineered.csv
│       └── zomato_test_engineered.csv
│
├── models/
│   ├── zomato_performance_model.pkl
│   └── zomato_preprocessor.pkl
│
├── notebooks/
│   ├── 01_zomato_exploration.ipynb
│   ├── 02_zomato_cleaning.ipynb
│   ├── 03_zomato_eda.ipynb
│   ├── 04_zomato_feature_engineering.ipynb
│   ├── 05_zomato_model_training.ipynb
│   └── 06_google_places_competition.ipynb
│
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── coordinator_agent.py
│   │   ├── location_agent.py
│   │   ├── performance_agent.py
│   │   ├── competition_agent.py
│   │   └── opportunity_agent.py
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── location_context.py
│   │   └── opportunity.py
│   │
│   ├── ml/
│   │   ├── __init__.py
│   │   └── predictor.py
│   │
│   └── places/
│       ├── __init__.py
│       └── competition.py
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Tech Stack

### AI / Agent

* Google ADK
* Gemini
* ADK `AgentTool`

### Machine Learning

* Python
* Pandas
* NumPy
* Scikit-learn
* Random Forest

### Data

* Historical Zomato dataset
* Engineered location-level features

### Live Data

* Google Places API

### Development

* Python
* Git
* GitHub
* VS Code

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Business_Analysis_Agent
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GOOGLE_MAPS_API_KEY=your_google_places_api_key
GOOGLE_API_KEY=your_gemini_api_key
```

Do not commit `.env` to GitHub.

---

## Running the Agent

Set the project root as the Python path.

### PowerShell

```powershell
$env:PYTHONPATH = (Get-Location).Path
```

Start the ADK application:

```powershell
adk web src
```

Then open the ADK interface and provide a business request.

Example:

> I want to open a bakery in Indiranagar, Bengaluru.

The Coordinator will determine the required information and delegate the appropriate analysis to the specialist agents.

---

## Security

The following files and directories should not be committed:

```text
.env
.venv/
*.pkl
data/raw/
data/processed/
__pycache__/
```

API keys should always be stored in environment variables.

---

## Limitations

The system should be treated as a **decision-support tool**, not a guaranteed business forecasting system.

Limitations include:

* Historical Zomato data may not represent current market conditions.
* Google Places results depend on live API availability and returned search results.
* Competitor relevance depends on available business types and filtering logic.
* ML predictions reflect patterns in the training dataset.
* Opportunity scores are analytical indicators and are not guarantees of profitability.
* Actual business success also depends on factors outside the system, such as rent, location visibility, operations, marketing, product quality, and execution.

---

## Future Improvements

Potential future improvements include:

* Web-based business analysis dashboard
* More extensive feature engineering
* Hyperparameter tuning
* Cross-validation
* Additional model comparison
* Competitor distance analysis
* Competitor price-level analysis
* Historical trend analysis
* More detailed location intelligence
* Automated business report generation
* Visualization of competition density
* More robust structured handoff between specialist agents
* Model fallback handling for temporary LLM availability errors

---

## Project Objective

The goal of this project is not to guarantee whether a business will succeed.

Instead, it provides a **data-driven decision-support system** that combines:

```text
Historical Business Data
        +
Machine Learning
        +
Live Competition Data
        +
AI-powered Orchestration and Explanation
        |
        v
Business Opportunity Analysis
```

The system helps users evaluate potential food and restaurant business opportunities using historical data, ML-based performance signals, live competition information, and AI-powered explanations.

---

## Key Design Principle

The core architecture separates **AI orchestration** from **numerical analysis**:

> **Gemini understands and orchestrates. Python calculates. Google Places provides live competition data. Machine Learning provides historical performance predictions.**

This makes the system more reliable because the LLM is not responsible for inventing or independently calculating analytical numbers.

---

## Author

**Tanay Chaturvedi**

AI / Machine Learning / Data Analytics Project
