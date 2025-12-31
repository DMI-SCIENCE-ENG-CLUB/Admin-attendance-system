from sqlalchemy import create_engine, text
from config import DATABASE_CONFIGS

def migrate():
    url = DATABASE_CONFIGS['sqlite']
    engine = create_engine(url)
    
    with engine.connect() as conn:
        # 1. Create leaves table
        print("Creating 'leaves' table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS leaves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    leave_type VARCHAR(20) DEFAULT 'vacation',
                    status VARCHAR(20) DEFAULT 'pending',
                    reason VARCHAR(255),
                    FOREIGN KEY(employee_id) REFERENCES employees(id)
                )
            """))
            print("Leaves table created (if not existed).")
        except Exception as e:
            print(f"Error creating table: {e}")

        # 2. Add contract_type to employees
        print("Adding 'contract_type' to 'employees'...")
        try:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(employees)"))
            columns = [row[1] for row in result]
            if 'contract_type' not in columns:
                conn.execute(text("ALTER TABLE employees ADD COLUMN contract_type VARCHAR(20) DEFAULT 'permanent'"))
                print("Column 'contract_type' added.")
            else:
                print("Column 'contract_type' already exists.")
        except Exception as e:
            print(f"Error adding column: {e}")

if __name__ == "__main__":
    migrate()
