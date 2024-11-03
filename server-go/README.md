(go version) server usage
=========================


[![build](https://github.com/yurenchen000/cloud-clipboard/actions/workflows/release.yml/badge.svg)](https://github.com/yurenchen000/cloud-clipboard/releases)

<!-- not work
[![go-report](https://goreportcard.com/badge/github.com/yurenchen000/cloud-clipboard)](https://goreportcard.com/report/github.com/yurenchen000/cloud-clipboard)
-->

[![release](https://img.shields.io/github/v/release/yurenchen000/cloud-clipboard)](https://github.com/yurenchen000/cloud-clipboard/releases)


NOTE: 
 - almost all features
 - only tested with ubuntu 22, go-1.22

## Usage
//1. install:  
download binary from release page  

or install by cmd (need golang 1.22)

```bash
go install -v  github.com/yurenchen000/cloud-clipboard/server-go/cloud-clip@golang
```

//2. run server:  
- need manually create `config.json`  
- need `./static` (link from server-node, no static resource in binary)  
- need `./upload` folder 

```bash
ln -s ../server-node/static
mkdir ./uploads
./cloud-clip
```

