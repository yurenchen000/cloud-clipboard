package main

/**
*** FILE: ws.go
***   handle ws send
**/

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strings"
	"sync"

	"github.com/gorilla/websocket"
	"github.com/ua-parser/uap-go/uaparser"
)

// --------------- ws utils

// send message to ws_list
func broadcast_ws_msg(ws_list map[*websocket.Conn]bool, message string, room string) {
	var wg sync.WaitGroup
	fmt.Println("--broadcast msg:", ws_list, room, message)
	for ws := range ws_list {
		if room_ws[ws] == room {
			wg.Add(1)
			go func(ws *websocket.Conn) {
				defer wg.Done()
				err := ws.WriteMessage(websocket.TextMessage, []byte(message))
				if err != nil {
					log.Println("write error:", err)
					ws.Close()
					delete(ws_list, ws)
				}
			}(ws)
		}
	}
	wg.Wait()
}

// send messageQueue to a ws
func ws_send_history(ws *websocket.Conn, room string) {
	fmt.Println("== send hist:", ws.RemoteAddr(), room)
	for _, message := range messageQueue.List { //msg: {event,data}
		fmt.Println("--hist msg:", message)
		// if message["data"].(map[string]interface{})["room"] == room {
		if message.Data.Room() == room {
			messageJSON, err := json.Marshal(message)
			if err != nil {
				fmt.Println("无法编码消息")
				return
			}
			messageStr := string(messageJSON)
			ws.WriteMessage(websocket.TextMessage, []byte(messageStr))
		}
	}
}

func ws_send_history_multi(ws *websocket.Conn, room string) {
	fmt.Println("== send hist multi:", ws.RemoteAddr(), room)
	var posts = PostEventMulti{Event: "receiveMulti"}
	// posts.Data list
	for _, message := range messageQueue.List {
		fmt.Println("--hist msg:", message)
		// if message["data"].(map[string]interface{})["room"] == room {
		if message.Data.Room() == room { //msg: {event,data}
			posts.Data = append(posts.Data, *&message.Data)
		}
	}

	messageJSON, err := json.Marshal(posts)
	if err != nil {
		fmt.Println("无法编码消息")
		return
	}
	messageStr := string(messageJSON)
	ws.WriteMessage(websocket.TextMessage, []byte(messageStr))
}

// Filter returns a new slice containing only elements that match the predicate
func Filter[T any](slice []T, predicate func(T) bool) []T {
	result := make([]T, 0, len(slice))
	for _, item := range slice {
		if predicate(item) {
			result = append(result, item)
		}
	}
	return result
}

// Map transforms each element of the slice using the mapper function
func Map[T any, R any](slice []T, mapper func(T) R) []R {
	result := make([]R, 0, len(slice))
	for _, item := range slice {
		result = append(result, mapper(item))
	}
	return result
}

func send_posts(ws *websocket.Conn, event_name string, list_post []PostEvent) {
	var posts = PostEventMulti{
		Event: event_name,
		Data:  Map(list_post, func(msg PostEvent) ReceiveHolder { return msg.Data }),
	}

	messageJSON, err := json.Marshal(posts)
	if err != nil {
		fmt.Println("无法编码消息")
		return
	}
	ws.WriteMessage(websocket.TextMessage, messageJSON)
}

func ws_send_history_multi2(ws *websocket.Conn, room string) {
	// 0. filter list
	var filteredList []PostEvent
	filteredList = Filter(messageQueue.List, func(msg PostEvent) bool { return msg.Data.Room() == room })

	fmt.Println("== send hist multi2:", ws.RemoteAddr(), room)

	splitIndex := len(filteredList) - 15
	if splitIndex < 0 {
		splitIndex = 0
	}
	list_hist := filteredList[:splitIndex] // All elements except last 15, maybe []
	list_news := filteredList[splitIndex:] // Last 15 elements

	// 1. latest first
	send_posts(ws, "receiveMulti", list_news)
	// time.Sleep(time.Second * 2)

	// 2. history later
	if splitIndex > 0 {
		send_posts(ws, "receiveMultiOld", list_hist)
	}
}

// send deviceConnected[] to websockets[]
func ws_send_devices(r *http.Request, ws *websocket.Conn) (string, string) {
	room := r.URL.Query().Get("room")
	user_agent := r.Header.Get("User-Agent")
	ip, port := get_remote(r)
	deviceID := fmt.Sprintf("%d", hash_murmur3(fmt.Sprintf("%s:%s %s", ip, port, user_agent), deviceHashSeed))
	parser := uaparser.NewFromSaved()
	client := parser.Parse(user_agent)
	fmt.Println("==send devices:", room, user_agent, ip, deviceID)

	// fmt.Println("uaparse:")
	// litter.Dump(client)

	deviceMeta := map[string]string{
		"id":      deviceID,
		"type":    client.Device.Family,
		"device":  strings.TrimSpace(fmt.Sprintf("%s %s %s", client.Device.Brand, client.Device.Model, client.Os.Family)),
		"os":      fmt.Sprintf("%s %s", client.Os.Family, client.Os.Major),
		"browser": fmt.Sprintf("%s %s", client.UserAgent.Family, client.UserAgent.Major),
	}

	//send old to self
	for _, meta := range deviceConnected {
		ws.WriteMessage(websocket.TextMessage, []byte(fmt.Sprintf(`{"event":"connect","data":%s}`, meta)))
	}

	//send new to all
	deviceMetaJSON, err := json.Marshal(deviceMeta)
	if err != nil {
		log.Println("Failed to marshal deviceMeta:", err)
		return "", ""
	}

	deviceConnected[deviceID] = string(deviceMetaJSON)
	broadcast_ws_msg(websockets, fmt.Sprintf(`{"event":"connect","data":%s}`, deviceMetaJSON), room)
	return deviceID, room
}
