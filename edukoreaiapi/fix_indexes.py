#!/usr/bin/env python3
"""Fix MongoDB indexes with partial unique indexes."""

from pymongo import MongoClient
from config.config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Drop all existing indexes except _id
try:
    db.users.drop_index('username_1')
    print('✓ Dropped old username index')
except:
    pass

try:
    db.users.drop_index('email_1')
    print('✓ Dropped old email index')
except:
    pass

try:
    db.users.drop_index('mobile_1')
    print('✓ Dropped old mobile index')
except:
    pass

# Create PARTIAL unique indexes (only enforce when field exists)
# This allows multiple documents to NOT have the email field
db.users.create_index(
    'email',
    unique=True,
    partialFilterExpression={'email': {'$exists': True}}
)
print('✓ Created email partial unique index (only for docs with email field)')

db.users.create_index(
    'mobile',
    unique=True,
    partialFilterExpression={'mobile': {'$exists': True}}
)
print('✓ Created mobile partial unique index (only for docs with mobile field)')

# List all indexes
print('\nCurrent indexes:')
for idx in db.users.list_indexes():
    print(f"  - {idx['name']}: {idx['key']}")
    if 'partialFilterExpression' in idx:
        print(f"    Filter: {idx['partialFilterExpression']}")

print('\n✅ Indexes properly configured!')
print('\nNow you can:')
print('  - Signup with email (no mobile)')
print('  - Signup with mobile (no email)')
print('  - Multiple users can be missing either field')
