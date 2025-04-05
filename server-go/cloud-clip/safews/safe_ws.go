// a gorilla/websocket wrapper for safe concurrent write
package SafeWebsocket

import (
	"errors"
	"log"

	"net/http"

	"github.com/gorilla/websocket"
)

// --------------- ws var
var TextMessage = websocket.TextMessage

// --------------- ws upgrader
type OrigUpgrader = websocket.Upgrader

// Upgrader 继承 websocket.Upgrader
type Upgrader struct {
	*websocket.Upgrader // 嵌入原始 Upgrader
}

// Upgrade 重写方法，返回安全的 SafeWebSocket 连接
func (u *Upgrader) Upgrade(w http.ResponseWriter, r *http.Request, responseHeader http.Header) (*Conn, error) {
	// 调用原始 Upgrade 获取标准 websocket 连接
	rawConn, err := u.Upgrader.Upgrade(w, r, responseHeader)
	if err != nil {
		return nil, err
	}

	// 封装为线程安全的 SafeWebSocket
	return NewConn(rawConn), nil
}

// --------------- ws conn

type Conn struct {
	// conn      *websocket.Conn
	*websocket.Conn
	writeChan chan writeRequest //
	closeChan chan struct{}     //only close: boradcast writeChan closed
}

type writeRequest struct {
	messageType int
	data        []byte
}

func NewConn(conn *websocket.Conn) *Conn {
	ws := &Conn{
		Conn:      conn,
		writeChan: make(chan writeRequest, 100),
		closeChan: make(chan struct{}),
	}
	go ws.writePump()
	return ws
}

func (ws *Conn) writePump() {
	for req := range ws.writeChan {
		err := ws.Conn.WriteMessage(req.messageType, req.data)
		if err != nil {
			log.Println("write error:", err)
			ws.Close()
			// delete(ws_list, ws)
		}
	}
}

var errChanClosed = errors.New("sws: already closed")

func (ws *Conn) WriteMessage(messageType int, data []byte) error {
	select {
	case <-ws.closeChan: //closed: do nothing
		return errChanClosed
	case ws.writeChan <- writeRequest{messageType, data}: //closed: panic
		return nil
	}
}
func (ws *Conn) Close() error {
	select {
	case <-ws.closeChan: //closed: do nothing
		return errChanClosed
	default:
		close(ws.closeChan)
		writeChan := ws.writeChan
		ws.writeChan = nil //avoid write to closed
		close(writeChan)   //avoid for range leak
		return ws.Conn.Close()
		// return nil
	}
}

// chan 回收机制: 不是关闭后被回收, 而是不再被引用 被回收
// 可以显式 ch = nil, 也可以等待 保存 ch 的结构被释放
