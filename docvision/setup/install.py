import os
from sys import platform
import click
def after_install():
    try:
        if platform == "linux" or platform == "linux2":
            os.system("sudo apt-get install tesseract-ocr")
            os.system("sudo apt-get install libtesseract-dev")
        elif platform == "darwin":
            os.system("brew install tesseract")
        else:
            click.secho("Unsupported platform",fg="red")
            click.secho("Please install tesseract-ocr manually",fg="red")
    except Exception as e:
        click.secho("sudo apt-get install tesseract-ocr failed with error: {}".format(e), fg="red")
        click.secho("Please install tesseract-ocr manually")
        
        