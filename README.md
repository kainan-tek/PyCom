# PyCOM
***A python GUI tool for serial communication***   

## Dependencies:
python v3.10.5  
pyside6==6.3.1  
pyserial==3.5  
pyinstaller==5.1 (optional)  
notice: pyinstaller is used for packing the python script file(\*.py) to executable file(\*.exe).  

## Dependencies install cmd:
```C
# install package with specified aliyun source path
pip install pyside6==6.3.1 -i https://mirrors.aliyun.com/pypi/simple
pip install pyserial==3.5 -i https://mirrors.aliyun.com/pypi/simple
pip install pyinstaller==5.1 -i https://mirrors.aliyun.com/pypi/simple (optional)
# or install all 
pip install requirements.txt
```

## pack with pyinstaller
```C
pyinstaller --clean main.spec
# or  
pyinstaller --onefile --noconsole --clean main.py
```
