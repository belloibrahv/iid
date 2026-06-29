"""
Database Module.
Handles SQLite and PostgreSQL database initialization and CRUD operations for events, alerts, and users.
Implements database schema as specified in Section 12.
"""
import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

from config import DATABASE_PATH, DATABASE_URL

# PostgreSQL support
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class Database:
    """
    Manages SQLite and PostgreSQL database operations for the IDS application.
    Automatically detects and uses PostgreSQL if DATABASE_URL is set.
    """
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.use_postgres = DATABASE_URL is not None and POSTGRES_AVAILABLE
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Ensures connections are properly closed.
        Supports both SQLite and PostgreSQL.
        """
        if self.use_postgres:
            conn = psycopg2.connect(DATABASE_URL)
            conn.autocommit = True
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                yield conn
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
    
    def _execute_query(self, cursor, query: str, params: tuple = ()):
        """
        Execute query with proper parameter substitution for SQLite or PostgreSQL.
        Automatically converts ? to %s for PostgreSQL.
        """
        if self.use_postgres:
            # Convert SQLite ? placeholders to PostgreSQL %s
            pg_query = query.replace('?', '%s')
            cursor.execute(pg_query, params)
        else:
            cursor.execute(query, params)
    
    def init_db(self):
        """
        Initialize database tables if they don't exist.
        Creates users, events, and alerts tables.
        Supports both SQLite and PostgreSQL syntax.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            if self.use_postgres:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                ''')
            
            # Create events table
            if self.use_postgres:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        predicted_class TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        source_ip TEXT,
                        duration REAL,
                        protocol_type TEXT,
                        service TEXT,
                        flag TEXT,
                        src_bytes REAL,
                        dst_bytes REAL,
                        logged_in INTEGER,
                        count REAL,
                        srv_count REAL,
                        same_srv_rate REAL,
                        diff_srv_rate REAL,
                        dst_host_count REAL,
                        dst_host_srv_count REAL,
                        dst_host_same_srv_rate REAL,
                        dst_host_diff_srv_rate REAL,
                        num_compromised REAL,
                        root_shell INTEGER,
                        su_attempted INTEGER,
                        num_root REAL,
                        num_failed_logins REAL,
                        raw_features_json TEXT
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                        predicted_class TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        source_ip TEXT,
                        duration REAL,
                        protocol_type TEXT,
                        service TEXT,
                        flag TEXT,
                        src_bytes REAL,
                        dst_bytes REAL,
                        logged_in INTEGER,
                        count REAL,
                        srv_count REAL,
                        same_srv_rate REAL,
                        diff_srv_rate REAL,
                        dst_host_count REAL,
                        dst_host_srv_count REAL,
                        dst_host_same_srv_rate REAL,
                        dst_host_diff_srv_rate REAL,
                        num_compromised REAL,
                        root_shell INTEGER,
                        su_attempted INTEGER,
                        num_root REAL,
                        num_failed_logins REAL,
                        raw_features_json TEXT
                    )
                ''')
            
            # Create alerts table
            if self.use_postgres:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id SERIAL PRIMARY KEY,
                        event_id INTEGER REFERENCES events(id),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        attack_type TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        source_ip TEXT,
                        status TEXT NOT NULL DEFAULT 'unresolved'
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id INTEGER NOT NULL REFERENCES events(id),
                        timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                        attack_type TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        source_ip TEXT,
                        status TEXT NOT NULL DEFAULT 'unresolved'
                    )
                ''')
            
            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON events(timestamp DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_predicted_class 
                ON events(predicted_class)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alerts_status 
                ON alerts(status)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alerts_attack_type 
                ON alerts(attack_type)
            ''')
            
            print("Database initialized successfully.")
    
    # User operations
    def create_user(self, username: str, password_hash: str) -> int:
        """
        Create a new user.
        
        Args:
            username: Username
            password_hash: Bcrypt hash of the password
            
        Returns:
            User ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.use_postgres:
                cursor.execute(
                    'INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id',
                    (username, password_hash)
                )
                return cursor.fetchone()['id']
            else:
                self._execute_query(
                    cursor,
                    'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                    (username, password_hash)
                )
                return cursor.lastrowid
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username.
        
        Args:
            username: Username to look up
            
        Returns:
            User dictionary or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute_query(
                cursor,
                'SELECT * FROM users WHERE username = ?',
                (username,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    # Event operations
    def create_event(self, event_data: Dict[str, Any]) -> int:
        """
        Create a new event record.
        
        Args:
            event_data: Dictionary containing event fields
            
        Returns:
            Event ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Serialize all features to JSON
            raw_features_json = json.dumps(event_data)
            
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO events (
                        timestamp, predicted_class, confidence, source_ip,
                        duration, protocol_type, service, flag,
                        src_bytes, dst_bytes, logged_in, count, srv_count,
                        same_srv_rate, diff_srv_rate, dst_host_count,
                        dst_host_srv_count, dst_host_same_srv_rate,
                        dst_host_diff_srv_rate, num_compromised, root_shell,
                        su_attempted, num_root, num_failed_logins, raw_features_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                ''', (
                    event_data.get('timestamp', datetime.utcnow().isoformat()),
                    event_data['predicted_class'],
                    event_data['confidence'],
                    event_data.get('source_ip'),
                    event_data.get('duration'),
                    event_data.get('protocol_type'),
                    event_data.get('service'),
                    event_data.get('flag'),
                    event_data.get('src_bytes'),
                    event_data.get('dst_bytes'),
                    event_data.get('logged_in'),
                    event_data.get('count'),
                    event_data.get('srv_count'),
                    event_data.get('same_srv_rate'),
                    event_data.get('diff_srv_rate'),
                    event_data.get('dst_host_count'),
                    event_data.get('dst_host_srv_count'),
                    event_data.get('dst_host_same_srv_rate'),
                    event_data.get('dst_host_diff_srv_rate'),
                    event_data.get('num_compromised'),
                    event_data.get('root_shell'),
                    event_data.get('su_attempted'),
                    event_data.get('num_root'),
                    event_data.get('num_failed_logins'),
                    raw_features_json
                ))
                return cursor.fetchone()['id']
            else:
                self._execute_query(cursor, '''
                    INSERT INTO events (
                        timestamp, predicted_class, confidence, source_ip,
                        duration, protocol_type, service, flag,
                        src_bytes, dst_bytes, logged_in, count, srv_count,
                        same_srv_rate, diff_srv_rate, dst_host_count,
                        dst_host_srv_count, dst_host_same_srv_rate,
                        dst_host_diff_srv_rate, num_compromised, root_shell,
                        su_attempted, num_root, num_failed_logins, raw_features_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_data.get('timestamp', datetime.utcnow().isoformat()),
                    event_data['predicted_class'],
                    event_data['confidence'],
                    event_data.get('source_ip'),
                    event_data.get('duration'),
                    event_data.get('protocol_type'),
                    event_data.get('service'),
                    event_data.get('flag'),
                    event_data.get('src_bytes'),
                    event_data.get('dst_bytes'),
                    event_data.get('logged_in'),
                    event_data.get('count'),
                    event_data.get('srv_count'),
                    event_data.get('same_srv_rate'),
                    event_data.get('diff_srv_rate'),
                    event_data.get('dst_host_count'),
                    event_data.get('dst_host_srv_count'),
                    event_data.get('dst_host_same_srv_rate'),
                    event_data.get('dst_host_diff_srv_rate'),
                    event_data.get('num_compromised'),
                    event_data.get('root_shell'),
                    event_data.get('su_attempted'),
                    event_data.get('num_root'),
                    event_data.get('num_failed_logins'),
                    raw_features_json
                ))
                return cursor.lastrowid
    
    def get_events(
        self,
        class_filter: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        source_ip: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get events with optional filters.
        
        Args:
            class_filter: Filter by predicted class
            from_date: Start date filter (ISO format)
            to_date: End date filter (ISO format)
            source_ip: Filter by source IP
            limit: Number of records to return
            offset: Offset for pagination
            
        Returns:
            List of event dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM events WHERE 1=1'
            params = []
            
            if class_filter:
                query += ' AND predicted_class = ?'
                params.append(class_filter)
            
            if from_date:
                query += ' AND timestamp >= ?'
                params.append(from_date)
            
            if to_date:
                query += ' AND timestamp <= ?'
                params.append(to_date)
            
            if source_ip:
                query += ' AND source_ip LIKE ?'
                params.append(f'%{source_ip}%')
            
            query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            self._execute_query(cursor, query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_event_count(
        self,
        class_filter: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        source_ip: Optional[str] = None
    ) -> int:
        """
        Get count of events matching filters.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT COUNT(*) FROM events WHERE 1=1'
            params = []
            
            if class_filter:
                query += ' AND predicted_class = ?'
                params.append(class_filter)
            
            if from_date:
                query += ' AND timestamp >= ?'
                params.append(from_date)
            
            if to_date:
                query += ' AND timestamp <= ?'
                params.append(to_date)
            
            if source_ip:
                query += ' AND source_ip LIKE ?'
                params.append(f'%{source_ip}%')
            
            self._execute_query(cursor, query, tuple(params))
            return cursor.fetchone()[0]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get dashboard statistics.
        
        Returns:
            Dictionary with total_processed, breakdown by class, active_alerts
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total processed
            self._execute_query(cursor, 'SELECT COUNT(*) FROM events')
            total_processed = cursor.fetchone()[0]
            
            # Breakdown by class
            self._execute_query(cursor, '''
                SELECT predicted_class, COUNT(*) 
                FROM events 
                GROUP BY predicted_class
            ''')
            class_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Active alerts
            self._execute_query(cursor, 'SELECT COUNT(*) FROM alerts WHERE status = ?', ('unresolved',))
            active_alerts = cursor.fetchone()[0]
            
            return {
                'total_processed': total_processed,
                'normal': class_counts.get('normal', 0),
                'dos': class_counts.get('dos', 0),
                'probing': class_counts.get('probing', 0),
                'r2l': class_counts.get('r2l', 0),
                'u2r': class_counts.get('u2r', 0),
                'active_alerts': active_alerts
            }
    
    # Alert operations
    def create_alert(self, event_id: int, attack_type: str, confidence: float, source_ip: Optional[str] = None) -> int:
        """
        Create a new alert.
        
        Args:
            event_id: ID of the associated event
            attack_type: Type of attack (dos, probing, r2l, u2r)
            confidence: Confidence score
            source_ip: Source IP address
            
        Returns:
            Alert ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO alerts (event_id, attack_type, confidence, source_ip)
                    VALUES (%s, %s, %s, %s) RETURNING id
                ''', (event_id, attack_type, confidence, source_ip))
                return cursor.fetchone()['id']
            else:
                self._execute_query(cursor, '''
                    INSERT INTO alerts (event_id, attack_type, confidence, source_ip)
                    VALUES (?, ?, ?, ?)
                ''', (event_id, attack_type, confidence, source_ip))
                return cursor.lastrowid
    
    def get_alerts(
        self,
        attack_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get alerts with optional filters.
        
        Args:
            attack_type: Filter by attack type
            status: Filter by status (unresolved/resolved)
            limit: Number of records to return
            offset: Offset for pagination
            
        Returns:
            List of alert dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM alerts WHERE 1=1'
            params = []
            
            if attack_type:
                query += ' AND attack_type = ?'
                params.append(attack_type)
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            self._execute_query(cursor, query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_alert_count(
        self,
        attack_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """
        Get count of alerts matching filters.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT COUNT(*) FROM alerts WHERE 1=1'
            params = []
            
            if attack_type:
                query += ' AND attack_type = ?'
                params.append(attack_type)
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            self._execute_query(cursor, query, tuple(params))
            return cursor.fetchone()[0]
    
    def resolve_alert(self, alert_id: int) -> bool:
        """
        Mark an alert as resolved.
        
        Args:
            alert_id: ID of the alert to resolve
            
        Returns:
            True if successful, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute_query(
                cursor,
                'UPDATE alerts SET status = ? WHERE id = ?',
                ('resolved', alert_id)
            )
            return cursor.rowcount > 0
    
    def get_alert_with_event(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """
        Get alert details with associated event data.
        
        Args:
            alert_id: ID of the alert
            
        Returns:
            Combined alert and event dictionary
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute_query(cursor, '''
                SELECT alerts.*, events.*
                FROM alerts
                JOIN events ON alerts.event_id = events.id
                WHERE alerts.id = ?
            ''', (alert_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None


# Global database instance
db = Database()


if __name__ == '__main__':
    # Test database operations
    print("Initializing database...")
    db = Database()
    
    print("\nTesting user creation...")
    user_id = db.create_user('admin', 'hashed_password_here')
    print(f"Created user with ID: {user_id}")
    
    print("\nTesting event creation...")
    event_data = {
        'predicted_class': 'dos',
        'confidence': 0.98,
        'source_ip': '192.168.1.100',
        'duration': 0,
        'protocol_type': 'tcp',
        'service': 'http',
        'flag': 'SF',
        'src_bytes': 100,
        'dst_bytes': 200,
        'logged_in': 0,
        'count': 5,
        'srv_count': 5,
        'same_srv_rate': 1.0,
        'diff_srv_rate': 0.0,
        'dst_host_count': 10,
        'dst_host_srv_count': 10,
        'dst_host_same_srv_rate': 1.0,
        'dst_host_diff_srv_rate': 0.0,
        'num_compromised': 0,
        'root_shell': 0,
        'su_attempted': 0,
        'num_root': 0,
        'num_failed_logins': 0
    }
    event_id = db.create_event(event_data)
    print(f"Created event with ID: {event_id}")
    
    print("\nTesting alert creation...")
    alert_id = db.create_alert(event_id, 'dos', 0.98, '192.168.1.100')
    print(f"Created alert with ID: {alert_id}")
    
    print("\nTesting stats retrieval...")
    stats = db.get_stats()
    print(f"Stats: {stats}")
    
    print("\nDatabase test complete!")
