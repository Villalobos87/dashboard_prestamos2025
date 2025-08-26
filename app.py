import streamlit as st
from sqlalchemy import create_engine
import pandas as pd

st.title("Prueba SQLAlchemy en Streamlit")

# Ejemplo de conexión (reemplaza con tus datos)
# engine = create_engine("postgresql://usuario:contraseña@localhost:5432/tu_base")

st.write("✅ SQLAlchemy importado y funcionando")