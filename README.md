# PyCOM
***A python GUI tool for serial communication***   

## Dependencies:
python v3.11.4  
pyside6  pyserial  chardet   

## Dependencies install cmd:
```C
// install package with specified tsinghua source path
pip install pyside6==6.5.2 -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install pyserial==3.5 -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install chardet==5.2.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
// or install all
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## pack with nuitka
```C
// install nuitka  
pip install nuitka==1.7.10 -i https://pypi.tuna.tsinghua.edu.cn/simple
// generate exe
nuitka --mingw64 --standalone --follow-imports --windows-disable-console --show-progress --show-memory --enable-plugin=pyside6 --windows-icon-from-ico=.\resrc\images\pycom.ico --include-data-dir=./demo=./demo --include-data-files=./ReleaseNote.txt=ReleaseNote.txt pycom.py
```

## pack with pyinstaller
```C
// install pyinstaller  
pip install pyinstaller==5.13.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
// generate exe
pyinstaller --onefile --noconsole --clean -i ./resrc/images/pycom.ico pycom.py
```
