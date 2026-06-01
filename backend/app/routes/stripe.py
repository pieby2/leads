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
stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/api/v1/stripe", tags=["stripe"])

@router.post("/create-checkout-session")
async def create_checkout_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=500, detail="Stripe is not configured.")

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=current_user.email,
            client_reference_id=current_user.id,
            line_items=[
                {
                    'price': settings.stripe_price_id, 
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=settings.frontend_url + '/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=settings.frontend_url + '/cancel',
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = settings.stripe_webhook_secret

    if not sig_header or not endpoint_secret:
        raise HTTPException(status_code=400, detail="Webhook not configured correctly")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
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
