import os
import oracledb

ORACLE_USER = os.getenv("ORACLE_USER", "ecommerce_user")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "ecommerce_password")
ORACLE_DSN = os.getenv("ORACLE_DSN", "localhost/XEPDB1")

def run_sql_script(cursor, filepath):
    print(f"Executing script: {filepath}...")
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found.")
        return False
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Strip SQL comments starting with --
    lines = content.splitlines()
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('--'):
            continue
        clean_lines.append(line)
    content = "\n".join(clean_lines)

    # Oracle PL/SQL blocks and trigger/procedure definitions end with a "/"
    chunks = content.split('/')
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        
        # Check if the chunk is a PL/SQL block or trigger/procedure definition
        chunk_upper = chunk.upper()
        is_plsql = ("BEGIN" in chunk_upper or 
                    "DECLARE" in chunk_upper or 
                    "CREATE OR REPLACE TRIGGER" in chunk_upper or 
                    "CREATE OR REPLACE PROCEDURE" in chunk_upper)
        
        if is_plsql:
            try:
                cursor.execute(chunk)
            except Exception as e:
                print(f"Error executing PL/SQL block in {filepath}:\n{e}")
                print(f"Block preview:\n{chunk[:300]}...\n")
                return False
        else:
            # Normal SQL statements inside the chunk are separated by ";"
            statements = chunk.split(';')
            for stmt in statements:
                stmt = stmt.strip()
                if not stmt:
                    continue
                try:
                    cursor.execute(stmt)
                except Exception as e:
                    print(f"Error executing statement in {filepath}:\n{e}")
                    print(f"Statement: {stmt}\n")
                    return False
    print(f"Successfully executed: {filepath}\n")
    return True

def main():
    print("Connecting to Oracle Database...")
    print(f"DSN: {ORACLE_DSN}")
    print(f"User: {ORACLE_USER}")
    
    try:
        connection = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)
        cursor = connection.cursor()
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("\nTroubleshooting Tips:")
        print("1. Verify Oracle Database is running (e.g. check OracleServiceXE service in Windows).")
        print("2. Ensure username 'ecommerce_user' exists and credentials are correct.")
        print("3. Check listener status (port 1521).")
        return

    # Files must be compiled in this exact dependency order
    sql_files = [
        "sql/sequences.sql",
        "sql/tables.sql",
        "sql/trigger.sql",
        "sql/procedure.sql",
        "sql/sample_data.sql"
    ]
    
    success = True
    for sql_file in sql_files:
        if not run_sql_script(cursor, sql_file):
            success = False
            break
            
    if success:
        try:
            connection.commit()
            print("Database configuration completed successfully! All tables, sequences, triggers, and sample data have been compiled.")
        except Exception as e:
            print(f"Error during commit: {e}")
    else:
        print("Database configuration failed. Rolling back changes.")
        connection.rollback()
        
    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()
