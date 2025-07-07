#!/usr/bin/env python3
from google.cloud import firestore

def check_order_user_doc(sender_id):
    db = firestore.Client()
    user_ref = db.collection('orders').document(sender_id)
    user_doc = user_ref.get()
    if user_doc.exists:
        print(f"✅ Документ orders/{sender_id} существует")
    else:
        print(f"❌ Документ orders/{sender_id} НЕ существует")

if __name__ == "__main__":
    check_order_user_doc("79140775712") 