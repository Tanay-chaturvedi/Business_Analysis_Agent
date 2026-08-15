# AI Business Advisory Agent

An AI-powered business advisory system that evaluates food and restaurant business ideas using **Google ADK, Gemini, Machine Learning, historical Zomato data, and live Google Places competition data**.

The system allows a user to describe a business idea naturally, such as:

> I want to open a bakery in Indiranagar, Bengaluru.

The AI agent collects the required business information, automatically resolves the location, runs the ML and competition analysis, and produces a structured business opportunity report.

---

## Features

- Natural-language business idea analysis
- Gemini-powered AI agent using Google ADK
- Automatic location coordinate resolution
- Historical location analysis using Zomato data
- Random Forest-based business performance prediction
- Live competitor discovery using Google Places API
- Direct and indirect competitor classification
- Competitor rating and review analysis
- Competition strength scoring
- Business opportunity scoring
- Data-backed business recommendations
- Protection against unsupported or hallucinated numerical results

---

## How It Works

```text
                     USER
                       |
                       v
              +-----------------+
              |    Gemini ADK   |
              |  Business Agent |
              +--------+--------+
                       |
              Understands business
                 idea + location
                       |
                       v
             Collects business inputs
                       |
                       v
           +------------------------+
           | business_analysis_tool |
           +-----------+------------+
                       |
                       v
             Resolve Location
                       |
                       v
                Google Places
                       |
                 Latitude/Longitude
                       |
                       v
              +------------------+
              | analyze_business |
              +--------+---------+
                       |
          +------------+------------+
          |            |            |
          v            v            v
     Historical       ML       Google Places
       Zomato       Model       Competition
        Data          |             |
          |           |             v
          |           |       Relevance Filter
          |           |             |
          |           |             v
          |           |       Direct/Indirect
          |           |             |
          |           |             v
          |           |      Competition Score
          |           |
          |           v
          |       Performance
          |        Prediction
          |
          +------------+------------+
                       |
                       v
                Opportunity Score
                       |
                       v
               Structured Results
                       |
                       v
                  Gemini ADK
                       |
                       v
              Final Business Report

Role of Gemini ADK

Gemini ADK acts as the AI orchestration and conversational layer.

It is responsible for:

Understanding the user's business idea.
Identifying the appropriate business category.
Collecting missing business information.
Creating the Google Places search query.
Calling the Python business analysis tool.
Explaining the analytical results.
Providing practical recommendations.

Gemini does not perform the core numerical analysis itself.

The Python analysis pipeline is the source of truth for:

ML predictions
Competitor counts
Ratings
Review counts
Competition scores
Opportunity scores

This separation makes the system more reliable and reproducible.

Machine Learning

The project uses a Random Forest classifier trained on historical Zomato data.

The model predicts a historical business performance class:

Low
Medium
High

The model also provides class probabilities.

For example:

High:   15.84%
Medium: 50.48%
Low:    33.68%

These probabilities represent the model's estimated class probabilities based on historical patterns.

They should not be interpreted as guaranteed real-world business success probabilities.

ML Pipeline
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
Model Files
models/
├── zomato_performance_model.pkl
└── zomato_preprocessor.pkl

zomato_performance_model.pkl

Contains the trained Random Forest model.

zomato_preprocessor.pkl

Contains the preprocessing pipeline used to transform input features before prediction.

Model Performance

The baseline Random Forest model achieved approximately 87% test accuracy.

Model selection is based on actual evaluation performance rather than assuming that a particular algorithm is always superior.

XGBoost was also evaluated as an alternative model, but Random Forest performed better on the current dataset.

Automatic Location Resolution

Users do not need to provide latitude and longitude.

For example:

I want to open a bakery in Indiranagar, Bengaluru.

The system automatically converts the location into coordinates using Google Places.

Indiranagar, Bengaluru
          |
          v
   Google Places API
          |
          v
Latitude + Longitude

This allows the system to work with different locations without hardcoding coordinates.

Examples:

Whitefield, Bengaluru
Brookfield, Bengaluru
Indiranagar, Bengaluru
Koramangala, Bengaluru
Google Places Competition Analysis

The system uses the Google Places API to discover nearby businesses.

For each candidate business, information such as the following can be retrieved:

Business name
Rating
Review count
Address
Business types
Location
Place ID

The system then applies Python-based relevance filtering.

Google Places Candidates
          |
          v
   Relevance Filtering
          |
          v
Relevant Competitors
       /       \
      /         \
 Direct       Indirect

This prevents unrelated businesses from being treated as competitors.

Competition Analysis

The system calculates competition statistics from the relevant competitors.

Examples include:

Number of competitors
Average competitor rating
Median competitor rating
Average review count
Median review count
Direct competitor count
Indirect competitor count

A competition strength score is also calculated by the Python analysis engine.



Opportunity Analysis

The system combines historical business performance and competition signals to produce an overall opportunity assessment.

Example:

Opportunity Score: 33.76
Opportunity Class: Low


Historical Performance: 41.08
Competition Strength: 77.21

The Python analysis engine calculates these values.

Gemini only explains the returned results.

End-to-End Example

Suppose the user enters:

I want to open a bakery in Indiranagar, Bengaluru.

The agent collects:

Business:
Bakery


Cuisine:
Bakery


Cost for two:
₹300


Online ordering:
Yes


Table booking:
No
Step 1 — Location
Indiranagar, Bengaluru
        |
        v
Google Places
        |
        v
Latitude + Longitude
Step 2 — Historical Location Analysis

The system retrieves historical location-level features from the processed Zomato dataset.

Step 3 — ML Prediction

The Random Forest model predicts the historical performance class.

Example:

High:   15.84%
Medium: 50.48%
Low:    33.68%


Prediction: Medium
Step 4 — Competition

Google Places discovers nearby businesses.

The Python pipeline filters them and identifies relevant competitors.

Example:

20 relevant competitors


19 Direct
1 Indirect
Step 5 — Competition Statistics

The system calculates:

Average Rating: 4.495
Median Rating: 4.45
Average Reviews: 2155.75
Median Reviews: 404.5
Step 6 — Opportunity

The Python scoring system produces:

Opportunity Score: 33.76
Opportunity Class: Low
Step 7 — Gemini Explanation

Gemini converts the structured results into a readable business report containing:

Business summary
ML prediction
Location context
Competition
Top competitors
Opportunity score
Risks
Advantages
Recommendations


Setup
1. Clone the repository
git clone <your-repository-url>
cd Business_Analysis_Agent
2. Create a virtual environment
python -m venv .venv

Activate it on Windows:

.venv\Scripts\Activate.ps1
3. Install dependencies
pip install -r requirements.txt
4. Configure environment variables

Create a .env file in the project root:

GOOGLE_MAPS_API_KEY=your_google_places_api_key
GOOGLE_API_KEY=your_gemini_api_key

Do not commit .env to GitHub.

Running the Agent

Set the project root as the Python path.

PowerShell
$env:PYTHONPATH = (Get-Location).Path

Start the ADK application:

adk web src

Then open the ADK interface and provide a business idea.



Limitations

The system should be treated as a decision-support tool, not a guaranteed business forecasting system.

Limitations include:

Historical Zomato data may not represent current market conditions.
Google Places results depend on live API availability and search results.
Competitor relevance depends on available business types and filtering logic.
ML predictions reflect patterns in the training dataset.
Opportunity scores are analytical indicators and are not guarantees of profitability.
Actual business success also depends on factors outside the system, such as rent, location visibility, operations, marketing, product quality, and execution.
Future Improvements

Potential future improvements include:

Web-based business analysis dashboard
More extensive feature engineering
Hyperparameter tuning
Cross-validation
Model comparison
Competitor distance analysis
Competitor price-level analysis
Historical trend analysis
More detailed location intelligence
Automated business report generation
Visualization of competition density