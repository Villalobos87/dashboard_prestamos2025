#!/bin/bash

echo "💡 Limpiando e instalando dependencias..."

# Desinstalar cualquier versión previa de SQLAlchemy
pip uninstall -y sqlalchemy SQLAlchemy

# Instalar SQLAlchemy correcto
pip install SQLAlchemy==2.0.23

# Instalar el resto de dependencias
pip install --upgrade --force-reinstall -r requirements.txt

echo "✅ Dependencias instaladas correctamente" 