# Copilot Instructions

This file contains instructions for the AI assistant working on this repository.

## Project Context
This project is focused on analyzing long-term cryptocurrency trades, specifically Ethereum (ETH). It involves data analysis, signal generation (buy/sell), and visualization.

## Critical Rules
1.  **Python Virtual Environment**: This is a Python project. **ALWAYS** use a virtual environment.
    *   Check if `.venv` exists. If not, create it: `python -m venv .venv`.
    *   Activate the virtual environment before running any python commands or installing packages.
        *   Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
        *   Linux/Mac: `source .venv/bin/activate`
    *   If you encounter "module not found" errors, ensure you are in the venv and dependencies are installed.

2.  **Dependencies**:
    *   Dependencies are listed in `requirements.txt`.
    *   Install/Update dependencies: `pip install -r requirements.txt`.

## Codebase Structure
*   `analysis_eth.py`: Main script for ETH analysis and signal generation.
*   `verify_signals.py`: Script for verifying the generated signals.
*   `inspect_data.py`: Utility to inspect data files.
*   `data/`: Directory containing input data (CSV, JSON, etc.).

## Path Handling
*   **Always use relative paths** instead of absolute paths for portability across different systems.
*   Use `os.path.join(os.path.dirname(__file__), "data")` to reference the data directory.
*   Never hardcode user-specific paths (e.g., `C:\Users\username\...`).

## Style & Best Practices
*   Follow PEP 8 guidelines for Python code.
*   Ensure plots and charts are saved with descriptive names (e.g., `eth_signals_Daily.png`).
