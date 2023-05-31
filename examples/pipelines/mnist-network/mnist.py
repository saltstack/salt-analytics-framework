# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from tensorflow import keras

# Load the mnist data
(x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()

# Normalize the data
x_train = x_train / 255
x_test = x_test / 255

# Flattening the data
x_train_flattened = x_train.reshape(len(x_train), 28 * 28)
x_test_flattened = x_test.reshape(len(x_test), 28 * 28)

# Create a simple model using only sigmoid activation functions
model = keras.Sequential(
    [
        keras.layers.Dense(100, input_shape=(784,), activation="relu"),
        keras.layers.Dense(10, activation="sigmoid"),
    ]
)

# Set the parameters on the model
model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])

# Train
model.fit(x_train_flattened, y_train, epochs=5)


# Save the model so we can reload it later
model_name = "mnist"
model.save(model_name)


# Run the model against the test data
model.evaluate(x_test_flattened, y_test)
