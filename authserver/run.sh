#!/bin/bash

export GOOGLE_APPLICATION_CREDENTIALS=~/containers/fredbrowserextension/authserver/key.json
pushd ~/containers/fredbrowserextension/authserver/app
python3 app.py
popd
