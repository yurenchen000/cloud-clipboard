py3 server usage
================

NOTE: 
 - a just work version
 - only tested with python 3.10

TODO: 
 - code refactor

## Usage
//1. install depends:
```sh
pip3 install -r requirements.txt
```

//build frontend
[README.md](../README.md#从源代码运行)

```sh
cd ../client
npm install
npm run build
```
 got frontend files at ../server-node/static/

<br>

//2. run server:  
// at 0.0.0.0:9501 (default config.json)
```sh
## link bulit frontend files
ln -s ../server-node/static
mkdir ./uploads
python3 main.py
```

