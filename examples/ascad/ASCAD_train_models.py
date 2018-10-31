import os.path
import sys

import h5py
import numpy as np
from keras.callbacks import ModelCheckpoint
from keras.layers import Flatten, Dense, Input, Conv1D, AveragePooling1D
from keras.models import Model, Sequential
from keras.models import load_model
# from keras.applications.imagenet_utils import _obtain_input_shape
from keras.optimizers import RMSprop
from keras.utils import to_categorical


def check_file_exists(file_path):
    if os.path.exists(file_path) == False:
        print("Error: provided file path '%s' does not exist!" % file_path)
        sys.exit(-1)
    return

#### MLP Best model (6 layers of 200 units)
def mlp_best(node=200,layer_nb=6):
    model = Sequential()
    model.add(Dense(node, input_dim=700, activation='relu'))
    for i in range(layer_nb-2):
        model.add(Dense(node, activation='relu'))
    model.add(Dense(256, activation='softmax'))
    optimizer = RMSprop(lr=0.00001)
    model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'])
    return model

### CNN Best model
def cnn_best(classes=256):
    # From VGG16 design
    input_shape = (700,1)
    img_input = Input(shape=input_shape)
    # Block 1
    x = Conv1D(64, 11, activation='relu', padding='same', name='block1_conv1')(img_input)
    x = AveragePooling1D(2, strides=2, name='block1_pool')(x)
    # Block 2
    x = Conv1D(128, 11, activation='relu', padding='same', name='block2_conv1')(x)
    x = AveragePooling1D(2, strides=2, name='block2_pool')(x)
    # Block 3
    x = Conv1D(256, 11, activation='relu', padding='same', name='block3_conv1')(x)
    x = AveragePooling1D(2, strides=2, name='block3_pool')(x)
    # Block 4
    x = Conv1D(512, 11, activation='relu', padding='same', name='block4_conv1')(x)
    x = AveragePooling1D(2, strides=2, name='block4_pool')(x)
    # Block 5
    x = Conv1D(512, 11, activation='relu', padding='same', name='block5_conv1')(x)
    x = AveragePooling1D(2, strides=2, name='block5_pool')(x)
    # Classification block
    x = Flatten(name='flatten')(x)
    x = Dense(4096, activation='relu', name='fc1')(x)
    x = Dense(4096, activation='relu', name='fc2')(x)
    x = Dense(classes, activation='softmax', name='predictions')(x)

    inputs = img_input
    # Create model.
    model = Model(inputs, x, name='cnn_best')
    optimizer = RMSprop(lr=0.00001)
    model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'])
    return model

def load_sca_model(model_file):
    check_file_exists(model_file)
    try:
            model = load_model(model_file)
    except:
        print("Error: can't load Keras model file '%s'" % model_file)
        sys.exit(-1)
    return model

#### ASCAD helper to load profiling and attack data (traces and labels)
# Loads the profiling and attack datasets from the ASCAD
# database
def load_ascad(ascad_database_file, load_metadata=False):
    check_file_exists(ascad_database_file)
    # Open the ASCAD database HDF5 for reading
    try:
        in_file  = h5py.File(ascad_database_file, "r")
    except:
        print("Error: can't open HDF5 file '%s' for reading (it might be malformed) ..." % ascad_database_file)
        sys.exit(-1)
    # Load profiling traces
    X_profiling = np.array(in_file['Profiling_traces/traces'], dtype=np.int8)
    # Load profiling labels
    Y_profiling = np.array(in_file['Profiling_traces/labels'])
    # Load attacking traces
    X_attack = np.array(in_file['Attack_traces/traces'], dtype=np.int8)
    # Load attacking labels
    Y_attack = np.array(in_file['Attack_traces/labels'])
    if load_metadata == False:
        return (X_profiling, Y_profiling), (X_attack, Y_attack)
    else:
        return (X_profiling, Y_profiling), (X_attack, Y_attack), (in_file['Profiling_traces/metadata'], in_file['Attack_traces/metadata'])

#### Training high level function
def train_model(X_profiling, Y_profiling, model, save_file_name, epochs=150, batch_size=100):
    check_file_exists(os.path.dirname(save_file_name))
    # Save model every epoch
    save_model = ModelCheckpoint(save_file_name)
    callbacks=[save_model]
    # Get the input layer shape
    input_layer_shape = model.get_layer(index=0).input_shape
    # Sanity check
    if input_layer_shape[1] != len(X_profiling[0]):
        print("Error: model input shape %d instead of %d is not expected ..." % (input_layer_shape[1], len(X_profiling[0])))
        sys.exit(-1)
    # Adapt the data shape according our model input
    if len(input_layer_shape) == 2:
        # This is a MLP
        Reshaped_X_profiling = X_profiling
    elif len(input_layer_shape) == 3:
        # This is a CNN: expand the dimensions
        Reshaped_X_profiling = X_profiling.reshape((X_profiling.shape[0], X_profiling.shape[1], 1))
    else:
        print("Error: model input shape length %d is not expected ..." % len(input_layer_shape))
        sys.exit(-1)
    
    history = model.fit(x=Reshaped_X_profiling, y=to_categorical(Y_profiling, num_classes=256), batch_size=batch_size, verbose = 1, epochs=epochs, callbacks=callbacks)
    return history


if __name__ == "__main__":

    # Our folders
    ascad_data_folder = "ASCAD_data/"
    ascad_databases_folder = ascad_data_folder + "ASCAD_databases/"
    ascad_trained_models_folder = ascad_data_folder + "ASCAD_trained_models/"

    # Load the profiling traces in the ASCAD database with no desync
    (X_profiling, Y_profiling), (X_attack, Y_attack) = load_ascad(ascad_databases_folder + "ASCAD.h5")
    (X_profiling_desync50, Y_profiling_desync50), (X_attack_desync50, Y_attack_desync50) = load_ascad(ascad_databases_folder + "ASCAD_desync50.h5")
    (X_profiling_desync100, Y_profiling_desync100), (X_attack_desync100, Y_attack_desync100) = load_ascad(ascad_databases_folder + "ASCAD_desync100.h5")

    ### CNN training
    #### No desync
    cnn_best_model = cnn_best()
    train_model(X_profiling, Y_profiling, cnn_best_model, ascad_trained_models_folder + "my_cnn_best_desync0_epochs75_batchsize200.h5", epochs=75, batch_size=200)

    #### Desync = 50
    cnn_best_model = cnn_best()
    train_model(X_profiling_desync50, Y_profiling_desync50, cnn_best_model, ascad_trained_models_folder + "my_cnn_best_desync50_epochs75_batchsize200.h5", epochs=75, batch_size=200)
    #### Desync = 100
    cnn_best_model = cnn_best()
    train_model(X_profiling_desync100, Y_profiling_desync100, cnn_best_model, ascad_trained_models_folder + "my_cnn_best_desync100_epochs75_batchsize200.h5", epochs=75, batch_size=200)

    ### MLP training
    #### No desync
    mlp_best_model = mlp_best()
    train_model(X_profiling, Y_profiling, mlp_best_model, ascad_trained_models_folder + "my_mlp_best_desync0_epochs200_batchsize100.h5", epochs=200, batch_size=100)
    #### Desync = 50
    mlp_best_model = mlp_best()
    train_model(X_profiling_desync50, Y_profiling_desync50, mlp_best_model, ascad_trained_models_folder + "my_mlp_best_desync50_epochs200_batchsize100.h5", epochs=200, batch_size=100)
    #### Desync = 100
    mlp_best_model = mlp_best()
    train_model(X_profiling_desync100, Y_profiling_desync100, mlp_best_model, ascad_trained_models_folder + "my_mlp_best_desync100_epochs200_batchsize100.h5", epochs=200, batch_size=100)

