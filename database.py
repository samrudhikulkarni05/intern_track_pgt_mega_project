import sqlite3
import json
from datetime import date, datetime, timedelta
import uuid
from typing import List, Dict, Optional

class DatabaseService:
    def __init__(self):
        self.conn = self.init_db()
    
    def init_db(self):
        """Initialize SQLite database with all required tables"""
        conn = sqlite3.connect('interntrack.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                domain TEXT NOT NULL,
                description TEXT,
                required_skills TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT,
                assigned_job_id TEXT,
                skills TEXT,
                onboarded BOOLEAN DEFAULT 0,
                analysis TEXT,
                performance_metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assigned_job_id) REFERENCES jobs (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id TEXT PRIMARY KEY,
                intern_id TEXT NOT NULL,
                date TEXT NOT NULL,
                time_in TEXT NOT NULL,
                time_out TEXT,
                task TEXT,
                resources TEXT,
                duration INTEGER,
                score INTEGER,
                status TEXT,
                quiz_results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (intern_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id TEXT PRIMARY KEY,
                intern_id TEXT NOT NULL,
                date TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (intern_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute("SELECT COUNT(*) FROM jobs")
        if cursor.fetchone()[0] == 0:
            sample_jobs = [
                ('job-1', 'Frontend Developer', 'Web Development', 
                 'Advanced UI engineering with React, TypeScript, and high-performance rendering patterns.',
                 json.dumps([{"name": "React", "minLevel": 4}, {"name": "TypeScript", "minLevel": 3}, 
                            {"name": "JavaScript", "minLevel": 4}, {"name": "CSS", "minLevel": 3},
                            {"name": "HTML", "minLevel": 3}])),
                ('job-2', 'AI Research Associate', 'Machine Learning',
                 'Development of neural architectures, Python-based pipelines, and statistical modeling.',
                 json.dumps([{"name": "Python", "minLevel": 5}, {"name": "Machine Learning", "minLevel": 4},
                            {"name": "Statistics", "minLevel": 4}, {"name": "TensorFlow", "minLevel": 3},
                            {"name": "Data Analysis", "minLevel": 4}])),
                ('job-3', 'DevOps Engineer', 'Cloud & Infrastructure',
                 'Cloud infrastructure management, CI/CD pipelines, and container orchestration.',
                 json.dumps([{"name": "AWS", "minLevel": 4}, {"name": "Docker", "minLevel": 4},
                            {"name": "Kubernetes", "minLevel": 3}, {"name": "Linux", "minLevel": 4},
                            {"name": "Networking", "minLevel": 3}]))
            ]
            cursor.executemany('''
                INSERT INTO jobs (id, title, domain, description, required_skills)
                VALUES (?, ?, ?, ?, ?)
            ''', sample_jobs)
        
        conn.commit()
        return conn
    
    def register_intern(self, name: str, email: str, password: str, job_id: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
        if cursor.fetchone()[0] > 0:
            return False
        
        user_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO users (id, name, email, password, assigned_job_id, onboarded, performance_metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, email, password, job_id, 0, json.dumps({})))
        
        self.conn.commit()
        return True
    
    def login_intern(self, email: str, password: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'performance_metrics' in columns:
            query = '''
                SELECT id, name, email, assigned_job_id, skills, onboarded, analysis, performance_metrics
                FROM users WHERE email = ? AND password = ?
            '''
        else:
            query = '''
                SELECT id, name, email, assigned_job_id, skills, onboarded, analysis, NULL
                FROM users WHERE email = ? AND password = ?
            '''
        
        cursor.execute(query, (email, password))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "assigned_job_id": row[3],
                "skills": json.loads(row[4]) if row[4] else [],
                "onboarded": bool(row[5]),
                "analysis": json.loads(row[6]) if row[6] else None,
                "performance_metrics": json.loads(row[7]) if row[7] else None
            }
        return None
    
    def update_intern(self, user: Dict) -> None:
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'performance_metrics' in columns:
            cursor.execute('''
                UPDATE users 
                SET skills = ?, onboarded = ?, analysis = ?, performance_metrics = ?
                WHERE id = ?
            ''', (
                json.dumps(user['skills']),
                int(user['onboarded']),
                json.dumps(user['analysis']),
                json.dumps(user.get('performance_metrics', {})),
                user['id']
            ))
        else:
            cursor.execute('''
                UPDATE users 
                SET skills = ?, onboarded = ?, analysis = ?
                WHERE id = ?
            ''', (
                json.dumps(user['skills']),
                int(user['onboarded']),
                json.dumps(user['analysis']),
                user['id']
            ))
        
        self.conn.commit()
    
    def update_performance_metrics(self, intern_id: str, metrics: Dict) -> None:
        cursor = self.conn.cursor()
        for metric_type, value in metrics.items():
            metric_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO performance_metrics (id, intern_id, date, metric_type, value)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                metric_id,
                intern_id,
                date.today().isoformat(),
                metric_type,
                value
            ))
        
        self.conn.commit()
    
    def get_jobs(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, domain, description, required_skills FROM jobs ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        jobs = []
        for row in rows:
            jobs.append({
                "id": row[0],
                "title": row[1],
                "domain": row[2],
                "description": row[3],
                "required_skills": json.loads(row[4])
            })
        return jobs
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, title, domain, description, required_skills 
            FROM jobs WHERE id = ?
        ''', (job_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "title": row[1],
                "domain": row[2],
                "description": row[3],
                "required_skills": json.loads(row[4])
            }
        return None
    
    def upsert_job(self, job: Dict) -> None:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE id = ?", (job['id'],))
        if cursor.fetchone()[0] > 0:
            cursor.execute('''
                UPDATE jobs SET title = ?, domain = ?, description = ?, required_skills = ?
                WHERE id = ?
            ''', (
                job['title'],
                job['domain'],
                job['description'],
                json.dumps(job['required_skills']),
                job['id']
            ))
        else:
            cursor.execute('''
                INSERT INTO jobs (id, title, domain, description, required_skills)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                job['id'],
                job['title'],
                job['domain'],
                job['description'],
                json.dumps(job['required_skills'])
            ))
        
        self.conn.commit()
    
    def delete_job(self, job_id: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        self.conn.commit()
    
    def log_attendance(self, log: Dict) -> str:
        cursor = self.conn.cursor()
        log_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO attendance (id, intern_id, date, time_in, time_out, task, resources, duration, score, status, quiz_results)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_id,
            log['intern_id'],
            log['date'],
            log['time_in'],
            log['time_out'],
            log['task'],
            json.dumps(log['resources']),
            log['duration'],
            log['score'],
            log['status'],
            json.dumps(log.get('quiz_results', {}))
        ))
        
        self.conn.commit()
        return log_id
    
    def get_attendance_for_intern(self, intern_id: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, date, time_in, time_out, task, resources, duration, score, status, quiz_results
            FROM attendance WHERE intern_id = ? ORDER BY date DESC, time_in DESC
        ''', (intern_id,))
        
        rows = cursor.fetchall()
        attendance = []
        for row in rows:
            attendance.append({
                "id": row[0],
                "date": row[1],
                "time_in": row[2],
                "time_out": row[3],
                "task": row[4],
                "resources": json.loads(row[5]),
                "duration": row[6],
                "score": row[7],
                "status": row[8],
                "quiz_results": json.loads(row[9]) if row[9] else {}
            })
        return attendance
    
    def get_all_attendance(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, intern_id, date, time_in, time_out, task, resources, duration, score, status, quiz_results
            FROM attendance ORDER BY date DESC, time_in DESC
        ''')
        
        rows = cursor.fetchall()
        attendance = []
        for row in rows:
            attendance.append({
                "id": row[0],
                "intern_id": row[1],
                "date": row[2],
                "time_in": row[3],
                "time_out": row[4],
                "task": row[5],
                "resources": json.loads(row[6]),
                "duration": row[7],
                "score": row[8],
                "status": row[9],
                "quiz_results": json.loads(row[10]) if row[10] else {}
            })
        return attendance
    
    def get_all_interns(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'performance_metrics' in columns:
            query = '''
                SELECT id, name, email, assigned_job_id, skills, onboarded, analysis, performance_metrics
                FROM users ORDER BY name
            '''
        else:
            query = '''
                SELECT id, name, email, assigned_job_id, skills, onboarded, analysis, NULL
                FROM users ORDER BY name
            '''
        
        cursor.execute(query)
        rows = cursor.fetchall()
        interns = []
        for row in rows:
            interns.append({
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "assigned_job_id": row[3],
                "skills": json.loads(row[4]) if row[4] else [],
                "onboarded": bool(row[5]),
                "analysis": json.loads(row[6]) if row[6] else None,
                "performance_metrics": json.loads(row[7]) if row[7] else None
            })
        return interns
    
    def get_performance_metrics(self, intern_id: str, days: int = 30) -> List[Dict]:
        cursor = self.conn.cursor()
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT date, metric_type, value 
            FROM performance_metrics 
            WHERE intern_id = ? AND date >= ? 
            ORDER BY date
        ''', (intern_id, start_date))
        
        rows = cursor.fetchall()
        metrics = []
        for row in rows:
            metrics.append({
                "date": row[0],
                "metric_type": row[1],
                "value": row[2]
            })
        return metrics
