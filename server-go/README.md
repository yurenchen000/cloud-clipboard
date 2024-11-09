(go version) server usage
=========================


[![build](https://github.com/yurenchen000/cloud-clipboard/actions/workflows/release.yml/badge.svg)](https://github.com/yurenchen000/cloud-clipboard/releases)

<!-- not work
[![go-report](https://goreportcard.com/badge/github.com/yurenchen000/cloud-clipboard)](https://goreportcard.com/report/github.com/yurenchen000/cloud-clipboard)
-->

[![release](https://img.shields.io/github/v/release/yurenchen000/cloud-clipboard)](https://github.com/yurenchen000/cloud-clipboard/releases)


NOTE: 
 - almost all features
 - only tested with ubuntu 22, go-1.22, go-1.18

## 1. Install
//1. install:  

download binary from release page  

or install by cmd (need golang ≥ 1.18)
//without embed static res
```bash
go install -v  github.com/yurenchen000/cloud-clipboard/server-go/cloud-clip@golang
# got ~/go/bin/cloud-clip
```

or build manually (need golang ≥ 1.18)
//should build client/ first
```bash
git clone git@github.com:yurenchen000/cloud-clipboard.git --branch golang
cd cloud-clipboard/server-go/cloud-clip/
go build
# got cloud-clip
```

## 2. Usage

//2. run server:  
- ~~need manually create `config.json`~~  
- ~~need `./static`~~ (~~link from server-node, no~~ static resource in binary)  
- ~~need `./uploads` folder~~ 

<del>`
ln -s ../server-node/static  
mkdir ./uploads  
`</del>

```
./cloud-clip
```

