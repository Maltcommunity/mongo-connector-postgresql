#!/bin/bash

rm dist/*
python setup.py sdist && twine upload --repository testpypi dist/* && twine upload --repository pypi dist/* 

