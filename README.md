# ⚡ AI-Based Electricity Consumption Analyzer

### Machine Learning-Based Household Electricity Consumption Analysis & Forecasting

An end-to-end machine learning web application that analyzes household electricity consumption, forecasts daily energy usage, classifies consumption levels, and discovers usage patterns using real machine learning models.

Built with **React.js, Flask, Python, and Scikit-learn**, this project combines data preprocessing, model training, performance evaluation, and interactive visualization in a single dashboard.

---

## 📌 Project Overview

Understanding household electricity consumption can help identify usage patterns, improve energy awareness, and support better electricity management.

The AI-Based Electricity Consumption Analyzer uses historical household electricity data to:

- Forecast daily electricity consumption.
- Classify consumption into Low, Medium, and High categories.
- Discover similar usage patterns through clustering.
- Evaluate machine learning model performance.
- Present consumption information through an interactive dashboard.

**Data integrity is a key design principle:** the application is intended to report missing datasets or trained models rather than fabricate predictions or evaluation metrics. Synthetic sample data, when used, must be clearly identified as demonstration data.

## ✨ Key Features

- 📊 **Interactive Dashboard** — Explore household electricity consumption statistics and trends.
- 🔮 **Consumption Forecasting** — Predict future daily energy usage using Linear Regression.
- 🌳 **Consumption Classification** — Categorize usage levels using a Decision Tree classifier.
- 🔍 **Usage Pattern Clustering** — Group similar consumption days using K-Means.
- 📈 **Model Evaluation** — Review supported model performance metrics.
- 💡 **Energy-Saving Tips** — Display practical recommendations for reducing electricity usage.
- 🔌 **REST API** — Connect the React frontend with the Flask backend.
- 🧪 **Sample Data Support** — Test the workflow with clearly labelled synthetic data when configured.
- 🖥️ **Windows Quick Start** — Use the included `start_project.bat` file to launch the application.

## 🧠 Machine Learning Algorithms

| Algorithm | Purpose | Evaluation |
|---|---|---|
| Linear Regression | Forecast daily electricity consumption in kWh | MAE, RMSE, R² |
| Decision Tree | Classify daily consumption as Low, Medium, or High | Accuracy, Precision, Recall, F1-score, Confusion Matrix |
| K-Means | Group days by electricity usage patterns | Inertia, Silhouette Score |

### 1. Linear Regression

Uses historical consumption and time-related features to forecast daily electricity usage. Forecast quality is evaluated on a chronological hold-out set.

### 2. Decision Tree Classifier

Predicts a consumption category from the configured usage and calendar features. If categories are created from training-data percentiles, they are useful labels rather than independently verified ground truth.

### 3. K-Means Clustering

Groups days with similar usage characteristics. Cluster descriptions can help users interpret the patterns discovered in the data.

> **Important:** Actual evaluation results depend on the dataset used and the models successfully trained. Do not report synthetic-data metrics as real-world performance.

## 🛠️ Tech Stack

| Technology | Usage |
|---|---|
| React.js | Frontend interface |
| Vite | Frontend development and build tooling |
| Recharts | Data visualization |
| Python | Data processing and ML |
| Flask | Backend REST API |
| Pandas | Dataset manipulation |
| NumPy | Numerical computation |
| Scikit-learn | Machine learning algorithms |
| Joblib | Saving and loading trained models |
| HTML, CSS, JavaScript | Web interface |

## 🏗️ System Architecture

```text
                ┌──────────────────────┐
                │       User           │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │   React Dashboard    │
                │   Vite + Recharts    │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │   API Client (api.js)│
                └──────────┬───────────┘
                           │ HTTP Requests
                           ▼
                ┌──────────────────────┐
                │     Flask API        │
                │    backend/app.py    │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Data Processing and  │
                │ Trained ML Models    │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ JSON Response and    │
                │ Dashboard Results    │
                └──────────────────────┘
```

## 📂 Project Structure

```text
AI-Electricity-Analyzer/
│
├── backend/
│   ├── app.py
│   ├── preprocess.py
│   ├── train_model.py
│   ├── download_dataset.py
│   ├── generate_sample_data.py
│   ├── requirements.txt
│   ├── data/
│   ├── models/
│   └── outputs/
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       ├── api.js
│       ├── index.css
│       ├── main.jsx
│       └── components/
│
├── start_project.bat
├── .gitignore
└── README.md
```
## 🖥️ Application Screenshots

### Main Dashboard
<img width="1600" height="847" alt="image" src="https://github.com/user-attachments/assets/10229ac1-460e-4471-9e81-a8f83f4151b0" />

### ForeCast
<img width="1600" height="857" alt="image" src="https://github.com/user-attachments/assets/c9b0867f-e74b-4f77-b134-a637485ec726" />

### Classify a Day
<img width="1600" height="847" alt="image" src="https://github.com/user-attachments/assets/03e914eb-51f0-4957-a5fe-aad8c2a9c260" />

### Usage Cluster
<img width="1600" height="852" alt="image" src="https://github.com/user-attachments/assets/356014d9-2acc-4fc9-8d9f-da4226d264a6" />

### Model Performance
<img width="1600" height="847" alt="image" src="https://github.com/user-attachments/assets/59f09f38-651f-4001-a16d-a6a228e6118c" />

### Energy Tips
<img width="1600" height="847" alt="image" src="https://github.com/user-attachments/assets/53d48d3f-70dd-4721-9b58-8165c42d10f6" />



**Important directories:**

- `backend/data/` — Dataset files used for analysis.
- `backend/models/` — Saved trained machine learning models.
- `backend/outputs/` — Generated metrics and aggregated data files.
- `frontend/src/components/` — Dashboard components.
- `start_project.bat` — Windows startup script.

## 📊 Dataset

This project uses the **Individual Household Electric Power Consumption** dataset from the UCI Machine Learning Repository.

**Dataset source:** [UCI — Individual Household Electric Power Consumption](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption)

The dataset contains measurements collected from a household in France between 2006 and 2010.

### Download and Prepare the Dataset

1. Open the official UCI dataset page.
2. Download and extract the dataset.
3. Locate `household_power_consumption.txt`.
4. Place the file inside `backend/data/`.

Alternatively, run the project's dataset download script from the backend directory:

```bash
python download_dataset.py
```

If automatic downloading fails, use the manual download method.

### Sample Data Mode

The project includes `generate_sample_data.py` for creating synthetic demonstration data.

Run it from the backend directory:

```bash
python generate_sample_data.py
```

Synthetic data is computer-generated and does not represent real household measurements. It can help demonstrate the application workflow, but its evaluation metrics should not be presented as evidence of real-world accuracy.

When real data becomes available, use the project's training workflow to train the models on that dataset.

## 🚀 Getting Started

### Prerequisites

Install the following software on Windows:

- Python 3.10 or later
- Node.js LTS and npm
- Git (optional, for cloning the repository)

### Option 1: Quick Start — Recommended

The repository includes a Windows startup script named `start_project.bat`.

1. Clone or download the repository.
2. Ensure Python and Node.js are installed.
3. Open the project folder.
4. Double-click `start_project.bat`.
5. Follow the terminal windows and wait for the application to start.
6. Open the frontend URL displayed in the terminal, usually:

   **http://localhost:5173**

The exact setup, dataset preparation, and training behavior depends on the commands configured in `start_project.bat`.

### Option 2: Manual Setup

**Step 1 — Clone the repository**

```bash
git clone https://github.com/SSsadiyashaikh/Electricity-Consumption-Analyzer-.git
cd Electricity-Consumption-Analyzer-
```

**Step 2 — Create the Python environment**

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Step 3 — Prepare the dataset**

```powershell
python download_dataset.py
```

If the download script cannot obtain the dataset, download it from the official UCI page and place the extracted text file in `backend/data/`.

**Step 4 — Train the machine learning models**

```powershell
python train_model.py
```

**Step 5 — Start the backend**

```powershell
python app.py
```

Keep the backend terminal open.

**Step 6 — Start the frontend**

Open a second terminal in the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite.

### Retraining the Models

After adding or changing the dataset, follow the project's training procedure. If existing model files cause training to be skipped, remove the relevant generated model files only when you intend to retrain, then run the training script again.

## ⚙️ Data Processing

The preprocessing workflow is designed around the following rules:

- The source dataset is semicolon-separated.
- Missing readings are represented by `?`.
- Active energy per minute is calculated from `Global_active_power` in kW multiplied by the one-minute interval in hours, then aggregated by day.
- Sub-meter readings are in Wh and are converted to kWh by dividing by 1,000.
- Missing minute readings are not automatically filled.
- A day is retained only if at least 1,296 of its 1,440 expected minute readings are available.
- A month is treated as complete when at least 90% of its days are retained.
- The forecasting evaluation uses a chronological split: the first 80% of days for training and the final 20% for testing.

## 🔌 API Endpoints

The Flask backend exposes the following endpoints, subject to the implementation in `backend/app.py`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check dataset and model availability |
| GET | `/api/history?granularity=monthly&limit=N` | Retrieve monthly history |
| GET | `/api/history?granularity=daily&limit=N` | Retrieve daily history |
| GET | `/api/summary` | Retrieve summary statistics |
| GET | `/api/model-metrics` | Retrieve saved model metrics |
| POST | `/api/predict` | Forecast future consumption |
| POST | `/api/classify` | Classify a consumption day |
| POST | `/api/cluster` | Identify a consumption cluster |

### Example Requests

**Forecast**

```json
{
  "days_ahead": 7
}
```

**Classification**

```json
{
  "peak_kw": 2.5,
  "kitchen_kwh": 1.2,
  "laundry_kwh": 0.8,
  "water_heater_ac_kwh": 1.5,
  "is_weekend": 1,
  "month": 7
}
```

**Clustering**

```json
{
  "daily_kwh": 12.5,
  "peak_kw": 3.2,
  "evening_share_pct": 35
}
```

The exact request fields, validation rules, and response formats are determined by the backend implementation.

## ⚠️ Limitations

- The original dataset represents one French household and may not generalize to other households.
- Synthetic data is suitable for demonstration, not for claiming real-world model performance.
- Linear Regression may not capture sudden changes in electricity usage.
- Recursive multi-day forecasting can accumulate errors.
- Percentile-derived consumption labels are not independent ground truth.
- K-Means results depend on the selected features and scaling procedure.
- Energy-saving tips are rule-based recommendations, not AI-generated predictions.
- A chronological split helps prevent future-data leakage in forecasting evaluation.
- Lag features must use only information available before the prediction date.

## 🔮 Future Enhancements

- Electricity bill estimation using tariff information.
- Weather-aware electricity forecasting.
- Real-time smart meter integration.
- Personalized energy-saving recommendations.
- Downloadable electricity consumption reports.
- Cloud deployment and model monitoring.
- Support for multiple households and user profiles.

## 🎓 Academic Project Details

| Field | Details |
|---|---|
| Project Title | AI-Based Electricity Consumption Analyzer |
| Project Type | College Mini-Project |
| Domain | Artificial Intelligence and Machine Learning |
| Frontend | React.js, Vite, Recharts |
| Backend | Python, Flask |
| Algorithms | Linear Regression, Decision Tree, K-Means |
| Dataset | UCI Individual Household Electric Power Consumption |

## 👩‍💻 Author

**Sadiya Shaikh**  
Information Technology Engineering Student  


---

*Making household electricity consumption easier to understand through data analysis and machine learning.*
