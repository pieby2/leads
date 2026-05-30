import stripe
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import datetime

from app.config import get_settings
from app.database import get_db
from app.core.auth import get_current_user
from app.db.models import User, Subscription

settings = get_settings()
# stripe.api_key = settings.stripe_secret_key # You would add this in config

router = APIRouter(prefix="/api/v1/stripe", tags=["stripe"])

# Replace with your actual frontend URL in production
FRONTEND_URL = "http://localhost:3000"


@router.post("/create-checkout-session")
async def create_checkout_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=current_user.email,
            client_reference_id=current_user.id,
            line_items=[
                {
                    # Provide the exact Price ID (e.g. pr_1234) of the product you want to sell
                    'price': 'price_12345', 
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=FRONTEND_URL + '/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=FRONTEND_URL + '/cancel',
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    # endpoint_secret = settings.stripe_webhook_secret

    try:
        import json
        data = json.loads(payload)
        event = stripe.Event.construct_from(data, stripe.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        user_id = session.get("client_reference_id")
        stripe_customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        if user_id:
            # Update user tier
            result = await db.execute(select(User).filter(User.id == user_id))
            user = result.scalars().first()
            if user:
                user.tier = "pro"
                user.stripe_customer_id = stripe_customer_id
                
                # Add subscription
                sub = Subscription(
                    user_id=user.id,
                    stripe_subscription_id=subscription_id,
                    status="active",
                    current_period_end=datetime.datetime.utcnow() + datetime.timedelta(days=30)
                )
                db.add(sub)
                db.add(user)
                await db.commit()

    return {"status": "success"}
