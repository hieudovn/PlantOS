from app.db import Base, get_engine
Base.metadata.create_all(get_engine())
print("Tables created OK")
