# MNIST Notebook

This pipeline will run test data through a saved tensorflow model trained on the [MNIST digits dataset](https://www.tensorflow.org/datasets/catalog/mnist). This is simlar to the [MNIST Network](../mnist-network) example, but uses a jupyter notebook directly.

## Try it!

### Install the requirements

If you haven't already, install the [requirements](../../requirements/mnist-notebook.txt) into your python environment.

### Training the model

You will need a trained and saved tensorflow model that can take the MNIST digits as input.  An example model can be found [here](../mnist-network/mnist.ipynb).  You may need to install the Jupyter notebook cli in order to train this model, or you can port it to a Python script and just run that, something similar to [this](../mnist-network/mnist.py). In both of these options, you will need to alter the save path of the model to suit your needs, or take note of the default.

If you do not want to train the model, we use a [saved one for testing purposes](../../tests/pipelines/files/mnist), and you can copy it to the desired destination on your system.

### Creating the notebook

Now, you will need a Jupyter noteobook that is able to take in the test data and run predictions on it one-by-one. There is a [simple one that is used for testing purposes](../../tests/pipelines/files/mnist_saf.ipynb) that should suit most systems well enough.

### Configuration

Once your saved model and notebook are in place, you just need to add this config to either your `analytics-engine.conf` file or into a new file, perhaps `salt-analytics-mnist-notebook.conf`. Anything within angled brackets (`<>`) will need to be tuned to your system's setup and own preferences.

```
analytics:
  collectors:
    mnist-digits-collector:
      interval: 0.1
      plugin: mnist_digits
      path: <path-to-save-mnist-digits-to>

  processors:
    numpy-save-keys-processor:
      plugin: numpy_save_keys
      base_path: <directory-to-save-inputs-to>

    jupyter-notebook-processor:
      plugin: jupyter_notebook
      notebook: <path-to-notebook>
      output_notebook: <path-to-output-notebook>
      params:
        model_path: <path-to-saved-model>
      input_keys:
        - x_path
        - y_path
      output_tag: output

    notebook-output-processor:
      plugin: notebook_output

  forwarders:
    mnist-notebook-disk-forwarder:
      plugin: disk
      path: <path-to-dump-directory>
      filename: <dump-filename>
      pretty_print: True

  pipelines:
    mnist-notebook:
      collect: mnist-digits-collector
      process:
        - numpy-save-keys-processor
        - jupyter-notebook-processor
        - notebook-output-processor
      forward: mnist-notebook-disk-forwarder
```

### Output

Once your master or minion are started, you should see data dumped to `<path-to-dump-directory>/<dump-filename>` that shows whether the model accurately predicted the correct digit, and a running average of accuracy and loss for your model.
