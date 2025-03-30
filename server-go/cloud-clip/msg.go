package main

/**
*** FILE: msg.go
***   handle messageQueue
**/

import "sync"

type PostEvent struct {
	Event string        `json:"event"`
	Data  ReceiveHolder `json:"data"`
}
type PostEventMulti struct {
	Event string          `json:"event"`
	Data  []ReceiveHolder `json:"data"`
}

type PostList struct {
	sync.Mutex
	nextid      int
	history_len int

	List []PostEvent `json:"receive"`
}

func (m *PostList) Append(item *PostEvent) {
	m.Lock()
	defer m.Unlock()

	if item.Data.ID() <= 0 { //fill uniq id, thread-safe way
		item.Data.SetID(m.nextid)
	}
	m.List = append(m.List, *item)

	for len(m.List) > m.history_len { //history reach max
		m.List = m.List[1:]
	}

	m.nextid++

	itemID := item.Data.ID()
	if m.nextid <= itemID {
		m.nextid = itemID + 1
	}
}

// remove array item by index
func (m *PostList) Remove(index int) {
	// m.Lock()
	// defer m.Unlock()
	if index < 0 || index >= len(m.List) {
		return
	}
	m.List = append(m.List[:index], m.List[index+1:]...)
}

// find item index which m.Data[index].Data.ID() == msgId
func (m *PostList) FindId(msgId int) int {
	// m.Lock()
	// defer m.Unlock()
	for i, msg := range m.List {
		if msg.Data.ID() == msgId {
			return i
		}
	}
	return -1 // Return -1 if the message ID is not found
}

// find item by id and remove it from array
func (m *PostList) RemoveById(msgId int) int {
	m.Lock()
	defer m.Unlock()

	index := m.FindId(msgId)
	if index != -1 {
		m.Remove(index)
	}

	return index
}
