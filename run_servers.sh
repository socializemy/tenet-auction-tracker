#!/bin/bash
# Start backend
cd /Users/coryjames/.gemini/antigravity/scratch/spokane-auction-properties/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000 &

# Start frontend on port 3000
cd /Users/coryjames/.gemini/antigravity/scratch/spokane-auction-properties/frontend
npm run dev -- --host 127.0.0.1 --port 3000 &

wait
