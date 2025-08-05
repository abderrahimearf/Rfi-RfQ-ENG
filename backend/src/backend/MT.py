import os
from sentence_transformers import SentenceTransformer
import numpy as np


MODEL_NAME = 'intfloat/multilingual-e5-small'
MODEL_DIR = './models/intfloat_multilingual-e5-small'


if not os.path.exists(MODEL_DIR):
    print(f"⬇ Téléchargement du modèle : {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    model.save(MODEL_DIR)
    print(f" Modèle sauvegardé dans : {MODEL_DIR}")
else:
    print(f" Chargement du modèle local depuis : {MODEL_DIR}")
    model = SentenceTransformer(MODEL_DIR)

phrase = "EXTRAIT DE"
vecteur = model.encode(phrase)


print("\n Test terminé avec succès !")
print(" Dimension du vecteur :", vecteur.shape)
print(" Début du vecteur :", np.round(vecteur[:5], 4), "...")
