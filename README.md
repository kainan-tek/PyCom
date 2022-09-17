# PyCOM
***A python GUI tool for serial communication***   

## Dependencies:
python v3.10.7  
pyside6==6.3.2  
pyserial==3.5  
chardet==5.0.0  
pyinstaller==5.4.1 (optional)  
notice: pyinstaller is used for packing the python script file(\*.py) to executable file(\*.exe).  

## Dependencies install cmd:
```C
// install package with specified aliyun source path
pip install pyside6==6.3.2 -i https://mirrors.aliyun.com/pypi/simple
pip install pyserial==3.5 -i https://mirrors.aliyun.com/pypi/simple
pip install chardet==5.0.0 -i https://mirrors.aliyun.com/pypi/simple
pip install pyinstaller==5.4.1 -i https://mirrors.aliyun.com/pypi/simple (optional)
// or install all
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
```

## pack with pyinstaller
```C
pyinstaller --onefile --noconsole --clean -i ./resrc/images/pycom.ico main.py
// or
pyinstaller --clean main.spec
```
