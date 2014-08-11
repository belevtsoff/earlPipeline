earlPipeline
============

A simplistic web-based GUI for visualizing and constructing modular data-processing pipelines. It provides a simple python interface for backend implementation. **earlPipeline** can become quite handy when one needs a GUI for some already existing data-processing library.

The package consists of three parts:

* frontend: web-based GUI, implemented in JavaScript, powered by Ember framework
* web server: Python web server, built with Tornado
* example backend: example backend implementation (simple calculator)

Installation
------------

Python part of the package depends upon:

* Python 2.x
* Tornado
* logutils
* bidict >= 0.1.2

All the JS libraries are included in the distribution.

To install the library, simply run smth like::

    $ sudo python2 setup.py install

Give it a shot
--------------

To try it out, create a file ``server.py`` somewhere, with the following contents:

```Python
from earlpipeline import server
from earlpipeline.backends import calculator

if __name__ == '__main__':
    server.set_backend(calculator)
    server.run(pipeline_folder=".")
```

Then, run the script::

    $ python2 server.py

If everything went well, you should now be able to navigate to [http://localhost:5000](http://localhost:5000), click
"New Pipeline", and play around with GUI. You might also have a look at ```earlpipeline/backends/calculator.py``` to see how backends are implemented.

This is how your pipeline might look like:

![ScreenShot](https://github.com/belevtsoff/earlPipeline/raw/master/earlpipeline/docs/screenshot.png)
