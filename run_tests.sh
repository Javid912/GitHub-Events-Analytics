#!/bin/bash

# Set up virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r data-collector/requirements.txt
pip install -r spark-jobs/requirements.txt
pip install pytest pytest-cov

# Run data collector tests
echo "Running data collector tests..."
cd data-collector
python -m unittest test_github_events_collector.py
cd ..

# Run spark job tests
echo "Running Spark job tests..."
cd spark-jobs
python -m unittest test_process_github_events.py
cd ..

# Run all tests with coverage
echo "Running all tests with coverage..."
pytest --cov=data-collector --cov=spark-jobs

# Deactivate virtual environment
deactivate

echo "All tests completed!" 