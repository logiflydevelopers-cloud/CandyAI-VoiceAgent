from fastapi import FastAPI
from dotenv import load_dotenv
from api1 import router
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="AI Voice Assistant",
    description="Real-time Voice Agent (STT + LLM + TTS)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔌 Include API routes
app.include_router(router)


# -----------------------------------
# HEALTH CHECK
# -----------------------------------
@app.get("/")
async def root():
    return {
        "status": "running",
        "message": "Voice Agent is live 🚀"
    }


# -----------------------------------
# OPTIONAL: STARTUP EVENT
# -----------------------------------
@app.on_event("startup")
async def startup_event():
    print("🚀 Server started successfully")


# -----------------------------------
# OPTIONAL: SHUTDOWN EVENT
# -----------------------------------
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Server shutting down")