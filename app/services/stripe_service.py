"""
Stripe Payment Integration Service
Handles subscription payments, webhooks, and billing management
"""
import stripe
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from flask import current_app, url_for
from ..models.user import User
from ..extensions import db

logger = logging.getLogger(__name__)

class StripeService:
    """Service for handling Stripe payment integration"""
    
    def __init__(self):
        self.stripe = stripe
        self._configure_stripe()
    
    def _configure_stripe(self):
        """Configure Stripe with API keys"""
        try:
            # Set API key from config
            self.stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
            
            if not self.stripe.api_key:
                logger.warning("Stripe secret key not configured")
                return False
            
            # Test the connection
            self.stripe.Account.retrieve()
            logger.info("✅ Stripe configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure Stripe: {e}")
            return False
    
    def create_customer(self, user: User) -> Optional[str]:
        """Create a Stripe customer for the user"""
        try:
            if user.stripe_customer_id:
                # Customer already exists, verify it's valid
                try:
                    customer = self.stripe.Customer.retrieve(user.stripe_customer_id)
                    return customer.id
                except stripe.error.InvalidRequestError:
                    # Customer doesn't exist anymore, create new one
                    pass
            
            # Create new customer
            customer = self.stripe.Customer.create(
                email=user.email,
                name=user.username,
                metadata={
                    'user_id': str(user.id),
                    'created_from': 'aksjeny_app'
                }
            )
            
            # Save customer ID to user
            user.stripe_customer_id = customer.id
            db.session.commit()
            
            logger.info(f"✅ Created Stripe customer {customer.id} for user {user.id}")
            return customer.id
            
        except Exception as e:
            logger.error(f"Error creating Stripe customer for user {user.id}: {e}")
            return None
    
    def create_checkout_session(self, user: User, price_id: str, success_url: str = None, cancel_url: str = None) -> Optional[str]:
        """Create a Stripe Checkout session for subscription"""
        try:
            # Ensure user has a Stripe customer ID
            customer_id = self.create_customer(user)
            if not customer_id:
                return None
            
            # Default URLs if not provided
            if not success_url:
                success_url = url_for('main.subscription_success', _external=True)
            if not cancel_url:
                cancel_url = url_for('main.pricing', _external=True)
            
            # Create checkout session
            session = self.stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                billing_address_collection='required',
                metadata={
                    'user_id': str(user.id),
                    'plan_type': self._get_plan_type_from_price_id(price_id)
                },
                subscription_data={
                    'metadata': {
                        'user_id': str(user.id),
                    }
                }
            )
            
            logger.info(f"✅ Created checkout session {session.id} for user {user.id}")
            return session.url
            
        except Exception as e:
            logger.error(f"Error creating checkout session for user {user.id}: {e}")
            return None
    
    def create_customer_portal_session(self, user: User, return_url: str = None) -> Optional[str]:
        """Create a Stripe Customer Portal session for managing subscriptions"""
        try:
            if not user.stripe_customer_id:
                logger.error(f"User {user.id} doesn't have a Stripe customer ID")
                return None
            
            if not return_url:
                return_url = url_for('main.account_settings', _external=True)
            
            session = self.stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=return_url,
            )
            
            logger.info(f"✅ Created portal session for user {user.id}")
            return session.url
            
        except Exception as e:
            logger.error(f"Error creating portal session for user {user.id}: {e}")
            return None
    
    def get_subscription_status(self, user: User) -> Dict:
        """Get detailed subscription status for user"""
        try:
            if not user.stripe_customer_id:
                return {
                    'has_subscription': False,
                    'status': 'no_customer',
                    'plan': None,
                    'current_period_end': None
                }
            
            # Get customer's subscriptions
            subscriptions = self.stripe.Subscription.list(
                customer=user.stripe_customer_id,
                status='active'
            )
            
            if not subscriptions.data:
                return {
                    'has_subscription': False,
                    'status': 'no_active_subscription',
                    'plan': None,
                    'current_period_end': None
                }
            
            # Get the most recent active subscription
            subscription = subscriptions.data[0]
            
            return {
                'has_subscription': True,
                'status': subscription.status,
                'plan': self._get_plan_name_from_subscription(subscription),
                'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                'subscription_id': subscription.id,
                'cancel_at_period_end': subscription.cancel_at_period_end
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription status for user {user.id}: {e}")
            return {
                'has_subscription': False,
                'status': 'error',
                'plan': None,
                'current_period_end': None
            }
    
    def handle_webhook(self, payload: str, signature: str) -> bool:
        """Handle Stripe webhook events"""
        try:
            webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
            if not webhook_secret:
                logger.error("Stripe webhook secret not configured")
                return False
            
            # Verify webhook signature
            event = self.stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            
            logger.info(f"📨 Received Stripe webhook: {event['type']}")
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                return self._handle_checkout_completed(event['data']['object'])
            elif event['type'] == 'customer.subscription.created':
                return self._handle_subscription_created(event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                return self._handle_subscription_updated(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                return self._handle_payment_failed(event['data']['object'])
            else:
                logger.info(f"Unhandled webhook event type: {event['type']}")
                return True
            
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return False
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return False
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return False
    
    def _handle_checkout_completed(self, session) -> bool:
        """Handle completed checkout session"""
        try:
            user_id = session.metadata.get('user_id')
            if not user_id:
                logger.error("No user_id in checkout session metadata")
                return False
            
            user = User.query.get(int(user_id))
            if not user:
                logger.error(f"User {user_id} not found for checkout session")
                return False
            
            # Update user subscription status
            plan_type = session.metadata.get('plan_type', 'monthly')
            
            user.has_subscription = True
            user.subscription_type = plan_type
            user.subscription_start = datetime.utcnow()
            
            # Set subscription end date based on plan
            if plan_type == 'yearly':
                user.subscription_end = datetime.utcnow() + timedelta(days=365)
            elif plan_type == 'lifetime':
                user.subscription_end = datetime.utcnow() + timedelta(days=365*10)  # 10 years
            else:  # monthly
                user.subscription_end = datetime.utcnow() + timedelta(days=30)
            
            db.session.commit()
            
            logger.info(f"✅ Activated {plan_type} subscription for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling checkout completion: {e}")
            return False
    
    def _handle_subscription_created(self, subscription) -> bool:
        """Handle new subscription created"""
        try:
            customer_id = subscription['customer']
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            
            if not user:
                logger.error(f"User not found for customer {customer_id}")
                return False
            
            # Update subscription status
            user.has_subscription = True
            user.subscription_start = datetime.fromtimestamp(subscription['current_period_start'])
            user.subscription_end = datetime.fromtimestamp(subscription['current_period_end'])
            user.subscription_type = self._get_plan_type_from_subscription(subscription)
            
            db.session.commit()
            
            logger.info(f"✅ Created subscription for user {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling subscription creation: {e}")
            return False
    
    def _handle_subscription_updated(self, subscription) -> bool:
        """Handle subscription updates"""
        try:
            customer_id = subscription['customer']
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            
            if not user:
                logger.error(f"User not found for customer {customer_id}")
                return False
            
            # Update subscription end date
            user.subscription_end = datetime.fromtimestamp(subscription['current_period_end'])
            
            # Update subscription status
            if subscription['status'] in ['active', 'trialing']:
                user.has_subscription = True
            else:
                user.has_subscription = False
            
            db.session.commit()
            
            logger.info(f"✅ Updated subscription for user {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling subscription update: {e}")
            return False
    
    def _handle_subscription_deleted(self, subscription) -> bool:
        """Handle subscription cancellation"""
        try:
            customer_id = subscription['customer']
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            
            if not user:
                logger.error(f"User not found for customer {customer_id}")
                return False
            
            # Deactivate subscription
            user.has_subscription = False
            user.subscription_type = 'free'
            user.subscription_end = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"✅ Cancelled subscription for user {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling subscription deletion: {e}")
            return False
    
    def _handle_payment_succeeded(self, invoice) -> bool:
        """Handle successful payment"""
        try:
            customer_id = invoice['customer']
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            
            if user:
                logger.info(f"✅ Payment succeeded for user {user.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling payment success: {e}")
            return False
    
    def _handle_payment_failed(self, invoice) -> bool:
        """Handle failed payment"""
        try:
            customer_id = invoice['customer']
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            
            if user:
                logger.warning(f"⚠️ Payment failed for user {user.id}")
                # Could send email notification here
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
            return False
    
    def _get_plan_type_from_price_id(self, price_id: str) -> str:
        """Get plan type from Stripe price ID"""
        # Map price IDs to plan types - update these with your actual Stripe price IDs
        price_map = {
            'price_monthly_pro': 'monthly',
            'price_yearly_pro': 'yearly',
            'price_lifetime_pro': 'lifetime'
        }
        
        return price_map.get(price_id, 'monthly')
    
    def _get_plan_type_from_subscription(self, subscription) -> str:
        """Get plan type from subscription object"""
        try:
            if subscription.items and subscription.items.data:
                price = subscription.items.data[0].price
                return self._get_plan_type_from_price_id(price.id)
        except:
            pass
        
        return 'monthly'
    
    def _get_plan_name_from_subscription(self, subscription) -> str:
        """Get human readable plan name from subscription"""
        plan_type = self._get_plan_type_from_subscription(subscription)
        
        plan_names = {
            'monthly': 'Pro Monthly',
            'yearly': 'Pro Yearly',
            'lifetime': 'Pro Lifetime'
        }
        
        return plan_names.get(plan_type, 'Pro')
    
    def get_pricing_info(self) -> Dict:
        """Get current pricing information"""
        return {
            'monthly': {
                'price': 99,  # NOK
                'currency': 'NOK',
                'interval': 'month',
                'features': [
                    'Ubegrenset aksjeanalyser',
                    'Sanntids markedsdata',
                    'Ubegrenset prisvarsler',
                    'Avanserte screening-verktøy',
                    'Portfolio tracking',
                    'E-post support'
                ]
            },
            'yearly': {
                'price': 990,  # NOK (2 months free)
                'currency': 'NOK',
                'interval': 'year',
                'monthly_equivalent': 82.5,
                'savings': '17%',
                'features': [
                    'Alt i Pro Monthly',
                    'Prioritert support',
                    '17% besparelse',
                    'Tidlig tilgang til nye funksjoner'
                ]
            },
            'lifetime': {
                'price': 2990,  # NOK
                'currency': 'NOK',
                'interval': 'lifetime',
                'features': [
                    'Alt i Pro Yearly',
                    'Livslang tilgang',
                    'Alle fremtidige funksjoner',
                    'VIP support'
                ]
            }
        }


# Global instance
stripe_service = StripeService()
