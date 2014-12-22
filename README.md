Auto Emailer
==========

Installation
----------
* Create local config in `./local.py`.
    * The three attributes required in this file are specified in `./local.py.example`.
* Set crontab entries.
    * Crontab examples for setting up recurring automatic sends are located in `./crontab.example`.
    * Currently I use python from a virtualenv, thus the `.virtualenv` path invocation of the python binary.
* Install python requirements (recommended in virtualenv).
    * `pip install -r requirements.txt`

Style
----------
* I follow [Google's python style guide](http://google-styleguide.googlecode.com/svn/trunk/pyguide.html).

