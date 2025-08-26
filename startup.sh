#!/bin/bash

echo "💡 Limpiando dependencias conflictivas..."

pip uninstall -y sqlalchemy SQLAlchemy
pip install SQLAlchemy==2.0.23
pip install --upgrade --force-reinstall -r requirements.txt

echo "✅ Dependencias instaladas correctamente"