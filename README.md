cloud clip
==========

## what's this?

a PWA web page for share text/file between devices.

before this tool, i used
- IM tools like wechat, [telegram](https://web.telegram.org/k/)  
//i don't want to login account ()

- transfer tools like [localsend](https://github.com/localsend/localsend), [snapdrop](https://snapdrop.net/)  
//efficient with large files, but have to run on both device sametime and in same net (not convenience)

and finaly i keep use this tool.
- don't have to install app  
 //just access via web (support PWA if use https)
- don't have to run in same net  
- don't have to run at same time on both side  
 //just upload onetime, and access anytime (it's convenience for text and small files)  
 //may not efficient for large files


this proj fork from https://github.com/TransparentLC/cloud-clipboard  
and may not be able to merge to upstream.

<br>

## what in this repo:

- a modified version front ui in client/
- a golang implement server in golang branch
- a python implement server in py3 branch


a online demo
https://demo1.ez2.fun/

<br>

## how to use

//for golang version, see server-go/README.md  
./cloud-clip

access in browser  
http://your_host:8000

