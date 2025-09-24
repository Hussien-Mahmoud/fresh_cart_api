from ninja import Schema


class StripeCheckoutOut(Schema):
    checkout_url: str
    session_id: str
