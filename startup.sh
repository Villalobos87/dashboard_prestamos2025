#!/bin/bash
# Forzar desinstalación de cualquier SQLAlchemy instalada
pip uninstall -y sqlalchemy SQLAlchemy

# Instalar la versión correcta
pip install SQLAlchemy==2.0.23

# Instalar el resto de dependencias
pip install -r requirements.txt 