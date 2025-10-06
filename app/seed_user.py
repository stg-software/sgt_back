from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.roles import Role
from app.core.security import hash_password

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

def seed_admin_user():
    db = SessionLocal()  # ← aquí abrimos la sesión
    try:
        # Verificar si ya existe admin
        admin_exists = db.query(User).filter_by(username="admin").first()
        if admin_exists:
            print("⚠️ El usuario admin ya existe.")
            return

        # Buscar rol Administrador
        admin_role = db.query(Role).filter_by(name="Administrador").first()
        if not admin_role:
            print("❌ No existe el rol 'Administrador'. Primero corre seed.py")
            return

        # Crear admin
        admin = User(
            username="jhony",
            first_name="Jhony",
            last_name="Perez",
            email="jhony@gmail.com",
            password=hash_password("jhony123"),
            role_id=4,
        )
        db.add(admin)
        db.commit()
        print("✅ Usuario admin creado con éxito (username=admin, password=admin123)")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin_user()
