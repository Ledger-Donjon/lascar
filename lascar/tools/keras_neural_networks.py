# This file is part of lascar
#
# lascar is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#
# Copyright 2018 Manuel San Pedro, Victor Servant, Charles Guillemet, Ledger SAS - manuel.sanpedro@ledger.fr, victor.servant@ledger.fr, charles@ledger.fr

"""
THis code is taken from ASCAD:

https://github.com/ANSSI-FR/ASCAD/blob/master/ASCAD_train_models.py

"""

from tensorflow.keras.layers import Flatten, Dense, Input, Conv1D, AveragePooling1D, Dropout
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.optimizers import RMSprop


#### MLP Best model (6 layers of 200 units)
def mlp_best(
    input_shape, number_of_classes=256, nodes=None, layer_nb=5, dropout=0.2, lr=0.01
):

    if nodes == None:
        nodes = [200] * (layer_nb)
    else:
        layer_nb = len(nodes)

    model = Sequential()
    model.add(Dense(nodes[0], input_shape=input_shape, activation="relu"))
    if dropout:
        model.add(Dropout(dropout))

    for i in range(1, layer_nb):
        model.add(Dense(nodes[i], activation="relu"))
        if dropout:
            model.add(Dropout(dropout))

    model.add(Dense(number_of_classes, activation="softmax"))
    optimizer = RMSprop(lr=lr)
    model.compile(
        loss="categorical_crossentropy", optimizer=optimizer, metrics=["accuracy"]
    )
    return model


### CNN Best model
def cnn_best(input_shape=(700, 1), number_of_classes=256, lr=0.01):
    # From VGG16 design
    img_input = Input(shape=input_shape)
    # Block 1
    x = Conv1D(64, 11, activation="relu", padding="same", name="block1_conv1")(
        img_input
    )
    x = AveragePooling1D(2, strides=2, name="block1_pool")(x)
    # Block 2
    x = Conv1D(128, 11, activation="relu", padding="same", name="block2_conv1")(x)
    x = AveragePooling1D(2, strides=2, name="block2_pool")(x)
    # Block 3
    x = Conv1D(256, 11, activation="relu", padding="same", name="block3_conv1")(x)
    x = AveragePooling1D(2, strides=2, name="block3_pool")(x)
    # Block 4
    x = Conv1D(512, 11, activation="relu", padding="same", name="block4_conv1")(x)
    x = AveragePooling1D(2, strides=2, name="block4_pool")(x)
    # Block 5
    x = Conv1D(512, 11, activation="relu", padding="same", name="block5_conv1")(x)
    x = AveragePooling1D(2, strides=2, name="block5_pool")(x)
    # Classification block
    x = Flatten(name="flatten")(x)
    x = Dense(4096, activation="relu", name="fc1")(x)
    x = Dense(4096, activation="relu", name="fc2")(x)
    x = Dense(number_of_classes, activation="softmax", name="predictions")(x)

    inputs = img_input
    # Create model.
    model = Model(inputs, x, name="cnn_best")
    optimizer = RMSprop(lr=lr)
    model.compile(
        loss="categorical_crossentropy", optimizer=optimizer, metrics=["accuracy"]
    )
    return model
