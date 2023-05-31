# MNIST Network

This pipeline will run test data through a saved tensorflow model trained on the [MNIST digits dataset](https://www.tensorflow.org/datasets/catalog/mnist).

## Try it!

### Install the requirements

If you haven't already, install the [requirements](../../requirements/mnist.txt) into your python environment.

### Training the model

You will need a trained and saved tensorflow model that can take the MNIST digits as input.  An example model can be found [here](mnist.ipynb).  You may need to install the Jupyter notebook cli in order to train this model, or you can port it to a Python script and just run that, something similar to [this](mnist.py). In both of these options, you will need to alter the save path of the model to suit your needs, or take note of the default.

If you do not want to train the model, we use a [saved one for testing purposes](../../tests/pipelines/files/mnist), and you can copy it to the desired destination on your system.

### Configuration

Once your saved model is in place, you just need to add this config to either your `analytics-engine.conf` file or into a new file, perhaps `salt-analytics-mnist-network.conf`.  Anything within angled brackets (`<>`) will need to be tuned to your system's setup and own preferences.

```
analytics:
  collectors:
    mnist-digits-collector:
      interval: 0.1
      plugin: mnist_digits
      path: <path-to-save-mnist-digits-to>

  processors:
    mnist-network-processor:
      plugin: mnist_network
      model: <path-to-saved-model>

  forwarders:
    mnist-disk-forwarder:
      plugin: disk
      path: <path-to-dump-directory>
      filename: <dump-filename>
      pretty_print: True

  pipelines:
    mnist-network:
      collect: mnist-digits-collector
      process: mnist-network-processor
      forward: mnist-disk-forwarder
```

### Output

Once your master or minion are started, you should see data dumped to `<path-to-dump-directory>/<dump-filename>` that shows whether the model accurately predicted the correct digit, and a running average of accuracy and loss for your model.
