import sqlite3

conn = sqlite3.connect('database_enhanced.db')
c = conn.cursor()

print("=== ALL DRIVERS ===")
c.execute("SELECT id, name, role, owner_id, verification_status FROM drivers")
for row in c.fetchall():
    print(f"  ID={row[0]} name={row[1]} role={row[2]} owner_id={row[3]} status={row[4]}")

print("\n=== ALL DOCUMENTS ===")
c.execute("SELECT id, driver_id, uploaded_by, doc_type, length(file_data), ai_status FROM driver_documents")
for row in c.fetchall():
    print(f"  doc_id={row[0]} driver_id={row[1]} uploaded_by={row[2]} type={row[3]} data_len={row[4]} status={row[5]}")

print("\n=== DOCUMENT DATA PREFIX (first 60 chars) ===")
c.execute("SELECT driver_id, doc_type, substr(file_data, 1, 60) FROM driver_documents")
for row in c.fetchall():
    print(f"  driver_id={row[0]} type={row[1]} prefix={repr(row[2])}")

conn.close()
