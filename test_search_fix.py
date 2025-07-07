#!/usr/bin/env python3
"""
Тест для проверки поиска sender_id в базе данных
"""

import asyncio
from google.cloud import firestore

async def test_search():
    session_id = "20250706_162943_50861_139"
    
    print(f"Searching for sender_id for session_id: {session_id}")
    
    try:
        db = firestore.Client()
        orders_ref = db.collection('orders')
        
        print("Scanning users in orders collection...")
        user_count = 0
        
        for user_doc in orders_ref.stream():
            user_count += 1
            print(f"Checking user {user_count}: {user_doc.id}")
            
            sessions_ref = user_doc.reference.collection('sessions')
            session_doc = sessions_ref.document(session_id).get()
            
            if session_doc.exists:
                print(f"✅ Found session in user: {user_doc.id}")
                print(f"   Session data: {session_doc.to_dict()}")
                return user_doc.id
            else:
                print(f"   Session not found in this user")
        
        print(f"❌ Session not found in any of {user_count} users")
        return None
            
    except Exception as e:
        print(f"❌ Error searching database: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_search())
    print(f"\nResult: {result}") 