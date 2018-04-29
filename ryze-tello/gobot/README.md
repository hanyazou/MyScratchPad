
# GOBOT DJI Tello sample

## source code

tello-gobot.go is from GASU's article on https://www.drone-engineer.com/articles/766

## how to build and execute

````
bash-3.2$ brew install mplayer
🍺  /usr/local/Cellar/mplayer/1.3.0: 11 files, 26.9MB
bash-3.2$ brew install go
🍺  /usr/local/Cellar/go/1.10.1: 8,158 files, 336.7MB
bash-3.2$ go get -d -u gobot.io/x/gobot/...
bash-3.2$ go build
bash-3.2$ ./tello-gobot
````

## how to fly

With Playstaion 4 bluetooth controller,
push Triangle button to take off and push Circle button to land.