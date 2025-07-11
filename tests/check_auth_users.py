import os
from dotenv import load_dotenv
from database import engine
from sqlalchemy import text

load_dotenv()

try:
    with engine.connect() as conn:
        # Check what users exist in auth.users
        result = conn.execute(text('SELECT id, email FROM auth.users'))
        users = result.fetchall()
        print('Users in auth.users table:')
        for user in users:
            print(f'  ID: {user[0]}, Email: {user[1]}')
            
        # Check the specific UUIDs from the logs
        test_uuids = [
            'd8ebec9d-c349-4b41-a787-2d7b913c8f1f',
            '0f9233b1-7390-515d-9787-175006338642'
        ]
        
        for test_uuid in test_uuids:
            result = conn.execute(text('SELECT id, email FROM auth.users WHERE id = :user_id'), {'user_id': test_uuid})
            user = result.fetchone()
            if user:
                print(f'\n✓ UUID {test_uuid} found: {user[1]}')
            else:
                print(f'\n❌ UUID {test_uuid} NOT found in auth.users')
                
except Exception as e:
    print(f'Error: {e}')
