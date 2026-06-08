# LUXE

LUXE is a lightweight repository currently focused on project setup and documentation.

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/dmang69/LUXE.git
   ```
2. Open the project folder:
   ```bash
   cd LUXE
   ```

## Dashboard

This repository now includes a Streamlit dashboard for the Luxe Collective command center.

### Run locally

1. Start the backend API on port `8000`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the dashboard:
   ```bash
   streamlit run dashboard.py --server.port 8501
   ```
4. Open `http://localhost:8501`.

### Current behavior

- Screen 1 uses the live boss approval endpoints.
- Screens 2-4 use mock data that is ready to swap for real backend data later.
- The dashboard auto-refreshes every 5 seconds.

## Project Status

The repository is in an early stage and currently contains foundational files only.

## Contributing

Contributions are welcome. Please open an issue to discuss proposed changes before submitting a pull request.
