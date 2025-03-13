# Database Setup and Management

This document provides instructions for setting up and managing the database for the Horizeel App.

## Database Structure

The Horizeel App uses PostgreSQL with the following tables:

- `users` - User accounts and profiles
- `videos` - Video content information
- `saved_videos` - Tracks which videos are saved by which users

## Database Initialization

To initialize the database with all tables:

```bash
# Run from the backend directory
python init_database.py
```

This will create all tables defined in the `app/models.py` file.

## Adding New Tables

If you need to add a new table to an existing database:

1. Define the model in `app/models.py`
2. Create a script similar to `app/add_saved_videos_table.py` 
3. Run the script to create just that table

For example:

```python
# Example script to add a new table
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine

def check_if_table_exists(table_name):
    with engine.connect() as connection:
        query = text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name);"
        )
        result = connection.execute(query, {"table_name": table_name})
        return result.scalar()

def create_new_table():
    if check_if_table_exists("new_table_name"):
        print("Table already exists.")
        return
    
    from app.models import NewTableModel
    NewTableModel.__table__.create(engine, checkfirst=True)
    print("Table created successfully.")

if __name__ == "__main__":
    create_new_table()
```

## Verifying Database Schema

To check which tables exist in the database:

```bash
# Run from the backend directory
python app/check_tables.py
```

## Troubleshooting

### UUID Generation

If you encounter errors with UUID generation like:

```
function uuid_generate_v4() does not exist
```

Make sure your models use Python's `uuid.uuid4` function instead:

```python
import uuid
from sqlalchemy import Column, UUID

class MyModel(Base):
    __tablename__ = "my_table"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

### Table Already Exists

If you try to create a table that already exists, you might get an error. Use the `checkfirst=True` parameter:

```python
MyModel.__table__.create(engine, checkfirst=True)
```

Or check if the table exists before creating it:

```python
if not check_if_table_exists("my_table"):
    MyModel.__table__.create(engine)
``` 