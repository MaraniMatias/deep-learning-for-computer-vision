#!/usr/bin/python3

from six.moves import cPickle
import cv2
import fnmatch
import re
import numpy as np
import os
import pandas as pd
import sys


# Extrar los objetos que importan
# https://programarfacil.com/blog/vision-artificial/detector-de-bordes-canny-opencv/
def cutHandOfImage(image):
    # Convertimos a escala de grises
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Aplicar suavizado Gaussiano
    # img= cv2.GaussianBlur(img, (5, 5), 0)

    # Detectamos los bordes con Canny
    img = cv2.Canny(img, 50, 150)
    kernel = np.ones((20, 20), np.uint8)
    img = cv2.morphologyEx(img, cv2.MORPH_GRADIENT, kernel)

    # Buscamos los contornos
    (_, contours, _) = cv2.findContours(
        img,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    # Mostramos el número de monedas por consola
    # print("He encontrado {} objetos".format(len(contours)))
    objetoMasGrande = 0
    for i, cnt in enumerate(contours):
        if len(contours[objetoMasGrande]) < len(cnt):
            objetoMasGrande = i
        # else:
        #     cv2.drawContours(image, contours, i, (0, 0, 0), -1)

    # image, objecots, num objecto (-1, todos), color de borde, tamaño del borde
    cv2.drawContours(image, contours, objetoMasGrande, (255, 255, 255), -1)

    # Limpiar, Dejar solo el color blanco
    image = cv2.inRange(
        image,
        np.array([255, 255, 255]),  # lower colr
        np.array([255, 255, 255])  # upper color
    )

    cv2.imwrite(
        "./cutHandOfImage.png",
        np.hstack([
            image,
        ])
    )

    return image


# whitepatch, normaliza la los colores de la imagen
#
# Como las imagenes tiene diferentes tonalidades de colores
# Este algoritmo whit-patch pretende llevar los colores de la
# imagenes a un tono igual
def whitePatch(image):
    B, G, R = cv2.split(image)

    red = cv2.equalizeHist(R)
    green = cv2.equalizeHist(G)
    blue = cv2.equalizeHist(B)

    imgOut = cv2.merge((blue, green, red))

    # show the images
    # cv2.imwrite("white-patch.png", np.hstack([image, imgOut, ]))

    return imgOut


# Show a progress bar
def updateProgress(progress, tick='', total='', status='Loading...'):
    barLength = 45
    if isinstance(progress, int):
        progress = float(progress)
    if progress < 0:
        progress = 0
        status = "Waiting...\r\n"
    if progress >= 1:
        progress = 1
        status = "Completed loading data\r\n"
    block = int(round(barLength * progress))
    sys.stdout.write(str("\rImage: {0}/{1} [{2}] {3}% {4}").format(
        tick,
        total,
        str(("#" * block)) + str("." * (barLength - block)),
        round(progress * 100, 1), status))
    sys.stdout.flush()


# For this problem the validation and test data provided by the concerned authority did not have labels, so the training data was split into train, test and validation sets
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
train_dir = os.path.join(__location__, 'dataset_sample')

X_train = []
y_age = []
y_gender = []

df = pd.read_csv(os.path.join(train_dir, 'dataset_sample_labels.csv'))
a = df.values
m = a.shape[0]

print('Loading data set...')
# file names on train_dir
files = os.listdir(train_dir)
# filtter image file
files = [f for f in files if fnmatch.fnmatch(f, '*.png')]
totalFile = len(files)

for i in range(totalFile):
    imgFile = files[i]

    y_age.append(df.boneage[df.id == int(imgFile[:-4])].tolist()[0])
    a = df.male[df.id == int(imgFile[:-4])].tolist()[0]
    if a:
        y_gender.append(1)
    else:
        y_gender.append(0)

    img_path = os.path.join(train_dir, imgFile)
    img = cv2.imread(img_path)

    imgBGR2RGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # =========================================================
    imgColorEqualize = whitePatch(imgBGR2RGB)
    # Crear una mascara para tratar de eliminar el fondo
    mask = cv2.GaussianBlur(imgColorEqualize, (23, 23), 0)
    mask = cv2.inRange(
        mask,
        np.array([128, 128, 128]),  # lower colr
        np.array([255, 255, 255])  # upper color
    )

    # Crear un kernel de '1' de 20x20
    kernel = np.ones((20, 20), np.uint8)
    # Se aplica la transformacion: Opening
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    # =========================================================

    output = cv2.bitwise_and(imgBGR2RGB, imgBGR2RGB, mask=mask)
    mask2 = cutHandOfImage(output.copy())

    output2 = cv2.bitwise_and(imgBGR2RGB, imgBGR2RGB, mask=mask2)

    # show the images
    cv2.imwrite(
        "./remainder.png",
        # "./dataset_sample/remainder_"+str(i)+".png",
        np.hstack([
            img,
            imgColorEqualize,
            output,
            output2
        ])
    )

    # TODO: Dejar solo el area de la mano amtes de redimencionar

    # Redimencionar las imagenes
    img = cv2.resize(img, (224, 224))

    x = np.asarray(img, dtype=np.uint8)
    X_train.append(x)

    # Update the progress bar
    updateProgress(float((i+1) / totalFile), (i+1), totalFile, imgFile)


print('\nSaving data...')
# Save data
train_pkl = open('data.pkl', 'wb')
cPickle.dump(X_train, train_pkl, protocol=cPickle.HIGHEST_PROTOCOL)
train_pkl.close()

train_age_pkl = open('data_age.pkl', 'wb')
cPickle.dump(y_age, train_age_pkl, protocol=cPickle.HIGHEST_PROTOCOL)
train_age_pkl.close()

train_gender_pkl = open('data_gender.pkl', 'wb')
cPickle.dump(y_gender, train_gender_pkl, protocol=cPickle.HIGHEST_PROTOCOL)
train_gender_pkl.close()
print('\nCompleted saved data')
