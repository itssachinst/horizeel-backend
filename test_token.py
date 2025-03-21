import os
os.environ['PYTHONPATH'] = os.path.abspath('.')
from jose import jwt
from app.utils.auth import SECRET_KEY
from app.crud import SECRET_KEY as CRUD_SECRET_KEY

print("Comparing SECRET KEYS:")
print(f"auth.py SECRET_KEY: {SECRET_KEY}")
print(f"crud.py SECRET_KEY: {CRUD_SECRET_KEY}")
print(f"Equal? {SECRET_KEY == CRUD_SECRET_KEY}")

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzNGU0NjQ5NC0wZWJlLTRjYWEtYmFkNi1hNTI1MWU4Mzg1N2UiLCJleHAiOjE3NDI1MDYwODF9.lw4MrEhdHXXXqZHZ5TBmBHllq_lZPCujPXSX6QHOAZg'

print("\nTrying to decode with auth.py SECRET_KEY:")
try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    print(f"Decoded payload: {payload}")
except Exception as e:
    print(f"Error: {str(e)}")

print("\nTrying to decode with crud.py SECRET_KEY:")
try:
    payload = jwt.decode(token, CRUD_SECRET_KEY, algorithms=['HS256'])
    print(f"Decoded payload: {payload}")
except Exception as e:
    print(f"Error: {str(e)}")

# Create a new token to test
print("\nCreating a new token with auth.py SECRET_KEY:")
from datetime import datetime, timedelta
new_payload = {
    "sub": "34e46494-0ebe-4caa-bad6-a5251e83857e",
    "exp": datetime.utcnow() + timedelta(minutes=30)
}
new_token = jwt.encode(new_payload, SECRET_KEY, algorithm="HS256")
print(f"New token: {new_token}")

# Verify the new token
print("\nVerifying the new token with auth.py SECRET_KEY:")
try:
    decoded = jwt.decode(new_token, SECRET_KEY, algorithms=['HS256'])
    print(f"Decoded: {decoded}")
except Exception as e:
    print(f"Error: {str(e)}")

print("\nVerifying the new token with crud.py SECRET_KEY:")
try:
    decoded = jwt.decode(new_token, CRUD_SECRET_KEY, algorithms=['HS256'])
    print(f"Decoded: {decoded}")
except Exception as e:
    print(f"Error: {str(e)}") 