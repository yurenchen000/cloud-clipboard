// a gorilla/websocket wrapper for safe concurrent write
package SafeWebsocket

import (
	"errors"
	"log"
	"time"

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
	flushCh     chan struct{} // flush 信号: 非 nil 时表示 flush 请求
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
		//是 flush 信号, 不是普通 ws 消息
        if req.flushCh != nil {
            close(req.flushCh)
            continue
        }
		
		//普通 ws 消息
		err := ws.Conn.WriteMessage(req.messageType, req.data)
		if err != nil {
			log.Println("write error:", err)
			ws.Close()
			// return
		}
	}

	log.Println("== write closeMessage!")
	ws.Conn.WriteMessage(websocket.CloseMessage, []byte{})
}

var errChanClosed = errors.New("sws: already closed")

func (ws *Conn) WriteMessage(messageType int, data []byte) error {
	select {
	case <-ws.closeChan: //closed: do nothing
		return errChanClosed
	case ws.writeChan <- writeRequest{messageType: messageType, data: data}: //closed: panic
		return nil
	}
}

// 等待 writePump 处理完所有已入队消息后再返回 nil；
// 若连接已关闭返回 errChanClosed；超时返回错误。
func (ws *Conn) Flush(timeout_ms int) error {
	if ws.writeChan == nil {
		return nil
	}

	// 1. 追加 flushCh 信号 进发送 fifo
    flushCh := make(chan struct{})
    select {
    case <-ws.closeChan:
        return errChanClosed
    case ws.writeChan <- writeRequest{flushCh: flushCh}:
    }

	// 2. 等待 flushCh 信号回应
    select {
    case <-flushCh:
        return nil
    case <-ws.closeChan:
        return errChanClosed
    case <-time.After(time.Duration(timeout_ms) * time.Millisecond):
        return errors.New("safe_ws: flush timeout")
    }
}

func (ws *Conn) Close() error {
	select {
	case <-ws.closeChan: //closed: do nothing
		return errChanClosed
	default:
		close(ws.closeChan)                        //通知 .WriteMessage 不要再接新任务
		writeChan := ws.writeChan
		ws.writeChan = nil //avoid write to closed //先赋值 nil, 再关闭: 避免竞态 write closed chan
		close(writeChan)   //avoid for range leak  //通知 .writePump 没有任务了
		return ws.Conn.Close()
		// return nil
	}
}

// chan 回收机制: 不是关闭后被回收, 而是不再被引用 被回收
// 可以显式 ch = nil, 也可以等待 保存 ch 的结构被释放
