import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse, Response

# Works when started as either:
#   uvicorn backend.main:app --reload
# or from inside backend:
#   uvicorn main:app --reload
try:
    from backend.agent import run_agent
    from backend.razorpay_service import create_order, verify_payment
    from backend.audit import log_event
except ModuleNotFoundError:
    from agent import run_agent
    from razorpay_service import create_order, verify_payment
    from audit import log_event

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

# Your project screenshot shows .env inside backend.
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

app = FastAPI(
    title="ShopBoost AI",
    description="AI Growth & Agentic Commerce Agent"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class ChatRequest(BaseModel):
    message: str

class OrderRequest(BaseModel):
    amount: float
    product_name: str

class VerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "ShopBoost AI is running"
    }

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = BASE_DIR / "frontend" / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return Response(status_code=204)

# =====================================================
# AI AGENT
# =====================================================

@app.post("/api/agent")
def agent(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Please enter a shopping request."
        )

    try:
        result = run_agent(request.message)

        try:
            log_event(
                "AI_RECOMMENDATION",
                {
                    "customer_request": request.message,
                    "result": result
                }
            )
        except Exception as log_error:
            print("Audit log warning:", log_error)

        return result

    except HTTPException:
        raise
    except Exception as error:
        print("AI AGENT ERROR:", repr(error))

        try:
            log_event(
                "AI_RECOMMENDATION_FAILURE",
                {
                    "customer_request": request.message,
                    "error": str(error)
                }
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=f"AI agent error: {str(error)}"
        )

# =====================================================
# RAZORPAY - CREATE ORDER
# =====================================================

@app.post("/api/create-order")
def order(request: OrderRequest):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    if request.amount > 500000:
        raise HTTPException(
            status_code=400,
            detail="Payment exceeds demo safety limit."
        )

    try:
        razorpay_order = create_order(request.amount)

        try:
            log_event(
                "ORDER_CREATED",
                {
                    "product": request.product_name,
                    "amount": request.amount,
                    "order_id": razorpay_order["id"]
                }
            )
        except Exception as log_error:
            print("Audit log warning:", log_error)

        return {
            "key": os.getenv("RAZORPAY_KEY_ID"),
            "order": razorpay_order
        }
    except Exception as error:
        print("ORDER ERROR:", repr(error))
        try:
            log_event("ORDER_FAILURE", {"error": str(error)})
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail="Could not create Razorpay order."
        )

# =====================================================
# RAZORPAY - VERIFY PAYMENT
# =====================================================

@app.post("/api/verify-payment")
def payment_verification(request: VerifyRequest):
    try:
        valid = verify_payment(
            request.razorpay_order_id,
            request.razorpay_payment_id,
            request.razorpay_signature
        )

        if not valid:
            try:
                log_event(
                    "PAYMENT_VERIFICATION_FAILED",
                    {
                        "order_id": request.razorpay_order_id,
                        "payment_id": request.razorpay_payment_id
                    }
                )
            except Exception:
                pass
            raise HTTPException(
                status_code=400,
                detail="Payment verification failed."
            )

        try:
            log_event(
                "PAYMENT_SUCCESS",
                {
                    "order_id": request.razorpay_order_id,
                    "payment_id": request.razorpay_payment_id
                }
            )
        except Exception:
            pass

        return {
            "success": True,
            "message": "Payment verified successfully."
        }
    except HTTPException:
        raise
    except Exception as error:
        print("PAYMENT VERIFICATION ERROR:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Payment verification failed."
        )
