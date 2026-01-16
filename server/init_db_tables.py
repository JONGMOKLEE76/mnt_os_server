from database import engine, Base
import models

def init_new_tables():
    print("Initializing new tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    init_new_tables()
