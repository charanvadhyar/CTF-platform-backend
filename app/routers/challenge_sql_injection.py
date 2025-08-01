"""
Backend endpoints for SQL Injection Challenge (Challenge #2)
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.database import get_database
import re
import sqlite3
import os
from contextlib import closing
import logging

# Create router for this challenge
router = APIRouter(
    prefix="/challenge-2",
    tags=["challenge-2"],
)

# Setup in-memory SQLite database for this challenge
DB_FILE = ":memory:"
logger = logging.getLogger(__name__)

# Models
class Product(BaseModel):
    id: int
    name: str
    category: str
    price: float

class User(BaseModel):
    id: int
    username: str
    password: str
    email: str

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    columns: List[str]
    results: List[Dict]
    query: str

def setup_database():
    """Set up SQLite database with vulnerable search functionality"""
    try:
        # Create in-memory database
        with closing(sqlite3.connect(DB_FILE)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Create products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    price REAL NOT NULL
                )
            """)
            
            # Create users table with sensitive data including the flag
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT NOT NULL
                )
            """)
            
            # Insert sample products
            products = [
                (1, 'Laptop', 'Electronics', 999.99),
                (2, 'Smartphone', 'Electronics', 699.99),
                (3, 'Headphones', 'Accessories', 149.99),
                (4, 'Monitor', 'Electronics', 299.99),
                (5, 'Keyboard', 'Accessories', 89.99)
            ]
            
            cursor.executemany(
                "INSERT OR REPLACE INTO products (id, name, category, price) VALUES (?, ?, ?, ?)",
                products
            )
            
            # Insert users with the flag as admin's password
            users = [
                (1, 'admin', 'CTF{sql_injection_union_attack}', 'admin@example.com'),
                (2, 'user1', 'password123', 'user1@example.com')
            ]
            
            cursor.executemany(
                "INSERT OR REPLACE INTO users (id, username, password, email) VALUES (?, ?, ?, ?)",
                users
            )
            
            conn.commit()
            logger.info("SQLite database for SQL Injection challenge setup complete")
    except Exception as e:
        logger.error(f"Error setting up SQLite database: {str(e)}")
        raise

# Initialize database
setup_database()

@router.post("/search", response_model=SearchResponse)
async def search_products(search_data: SearchRequest):
    """
    Search products endpoint - intentionally vulnerable to SQL injection
    """
    query = search_data.query
    
    # Log the search query (optional)
    db = get_database()
    await db.challenge_attempts.insert_one({
        "challenge_id": 2,
        "attempt_type": "search",
        "query": query
    })
    
    try:
        # Intentionally vulnerable SQL query
        # DO NOT USE THIS IN PRODUCTION CODE - THIS IS A DELIBERATE SECURITY VULNERABILITY
        sql_query = f"""
            SELECT id, name, category, price
            FROM products
            WHERE name LIKE '%{query}%' OR category LIKE '%{query}%'
        """
        
        with closing(sqlite3.connect(DB_FILE)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Execute the query (intentionally vulnerable)
            cursor.execute(sql_query)
            results = [dict(row) for row in cursor.fetchall()]
            
            # Get column names
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            return SearchResponse(
                columns=columns,
                results=results,
                query=sql_query
            )
            
    except sqlite3.Error as e:
        # Return the SQL error to help users debug their injection
        # This is also intentionally vulnerable
        return SearchResponse(
            columns=["error"],
            results=[{"error": str(e)}],
            query=sql_query
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
