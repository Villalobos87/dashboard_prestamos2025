#!/bin/bash
# Elimina posibles cachés antiguos de pip
pip cache purge

# Fuerza reinstalación de todas las dependencias
pip install --upgrade --force-reinstall -r requirements.txt