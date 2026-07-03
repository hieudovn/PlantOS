from passlib.context import CryptContext
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
print("engineer:", pwd.hash("PlantOS@2026!"))
print("operator:", pwd.hash("PlantOS@2026!"))
